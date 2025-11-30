from app.database import SessionLocal, engine
from app.models import Promocode, Base

# Ensure tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

codes = ["WELCOME", "FREEGIFT", "PRIME2024"]

for code in codes:
    try:
        exists = db.query(Promocode).filter(Promocode.code == code).first()
        if not exists:
            promo = Promocode(code=code, max_usages=10000)
            db.add(promo)
            print(f"Created promo: {code}")
        else:
            print(f"Promo {code} exists")
    except Exception as e:
        print(f"Error checking code {code}: {e}")

db.commit()
db.close()
