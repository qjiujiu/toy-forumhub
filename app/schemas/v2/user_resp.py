"""兼容导出（历史路径：app.schemas.v2.user_resp）

UserOut/BatchUsersOut 在本项目语义上属于 DTO，已迁移至 `app/schemas/v2/user_dto.py`。
保留本模块用于兼容旧 import。
"""

from app.schemas.v2.user_dto import BatchUsersOut, UserOut

__all__ = ["UserOut", "BatchUsersOut"]
