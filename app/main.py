from fastapi import FastAPI
from app import models
from app.routers import books, users, orders, user_login

app = FastAPI(title="Forum Management System")

# 注册路由
# app.include_router(books.books_router)


@app.get("/")
def root():
    return {"message": "Welcome to Forum Management System"}