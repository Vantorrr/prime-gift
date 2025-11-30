from app.database import SessionLocal
from app import models

db = SessionLocal()

def add_new_year_case():
    # Проверяем, есть ли уже Новогодний кейс
    existing = db.query(models.Case).filter(models.Case.name == "Новогодний").first()
    
    if not existing:
        print("Adding New Year Case...")
        case = models.Case(
            name="Новогодний",
            image_url="/NewYearCase.png", # Путь на фронте
            price=500, # Цена открытия
            currency=models.CurrencyType.STARS,
            is_limited=True,
            limit_total=1000,
            limit_remaining=1000 # На старте полный
        )
        db.add(case)
        db.commit()
        print("Added!")
    else:
        print("Case exists, updating limits...")
        existing.image_url = "/NewYearCase.png"
        existing.limit_total = 1000
        # existing.limit_remaining = 1000 # Раскомментировать для сброса
        db.commit()

if __name__ == "__main__":
    add_new_year_case()

