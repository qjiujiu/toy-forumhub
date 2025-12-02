from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from app.storage.user.SQLAlchemyUserRepository import SQLAlchemyUserRepository
from app.storage.follow.SQLAlchemyFollowRepository import SQLAlchemyFollowRepository
from app.storage.user_stats.SQLAlchemyUserStatsRepository import SQLAlchemyUserStatsRepository
from app.storage.post.SQLAlchemyPostRepository import SQLAlchemyPostRepository
from app.storage.post_content.SQLAlchemyPostConRepository import SQLAlchemyPostContentRepository
from app.storage.post_stats.SQLAlchemyPostStatsRepository import SQLAlchemyPostStatsRepository
from app.storage.comment.SQLAlchemyCommentRepository import SQLAlchemyCommentRepository
from app.storage.comment_content.SQLAlchemyComConRepository import SQLAlchemyCommentContentRepository

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
def get_usersta_repo(db: Session = Depends(get_db)) -> SQLAlchemyUserStatsRepository:
    return SQLAlchemyUserStatsRepository(db)
def get_post_repo(db: Session = Depends(get_db)) -> SQLAlchemyPostRepository:
    return SQLAlchemyPostRepository(db)
def get_postcon_repo(db: Session = Depends(get_db)) -> SQLAlchemyPostContentRepository:
    return SQLAlchemyPostContentRepository(db)
def get_poststats_repo(db: Session = Depends(get_db)) -> SQLAlchemyPostStatsRepository:
    return SQLAlchemyPostStatsRepository(db)
def get_comment_repo(db: Session = Depends(get_db)) -> SQLAlchemyCommentRepository:
    return SQLAlchemyCommentRepository(db)
def get_comcon_repo(db: Session = Depends(get_db)) -> SQLAlchemyCommentContentRepository:
    return SQLAlchemyCommentContentRepository(db)