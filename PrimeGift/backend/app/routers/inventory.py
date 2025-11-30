from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database, models, schemas

router = APIRouter(
    prefix="/api/inventory",
    tags=["inventory"]
)

@router.get("/{user_id}")
async def get_inventory(user_id: int, db: Session = Depends(database.get_db)):
    # Возвращаем только активные (не проданные) предметы
    # Join с Item, чтобы получить название и картинку
    items = db.query(models.UserItem).join(models.Item).filter(
        models.UserItem.user_id == user_id,
        models.UserItem.is_sold == False
    ).all()
    
    # Формируем красивый ответ
    return [
        {
            "id": ui.id, # ID записи в инвентаре (для продажи)
            "item_id": ui.item.id,
            "name": ui.item.name,
            "image_url": ui.item.image_url,
            "rarity": ui.item.rarity,
            "value": ui.item.value_stars,
            "obtained_at": ui.obtained_at
        }
        for ui in items
    ]

@router.post("/sell/{user_item_id}")
async def sell_item(user_item_id: int, db: Session = Depends(database.get_db)):
    # 1. Ищем предмет у юзера
    user_item = db.query(models.UserItem).filter(models.UserItem.id == user_item_id).first()
    if not user_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if user_item.is_sold:
        raise HTTPException(status_code=400, detail="Item already sold")

    # 2. Начисляем звезды
    user = user_item.user
    sell_price = user_item.item.value_stars
    user.balance_stars += sell_price
    
    # 3. Помечаем как проданный
    user_item.is_sold = True
    
    db.commit()
    
    return {
        "status": "sold",
        "earned": sell_price,
        "new_balance": user.balance_stars
    }

