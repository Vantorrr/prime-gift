from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, SessionLocal
from . import models
from .routers import users, cases, inventory

# Создаем таблицы в БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Prime Gift API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
        "https://motivated-comfort-production.up.railway.app",
        "http://localhost:3000",
        "http://localhost:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(cases.router)
app.include_router(inventory.router)

@app.on_event("startup")
def init_data():
    db = SessionLocal()
    codes = ["WELCOME", "FREEGIFT", "PRIME2024"]
    try:
        for code in codes:
            if not db.query(models.Promocode).filter(models.Promocode.code == code).first():
                db.add(models.Promocode(code=code))
        db.commit()
    except Exception as e:
        print(f"Init error: {e}")
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Prime Gift API is running", "status": "ok"}
