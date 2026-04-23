from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.user import User, UserRole, UserStatus
from app.schemas.v2.user import (
    UserDto,
    UserCreate,
    UserOut,
    BatchUsersOut,
)
from app.storage.v2.user.user_interface import IUserRepository
from app.core.db import transaction


def _map_user_to_out(user: User) -> UserOut:
    return UserOut(
        uid=user.uid,
        user_info=UserDto(
            username=user.username,
            phone=user.phone,
            email=user.email,
            avatar_url=user.avatar_url,
            bio=user.bio,
        ),
        role=user.role,
        status=user.status,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        deleted_at=user.deleted_at,
    )


class SQLAlchemyUserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    def _base_query(self):
        return self.db.query(User).filter(
            User.deleted_at.is_(None),
            User.status == 0,
        )

    def find_user(self, uid: Optional[str] = None, phone: Optional[str] = None) -> Optional[UserOut]:
        if uid:
            user = self._base_query().filter(User.uid == uid).first()
        elif phone:
            user = self._base_query().filter(User.phone == phone).first()
        else:
            return None
        return _map_user_to_out(user) if user else None

    def list_users(
        self,
        username: Optional[str] = None,
        page: int = 0,
        page_size: int = 10,
    ) -> BatchUsersOut:
        base_q = self._base_query()
        if username:
            base_q = base_q.filter(User.username == username)
        base_q = base_q.order_by(User.created_at.desc())

        total = base_q.count()
        users_orm = base_q.offset(page * page_size).limit(page_size).all()
        users_out = [_map_user_to_out(u) for u in users_orm]

        return BatchUsersOut(
            total=total,
            count=len(users_out),
            users=users_out,
        )

    def create_user(self, user_data: UserCreate) -> UserOut:
        user_info = user_data.user_info
        user = User(
            username=user_info.username,
            phone=user_info.phone,
            email=user_info.email,
            avatar_url=user_info.avatar_url,
            bio=user_info.bio,
            password=user_data.password,
            role=UserRole.NORMAL_USER.value,
            status=UserStatus.NORMAL.value,
        )
        with transaction(self.db):
            self.db.add(user)
        self.db.refresh(user)
        return _map_user_to_out(user)

    def update_user(self, uid: str, **kwargs) -> Optional[UserOut]:
        user = self._base_query().filter(User.uid == uid).first()
        if not user:
            return None

        with transaction(self.db):
            for field, value in kwargs.items():
                if value is not None:
                    if field == "user_info":
                        user.username = value.username
                        user.phone = value.phone
                        user.email = value.email
                        user.avatar_url = value.avatar_url
                        user.bio = value.bio
                    elif field == "status":
                        user.status = value
                    elif field == "role":
                        user.role = value
                    elif field == "deleted_at":
                        user.deleted_at = datetime.now(timezone(timedelta(hours=8))) if value else None
                    elif field == "password":
                        user.password = value
            user.updated_at = datetime.now(timezone(timedelta(hours=8)))

        self.db.refresh(user)
        return _map_user_to_out(user)

    def delete_user(self, uid: str) -> bool:
        user = self.db.query(User).filter(User.uid == uid).first()
        if not user:
            return False
        with transaction(self.db):
            self.db.delete(user)
        return True

    def get_password(self, uid: str) -> Optional[str]:
        user = self._base_query().filter(User.uid == uid).first()
        return user.password if user else None