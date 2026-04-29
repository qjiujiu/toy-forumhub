from fastapi import FastAPI
from app.api.v1 import follows, posts, comments, likes
from app.api.v2 import users


app = FastAPI(title="Forum Management System")

# uvicorn main:app
# uvicorn main:app --reload


@app.get("/")
def root():
    return {"message": "Welcome to Forum Management System"}


# 注册路由
app.include_router(users.users_router)
app.include_router(follows.follows_router)
app.include_router(posts.posts_router)
app.include_router(comments.comments_router)
app.include_router(likes.likes_router)
