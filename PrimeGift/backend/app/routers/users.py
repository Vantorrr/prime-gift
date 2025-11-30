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
BOT_TOKEN = "YOUR_BOT_TOKEN" # Вставь сюда токен бота, если есть
CHANNEL_ID = "@TGiftPrime"   # ID или юзернейм канала

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.post("/auth", response_model=schemas.UserResponse)
async def auth_telegram(
    auth_data: schemas.AuthRequest,
    db: Session = Depends(database.get_db)
):
    # 1. Валидация
    tg_user = auth.validate_init_data(auth_data.initData)
    
    # Фолбек для Demo
    if not tg_user and ("test" in auth_data.initData or "demo" in auth_data.initData): 
         tg_user = {"id": 1, "username": "demo_user", "first_name": "Demo"}
    
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
                referrer.balance_tickets += 1
                
                friends_count = db.query(models.User).filter(models.User.referrer_id == referrer.id).count()
                # Награда за 10 друзей (было 5)
                if (friends_count + 1) % 10 == 0:
                    # Даем 5 БИЛЕТОВ (Купонов)
                    referrer.balance_tickets += 5 

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    # Обновление профиля
    if db_user.username != tg_user.get("username"):
        db_user.username = tg_user.get("username")
        db_user.photo_url = tg_user.get("photo_url")
        db.commit()
        
    return db_user

@router.post("/check-subscription")
async def check_subscription(
    auth_data: schemas.AuthRequest,
    db: Session = Depends(database.get_db)
):
    # 1. Ищем юзера
    tg_user = auth.validate_init_data(auth_data.initData)
    if not tg_user and ("test" in auth_data.initData or "demo" in auth_data.initData):
        tg_user = {"id": 1} # Demo ID
        
    if not tg_user:
        raise HTTPException(status_code=401, detail="Invalid auth")
        
    user = db.query(models.User).filter(models.User.id == tg_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Проверяем подписку через Telegram API
    is_subscribed = False
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN":
        # DEMO MODE: Всегда считаем, что подписан, для теста
        is_subscribed = True 
    else:
        # REAL MODE
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
                response = await client.get(url, params={"chat_id": CHANNEL_ID, "user_id": user.id})
                data = response.json()
                if data.get("ok"):
                    status = data["result"]["status"]
                    # 'creator', 'administrator', 'member', 'restricted' (if is_member is True)
                    if status in ["creator", "administrator", "member"]:
                        is_subscribed = True
        except Exception as e:
            print(f"Telegram API Error: {e}")
            
    if not is_subscribed:
        return {"subscribed": False, "reward_claimed": user.subscription_reward_claimed}

    # 3. Начисляем награду (если еще не брал)
    reward_given = False
    if not user.subscription_reward_claimed:
        # НАГРАДА: 1 Токен (или бесплатный прокрут)
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
