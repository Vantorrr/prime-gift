from app.database import SessionLocal, engine
from app.models import Case, Item, CaseItem, Base

db = SessionLocal()

try:
    # 1. Clear existing cases (cascade will handle case_items usually, but let's be safe)
    db.query(CaseItem).delete()
    db.query(Case).delete()
    db.commit()
    print("Deleted all cases.")

    # 2. Create "Бесплатный"
    free_case = Case(
        name="Бесплатный",
        image_url="/freenonfon.png",
        price=0,
        currency="stars",
        is_limited=False
    )
    db.add(free_case)
    
    # 3. Create "Новогодний"
    ny_case = Case(
        name="Новогодний",
        image_url="/NewYearCase.png",
        price=500,
        currency="stars",
        is_limited=True,
        limit_total=1000,
        limit_remaining=1000
    )
    db.add(ny_case)
    db.commit()

    # Reload to get IDs
    db.refresh(free_case)
    db.refresh(ny_case)
    print(f"Created cases: {free_case.name} (ID {free_case.id}), {ny_case.name} (ID {ny_case.id})")

    # 4. Create/Get Items
    items_data = [
        {"name": "10 Звезд", "image_url": "/star.png", "value_stars": 10, "rarity": "common"},
        {"name": "50 Звезд", "image_url": "/star.png", "value_stars": 50, "rarity": "common"},
        {"name": "100 Звезд", "image_url": "/star.png", "value_stars": 100, "rarity": "rare"},
        {"name": "iPhone 15", "image_url": "/iphone.png", "value_stars": 50000, "rarity": "legendary"},
        {"name": "Tesla Model S", "image_url": "/tesla.png", "value_stars": 1000000, "rarity": "mythical"}
    ]

    db_items = {}
    for data in items_data:
        existing = db.query(Item).filter(Item.name == data["name"]).first()
        if not existing:
            item = Item(**data)
            db.add(item)
            db.commit()
            db.refresh(item)
            db_items[data["name"]] = item
        else:
            db_items[data["name"]] = existing

    # 5. Link to Free Case
    db.add(CaseItem(case_id=free_case.id, item_id=db_items["10 Звезд"].id, probability=0.7))
    db.add(CaseItem(case_id=free_case.id, item_id=db_items["50 Звезд"].id, probability=0.29))
    db.add(CaseItem(case_id=free_case.id, item_id=db_items["iPhone 15"].id, probability=0.01))

    # 6. Link to NY Case
    db.add(CaseItem(case_id=ny_case.id, item_id=db_items["50 Звезд"].id, probability=0.4))
    db.add(CaseItem(case_id=ny_case.id, item_id=db_items["100 Звезд"].id, probability=0.4))
    db.add(CaseItem(case_id=ny_case.id, item_id=db_items["iPhone 15"].id, probability=0.15))
    db.add(CaseItem(case_id=ny_case.id, item_id=db_items["Tesla Model S"].id, probability=0.05))

    db.commit()
    print("Linked items successfully.")

except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()

