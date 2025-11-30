from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from . import models
from .routers import users, cases, inventory # Добавил inventory

# Создаем таблицы в БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Prime Gift API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(cases.router)
app.include_router(inventory.router) # Подключил роутер

@app.get("/")
async def root():
    return {"message": "Prime Gift API is running", "status": "ok"}
