from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import logging
import time

import httpx

logger = logging.getLogger(__name__)


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"


@dataclass
class LLMUsage:
    """LLM 调用消耗统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0


@dataclass
class LLMResponse:
    """LLM 调用返回结果"""
    content: str
    usage: LLMUsage = field(default_factory=LLMUsage)
    model: str = ""
    success: bool = True
    error_message: str = ""
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


# DeepSeek 价格（每百万 tokens，单位：元）
_MODEL_PRICING: Dict[str, float] = {
    "deepseek-chat": 2.0,       # 输入 2元/M, 输出 8元/M — 取平均 2
    "deepseek-reasoner": 4.0,   # 输入 4元/M, 输出 16元/M — 取平均 4
}


def _estimate_cost(model: str, total_tokens: int) -> float:
    """估算调用成本（人民币）"""
    price_per_million = _MODEL_PRICING.get(model, 2.0)
    return total_tokens * price_per_million / 1_000_000


class LLMClient:
    """
    LLM API 客户端，兼容 DeepSeek / OpenAI 接口。
    默认使用 DeepSeek API，可通过 base_url 切换到其他兼容服务。
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = DEEPSEEK_BASE_URL,
        model: str = DEEPSEEK_MODEL,
        timeout: int = 120,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        self._http_client = httpx.Client(timeout=timeout, follow_redirects=True)

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_payload(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8,
        max_tokens: int = 2048,
        top_p: float = 1.0,
        frequency_penalty: float = 0.3,
        presence_penalty: float = 0.3,
    ) -> Dict[str, Any]:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stream": False,
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """
        调用 LLM Chat Completions API。

        Args:
            messages: OpenAI 格式的 messages 列表
            temperature: 生成温度 (0.0 ~ 2.0)
            max_tokens: 最大生成 token 数

        Returns:
            LLMResponse 包含生成内容和使用统计
        """
        payload = self._build_payload(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        last_error = ""
        start_time = time.perf_counter()

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._http_client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._build_headers(),
                    json=payload,
                )

                latency = (time.perf_counter() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    choice = data["choices"][0]
                    content = choice["message"]["content"].strip()

                    usage_data = data.get("usage", {})
                    usage = LLMUsage(
                        prompt_tokens=usage_data.get("prompt_tokens", 0),
                        completion_tokens=usage_data.get("completion_tokens", 0),
                        total_tokens=usage_data.get("total_tokens", 0),
                        cost=_estimate_cost(self.model, usage_data.get("total_tokens", 0)),
                    )

                    return LLMResponse(
                        content=content,
                        usage=usage,
                        model=self.model,
                        latency_ms=round(latency, 2),
                    )

                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
                    logger.warning(
                        f"[LLM] Rate limited (attempt {attempt}/{self.max_retries}), "
                        f"retrying in {retry_after}s"
                    )
                    time.sleep(retry_after)
                    last_error = f"429 rate limit: {response.text}"
                    continue

                elif response.status_code in (500, 502, 503):
                    wait = 2 ** attempt
                    logger.warning(
                        f"[LLM] Server error {response.status_code} "
                        f"(attempt {attempt}/{self.max_retries}), retrying in {wait}s"
                    )
                    time.sleep(wait)
                    last_error = f"{response.status_code}: {response.text}"
                    continue

                else:
                    error_detail = response.text[:500]
                    logger.error(
                        f"[LLM] API error: {response.status_code} {error_detail}"
                    )
                    return LLMResponse(
                        content="",
                        success=False,
                        error_message=f"API error {response.status_code}: {error_detail}",
                        latency_ms=round((time.perf_counter() - start_time) * 1000, 2),
                    )

            except httpx.TimeoutException:
                wait = 2 ** attempt
                logger.warning(
                    f"[LLM] Timeout (attempt {attempt}/{self.max_retries}), retrying in {wait}s"
                )
                time.sleep(wait)
                last_error = "timeout"

            except httpx.RequestError as e:
                wait = 2 ** attempt
                logger.warning(
                    f"[LLM] Request error: {e} "
                    f"(attempt {attempt}/{self.max_retries}), retrying in {wait}s"
                )
                time.sleep(wait)
                last_error = str(e)

        return LLMResponse(
            content="",
            success=False,
            error_message=f"Max retries exceeded: {last_error}",
            latency_ms=round((time.perf_counter() - start_time) * 1000, 2),
        )

    def close(self):
        """关闭 HTTP 客户端"""
        self._http_client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
