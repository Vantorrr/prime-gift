from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .models import CurrencyType, RarityType

class AuthRequest(BaseModel):
    initData: str
    referrer_code: Optional[str] = None

class OpenCasePayload(AuthRequest):
    promo_code: Optional[str] = None

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
    last_daily_spin: Optional[datetime] = None
    created_at: datetime
    referrals_count: int = 0
    is_admin: bool = False

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

class OpenCaseRequest(BaseModel):
    promo_code: Optional[str] = None

class ItemSchema(BaseModel):
    id: int
    name: str
    image_url: str
    value_stars: float
    rarity: RarityType

    class Config:
        from_attributes = True

class UserItemSchema(BaseModel):
    id: int
    item: ItemSchema
    is_sold: bool

    class Config:
        from_attributes = True

class SellItemRequest(BaseModel):
    user_item_id: int

class SellItemResponse(BaseModel):
    success: bool
    stars_added: float
    new_balance: float

class OpenCaseResponse(BaseModel):
    win_item: UserItemSchema
    new_balance_stars: float
    new_balance_tickets: int
