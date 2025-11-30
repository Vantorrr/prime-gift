from app.database import SessionLocal, engine
from app import models

# Создаем сессию
db = SessionLocal()

def init_db():
    print("Creating initial data...")
    
    # 1. Создаем кейсы
    cases = [
        {
            "name": "Starter Box",
            "image_url": "https://cdn-icons-png.flaticon.com/512/4213/4213652.png", # Заглушка
            "price": 0,
            "currency": models.CurrencyType.STARS,
            "is_limited": False
        },
        {
            "name": "Golden Dragon",
            "image_url": "https://cdn-icons-png.flaticon.com/512/10697/10697423.png",
            "price": 500,
            "currency": models.CurrencyType.STARS,
            "is_limited": True,
            "limit_total": 5000,
            "limit_remaining": 124
        },
        {
            "name": "Ticket Premium",
            "image_url": "https://cdn-icons-png.flaticon.com/512/10828/10828289.png",
            "price": 5,
            "currency": models.CurrencyType.TICKETS,
            "is_limited": False
        }
    ]

    for case_data in cases:
        # Проверяем, есть ли уже такой кейс
        existing = db.query(models.Case).filter(models.Case.name == case_data["name"]).first()
        if not existing:
            case = models.Case(**case_data)
            db.add(case)
    
    # 2. Создаем предметы (Items)
    items = [
        {"name": "10 Stars", "value_stars": 10, "rarity": models.RarityType.COMMON, "image_url": "star.png"},
        {"name": "50 Stars", "value_stars": 50, "rarity": models.RarityType.COMMON, "image_url": "star_stack.png"},
        {"name": "iPhone 15", "value_stars": 100000, "rarity": models.RarityType.LEGENDARY, "image_url": "iphone.png"},
        {"name": "Tesla Model S", "value_stars": 5000000, "rarity": models.RarityType.MYTHICAL, "image_url": "tesla.png"},
    ]

    for item_data in items:
        existing = db.query(models.Item).filter(models.Item.name == item_data["name"]).first()
        if not existing:
            item = models.Item(**item_data)
            db.add(item)

    db.commit()
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()

