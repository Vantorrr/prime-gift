from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from .. import database, models, schemas
import random

router = APIRouter(
    prefix="/api/cases",
    tags=["cases"]
)

@router.get("/", response_model=list[schemas.CaseSchema])
async def get_cases(db: Session = Depends(database.get_db)):
    return db.query(models.Case).all()

@router.post("/{case_id}/open")
async def open_case(
    case_id: int,
    auth: schemas.AuthRequest,
    db: Session = Depends(database.get_db)
):
    # В MVP user_id=1 (Demo)
    user_id = 1 
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # --- ЛОГИКА БЕСПЛАТНОГО КЕЙСА (24ч) ---
    if case.price == 0 and "бесплатн" in case.name.lower(): # Или по ID/типу
        if user.last_daily_spin:
            # Проверяем, прошло ли 24 часа
            # last_daily_spin в UTC? Да, datetime.now(timezone.utc)
            now = datetime.now(timezone.utc)
            # Приводим к offset-aware, если в базе offset-naive
            last_spin = user.last_daily_spin
            if last_spin.tzinfo is None:
                last_spin = last_spin.replace(tzinfo=timezone.utc)
                
            diff = now - last_spin
            if diff < timedelta(hours=24):
                remaining_seconds = int((timedelta(hours=24) - diff).total_seconds())
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cooldown: {remaining_seconds}s"
                )
        
        # Обновляем время
        user.last_daily_spin = func.now()

    # Проверка лимитов
    if case.is_limited:
        if (case.limit_remaining or 0) <= 0:
            raise HTTPException(status_code=400, detail="Sold out")

    # Проверка баланса (для платных)
    if case.price > 0:
        if case.currency == models.CurrencyType.STARS:
            if user.balance_stars < case.price:
                raise HTTPException(status_code=400, detail="Not enough stars")
            user.balance_stars -= case.price
        elif case.currency == models.CurrencyType.TICKETS:
            if user.balance_tickets < case.price:
                raise HTTPException(status_code=400, detail="Not enough tickets")
            user.balance_tickets -= int(case.price)

    # Выбор предмета
    case_items = case.items
    if not case_items:
        # Если база пустая, фолбэк на заглушку (чтобы не крашилось)
        won_item = db.query(models.Item).first()
    else:
        items = [ci.item for ci in case_items]
        weights = [ci.probability for ci in case_items]
        won_item = random.choices(items, weights=weights, k=1)[0]

    # Сохраняем в инвентарь
    user_item = models.UserItem(user_id=user.id, item_id=won_item.id)
    db.add(user_item)

    if case.is_limited:
        case.limit_remaining -= 1

    db.commit()
    db.refresh(user)
    
    return {
        "item": won_item,
        "remaining": case.limit_remaining,
        "balance_stars": user.balance_stars,
        "balance_tickets": user.balance_tickets,
        "last_daily_spin": user.last_daily_spin # Возвращаем, чтобы обновить таймер
    }
