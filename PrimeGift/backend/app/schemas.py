from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .models import CurrencyType, RarityType

class AuthRequest(BaseModel):
    initData: str
    referrer_code: Optional[str] = None

class UserBase(BaseModel):
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    photo_url: Optional[str] = None

class UserResponse(UserBase):
    balance_stars: float
    balance_tickets: int
    referral_code: str
    subscription_reward_claimed: bool
    last_daily_spin: Optional[datetime] = None # <--- Добавил
    created_at: datetime

    class Config:
        from_attributes = True

class CaseSchema(BaseModel):
    id: int
    name: str
    image_url: str
    price: float
    currency: CurrencyType
    is_limited: bool
    limit_total: Optional[int] = None
    limit_remaining: Optional[int] = None

    class Config:
        from_attributes = True
