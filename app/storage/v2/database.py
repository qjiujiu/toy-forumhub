from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from app.storage.v2.user.user_repo_sqlalchemy import SQLAlchemyUserRepository
from app.storage.v2.post.post_repo_sqlalchemy import SQLAlchemyPostRepository
from app.storage.v1.comment.comment_repo_sqlalchemy import SQLAlchemyCommentRepository
from app.storage.v1.comment_content.comment_content_repo_sqlalchemy import SQLAlchemyCommentContentRepository
from app.storage.v1.follow.follow_repo_sqlalchemy import SQLAlchemyFollowRepository
from app.storage.v1.like.like_repo_sqlalchemy import SQLAlchemyLikeRepository

from fastapi import Depends

# ======== 配置区 ========
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "102412"   # 你的 MySQL 密码
DB_NAME = "forum_db"
# ========================

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
# SQLAlchemy 引擎
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 未来可以根据配置切换不同的实现
def get_user_repo(db: Session = Depends(get_db)) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(db)


def get_follow_repo(db: Session = Depends(get_db)) -> SQLAlchemyFollowRepository:
    return SQLAlchemyFollowRepository(db)


def get_post_repo(db: Session = Depends(get_db)) -> SQLAlchemyPostRepository:
    return SQLAlchemyPostRepository(db)


def get_comment_repo(db: Session = Depends(get_db)) -> SQLAlchemyCommentRepository:
    return SQLAlchemyCommentRepository(db)


def get_comcon_repo(db: Session = Depends(get_db)) -> SQLAlchemyCommentContentRepository:
    return SQLAlchemyCommentContentRepository(db)


def get_like_repo(db: Session = Depends(get_db)) -> SQLAlchemyLikeRepository:
    return SQLAlchemyLikeRepository(db)
