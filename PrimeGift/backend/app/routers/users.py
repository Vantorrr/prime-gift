from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import database, models, schemas, auth
import random
import string
import httpx

router = APIRouter(
    prefix="/api/users",
    tags=["users"]
)

# --- CONFIG ---
BOT_TOKEN = "8060581855:AAFuo9YTbgQnki1zseuaqbIESR-ahH5yCSs"
CHANNEL_ID = "@TGiftPrime"   # ID или юзернейм канала
ADMIN_IDS = [2053914171, 8141463258]

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.post("/auth", response_model=schemas.UserResponse)
async def auth_telegram(
    auth_data: schemas.AuthRequest,
    db: Session = Depends(database.get_db)
):
    # 1. Валидация
    tg_user = auth.validate_init_data(auth_data.initData, BOT_TOKEN)
    
    # Фолбек для Demo
    if not tg_user and ("test" in auth_data.initData or "demo" in auth_data.initData): 
         tg_user = {"id": 1, "username": "demo_user", "first_name": "Demo", "photo_url": None}
    
    if not tg_user:
        raise HTTPException(status_code=401, detail="Invalid data")
        
    user_id = tg_user["id"]
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    
    # 2. РЕГИСТРАЦИЯ НОВОГО
    if not db_user:
        # Создаем юзера
        new_user = models.User(
            id=user_id,
            username=tg_user.get("username"),
            first_name=tg_user.get("first_name"),
            photo_url=tg_user.get("photo_url"),
            referral_code=generate_referral_code(),
            balance_stars=100.0,
            balance_tickets=0
        )
        
        # 3. ЛОГИКА РЕФЕРАЛКИ
        if auth_data.referrer_code:
            referrer = db.query(models.User).filter(models.User.referral_code == auth_data.referrer_code).first()
            if referrer and referrer.id != user_id:
                new_user.referrer_id = referrer.id
                
                # 1. Базовая награда: +1 Купон за каждого друга
                referrer.balance_tickets += 1
                
                # 2. Майлстоуны (10 друзей = 500 звезд, 20 друзей = 1000 звезд)
                friends_count = db.query(models.User).filter(models.User.referrer_id == referrer.id).count()
                new_total = friends_count + 1 
                
                if new_total == 10:
                    referrer.balance_stars += 500.0
                elif new_total == 20:
                    referrer.balance_stars += 1000.0 

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        new_user.referrals_count = 0
        new_user.is_admin = user_id in ADMIN_IDS
        return new_user
    
    # Обновление профиля (Аватар и Юзернейм)
    if db_user.username != tg_user.get("username") or db_user.photo_url != tg_user.get("photo_url"):
        db_user.username = tg_user.get("username")
        db_user.photo_url = tg_user.get("photo_url")
        db.commit()
    
    # Считаем рефералов для ответа
    ref_count = db.query(models.User).filter(models.User.referrer_id == db_user.id).count()
    db_user.referrals_count = ref_count
    db_user.is_admin = user_id in ADMIN_IDS
        
    return db_user

@router.post("/check-subscription")
async def check_subscription(
    auth_data: schemas.AuthRequest,
    db: Session = Depends(database.get_db)
):
    # 1. Ищем юзера
    tg_user = auth.validate_init_data(auth_data.initData, BOT_TOKEN)
    if not tg_user and ("test" in auth_data.initData or "demo" in auth_data.initData):
        tg_user = {"id": 1} # Demo ID
        
    if not tg_user:
        raise HTTPException(status_code=401, detail="Invalid auth")
        
    user = db.query(models.User).filter(models.User.id == tg_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Проверяем подписку через Telegram API
    is_subscribed = False
    
    # REAL MODE (Token is set)
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
            response = await client.get(url, params={"chat_id": CHANNEL_ID, "user_id": user.id})
            data = response.json()
            if data.get("ok"):
                status = data["result"]["status"]
                if status in ["creator", "administrator", "member"]:
                    is_subscribed = True
    except Exception as e:
        print(f"Telegram API Error: {e}")
            
    if not is_subscribed:
        return {"subscribed": False, "reward_claimed": user.subscription_reward_claimed}

    # 3. Начисляем награду (если еще не брал)
    reward_given = False
    if not user.subscription_reward_claimed:
        # НАГРАДА: 1 Токен
        user.balance_tickets += 1
        user.subscription_reward_claimed = True
        db.commit()
        reward_given = True
        
    return {
        "subscribed": True,
        "reward_claimed": True,
        "just_rewarded": reward_given,
        "new_balance": user.balance_tickets
    }
