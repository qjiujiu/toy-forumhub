import random
from typing import Dict, List, Optional

from app.agent.models.mbti import MBTIType, MBTIDistribution, DEFAULT_DISTRIBUTION


class MBTISampler:
    """
    MBTI 人口比例采样器。

    按真实世界 MBTI 分布比例对 Agent 进行确定性采样。
    使用最大余数法 (Largest Remainder Method) 处理小数分配，
    确保采样总数精确匹配且比例尽可能接近目标分布。

    Usage:
        sampler = MBTISampler(seed=42)
        types = sampler.sample(100)  # 返回 100 个 MBTIType
        # 结果大致为: ISTJ×14, ISFJ×14, ESFJ×12, ESTJ×9, ISFP×9, ...
    """

    def __init__(
        self,
        distribution: Optional[MBTIDistribution] = None,
        seed: Optional[int] = None,
    ):
        """
        Args:
            distribution: MBTI 分布数据，默认使用真实人口分布
            seed: 随机种子，传入则采样结果可复现
        """
        self.distribution = distribution or DEFAULT_DISTRIBUTION
        self._rng = random.Random(seed) if seed is not None else random.Random()

    def sample(self, count: int) -> List[MBTIType]:
        """
        按比例采样指定数量的 MBTI 类型。

        算法：
        1. 计算每种类型的理论配额：count * (比例/总比例)
        2. 取整数部分，剩余名额按小数部分从大到小分配
        3. 确保最终总数 == count
        """
        if count <= 0:
            return []

        weights = self.distribution.data
        total_weight = sum(weights.values())

        # 1) 计算理论配额
        quotas: Dict[MBTIType, float] = {
            t: count * (w / total_weight) for t, w in weights.items()
        }

        # 2) 取整 + 记录余数
        result: List[MBTIType] = []
        remainder: List[tuple[float, MBTIType]] = []
        allocated = 0

        for mbti_type, quota in quotas.items():
            seats = int(quota)
            result.extend([mbti_type] * seats)
            allocated += seats
            remainder.append((quota - seats, mbti_type))

        # 3) 剩余名额按余数从大到小分配
        remaining = count - allocated
        if remaining > 0:
            remainder.sort(key=lambda x: x[0], reverse=True)
            for i in range(remaining):
                result.append(remainder[i][1])

        # 4) 打乱顺序，使同类型 Agent 不扎堆
        self._rng.shuffle(result)
        return result

    def sample_from_pool(
        self,
        pool: Dict[MBTIType, List[str]],
        count: int,
    ) -> List[tuple[MBTIType, str]]:
        """
        从已有的 Agent 池中按比例采样。

        Args:
            pool: {MBTIType: [agent_id, ...]} 格式的现有 Agent 池
            count: 需要的样本量

        Returns:
            [(MBTIType, agent_id), ...] 列表
        """
        available = {t: ids[:] for t, ids in pool.items()}
        total_available = sum(len(ids) for ids in available.values())
        actual_count = min(count, total_available)

        type_counts: Dict[MBTIType, int] = {}
        for mbti_type in self.sample(actual_count):
            type_counts[mbti_type] = type_counts.get(mbti_type, 0) + 1

        result: List[tuple[MBTIType, str]] = []
        for mbti_type, need in type_counts.items():
            pool_ids = available.get(mbti_type, [])
            selected = pool_ids[:need]
            for agent_id in selected:
                result.append((mbti_type, agent_id))

        self._rng.shuffle(result)
        return result

    def distribution_summary(self, count: int = 1000) -> Dict[str, float]:
        """
        查看按当前分布采样 count 个后的实际比例。

        Returns:
            {类型名: 实际比例%}，用于验证采样精度
        """
        sampled = self.sample(count)
        actual: Dict[str, float] = {}
        for t in MBTIType:
            pct = sampled.count(t) / count * 100
            actual[t.value] = round(pct, 2)
        return actual

    def set_seed(self, seed: int):
        """重置随机种子"""
        self._rng = random.Random(seed)
