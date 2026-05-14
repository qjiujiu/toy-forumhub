from fastapi import FastAPI
from app.core.log_config import config_logging

config_logging()

from app.api.v2 import users, follows, posts, comments, likes

app = FastAPI(title="Forum Management System")

# uvicorn app.main:app
# uvicorn app.main:app --reload

# 注册路由
app.include_router(users.users_router)
app.include_router(follows.follows_router)
app.include_router(posts.posts_router)
app.include_router(comments.comments_router)
app.include_router(likes.likes_router)

@app.get("/")
def root():
    return {"message": "Welcome to Forum Management System"}