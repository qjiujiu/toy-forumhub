from fastapi import FastAPI
from app.routers import users, follows

app = FastAPI(title="Forum Management System")

# 注册路由
app.include_router(users.users_router)
app.include_router(follows.follows_router)


# uvicorn main:app
# uvicorn main:app --reload
@app.get("/")
def root():
    return {"message": "Welcome to Forum Management System"}