from app.database import SessionLocal
from app import models

db = SessionLocal()

def update_limit():
    case = db.query(models.Case).filter(models.Case.name == "Новогодний").first()
    if case:
        print(f"Было: {case.limit_remaining}")
        case.limit_remaining = 150  # Ставим мало, чтобы проверить шкалу
        db.commit()
        print(f"Стало: {case.limit_remaining} (из {case.limit_total})")

if __name__ == "__main__":
    update_limit()

