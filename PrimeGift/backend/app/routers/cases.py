from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from .. import database, models, schemas, auth
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
    payload: schemas.OpenCasePayload,
    db: Session = Depends(database.get_db)
):
    # 1. AUTH
    tg_data = auth.validate_init_data(payload.initData)
    if not tg_data and ("demo" in payload.initData or "test" in payload.initData):
        tg_data = {"id": 1} # Fallback for demo
        
    if not tg_data:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    user_id = tg_data["id"]
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # --- БЕСПЛАТНЫЙ КЕЙС (Логика) ---
    if case.price == 0:
        # 1. Global 24h Cooldown Check
        if user.last_daily_spin:
            # Ensure TZ aware
            last_spin = user.last_daily_spin
            if last_spin.tzinfo is None:
                last_spin = last_spin.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            diff = now - last_spin
            
            if diff < timedelta(hours=24):
                remaining_seconds = int((timedelta(hours=24) - diff).total_seconds())
                raise HTTPException(
                    status_code=400, 
                    detail=f"COOLDOWN:{remaining_seconds}"
                )

        # 2. Access Check (Promo OR Condition)
        can_open = False
        used_promo = None
        
        # A. Check Promo
        if payload.promo_code:
            promo = db.query(models.Promocode).filter(models.Promocode.code == payload.promo_code).first()
            if promo:
                if not promo.is_active:
                    raise HTTPException(400, "Promocode is inactive")
                if promo.current_usages >= promo.max_usages:
                    raise HTTPException(400, "Promocode usage limit reached")
                
                # Did user use THIS promo?
                used = db.query(models.UserPromocode).filter(
                    models.UserPromocode.user_id == user.id,
                    models.UserPromocode.promocode_id == promo.id
                ).first()
                
                if used:
                    raise HTTPException(400, "You already used this promocode")
                
                # OK
                can_open = True
                used_promo = promo
            else:
                raise HTTPException(400, "Invalid promocode")
        
        # B. Check Condition (10 Friends) if not opened by promo
        if not can_open:
            friends_count = db.query(models.User).filter(models.User.referrer_id == user.id).count()
            if friends_count >= 10:
                can_open = True
            else:
                # No promo provided and condition not met
                if not payload.promo_code:
                    raise HTTPException(403, "CONDITION_NOT_MET")
        
        if not can_open:
            raise HTTPException(403, "Access denied")
            
        # 3. Apply Usage
        if used_promo:
            db.add(models.UserPromocode(user_id=user.id, promocode_id=used_promo.id))
            used_promo.current_usages += 1
            
        user.last_daily_spin = func.now()

    # --- ПЛАТНЫЙ / ЛИМИТИРОВАННЫЙ ---
    else:
        if case.is_limited:
            if (case.limit_remaining or 0) <= 0:
                raise HTTPException(status_code=400, detail="Sold out")

        if case.currency == models.CurrencyType.STARS:
            if user.balance_stars < case.price:
                raise HTTPException(status_code=400, detail="Not enough stars")
            user.balance_stars -= case.price
        elif case.currency == models.CurrencyType.TICKETS:
            if user.balance_tickets < case.price:
                raise HTTPException(status_code=400, detail="Not enough tickets")
            user.balance_tickets -= int(case.price)
            
        if case.is_limited:
            case.limit_remaining -= 1

    # --- ВЫДАЧА ПРЕДМЕТА ---
    case_items = case.items
    if not case_items:
        won_item = db.query(models.Item).first() # Fallback
    else:
        items = [ci.item for ci in case_items]
        weights = [ci.probability for ci in case_items]
        won_item = random.choices(items, weights=weights, k=1)[0]

    # Save to Inventory
    user_item = models.UserItem(user_id=user.id, item_id=won_item.id)
    db.add(user_item)

    db.commit()
    db.refresh(user)
    
    # Для респонса нам нужно собрать UserItemSchema, но у нас только модель.
    # Pydantic сам не соберет вложенные items без lazy loading, но попробуем.
    # Лучше вернуть словарь.
    
    return {
        "win_item": {
            "id": user_item.id,
            "item": won_item,
            "is_sold": False
        },
        "new_balance_stars": user.balance_stars,
        "new_balance_tickets": user.balance_tickets,
        "remaining": case.limit_remaining
    }
