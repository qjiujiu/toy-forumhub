from fastapi import FastAPI
from app.routers import users, follows, posts, comments

app = FastAPI(title="Forum Management System")

# 注册路由
app.include_router(users.users_router)
app.include_router(follows.follows_router)
app.include_router(posts.posts_router)
app.include_router(comments.comments_router)

# uvicorn main:app
# uvicorn main:app --reload
@app.get("/")
def root():
    return {"message": "Welcome to Forum Management System"}