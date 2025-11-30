from app.database import SessionLocal
from app import models

db = SessionLocal()

def link_items():
    print("Linking items to cases...")
    
    # Get Cases
    new_year_case = db.query(models.Case).filter(models.Case.name == "Новогодний").first()
    free_case = db.query(models.Case).filter(models.Case.name == "Бесплатный").first() or \
                db.query(models.Case).filter(models.Case.name == "Starter Box").first()

    # Get Items
    star_10 = db.query(models.Item).filter(models.Item.name == "10 Stars").first()
    star_50 = db.query(models.Item).filter(models.Item.name == "50 Stars").first()
    iphone = db.query(models.Item).filter(models.Item.name == "iPhone 15").first()
    tesla = db.query(models.Item).filter(models.Item.name == "Tesla Model S").first()

    # Helper to add link if not exists
    def add_link(case, item, prob):
        if not case or not item: return
        exists = db.query(models.CaseItem).filter_by(case_id=case.id, item_id=item.id).first()
        if not exists:
            print(f"Adding {item.name} to {case.name} ({prob})")
            link = models.CaseItem(case_id=case.id, item_id=item.id, probability=prob)
            db.add(link)

    # 1. Новогодний Кейс (Premium)
    # iPhone (1%), 50 Stars (50%), 10 Stars (49%)
    add_link(new_year_case, iphone, 0.01)
    add_link(new_year_case, star_50, 0.50)
    add_link(new_year_case, star_10, 0.49)

    # 2. Free Case
    # Tesla (0.0001%), 10 Stars (99.9%)
    add_link(free_case, tesla, 0.00001)
    add_link(free_case, star_10, 0.99999)

    db.commit()
    print("Linked!")

if __name__ == "__main__":
    link_items()

