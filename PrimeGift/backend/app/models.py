from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base

class CurrencyType(str, enum.Enum):
    STARS = "stars"
    TICKETS = "tickets"

class RarityType(str, enum.Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHICAL = "mythical"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True) # Telegram ID
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    
    balance_stars = Column(Float, default=0.0)
    balance_tickets = Column(Integer, default=0)
    
    referral_code = Column(String, unique=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    subscription_reward_claimed = Column(Boolean, default=False)
    
    # --- НОВОЕ ПОЛЕ: Время последнего бесплатного прокрута ---
    last_daily_spin = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    inventory = relationship("UserItem", back_populates="user")
    referrer = relationship("User", remote_side=[id], backref="referrals")
    promocodes_used = relationship("UserPromocode", backref="user")

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    image_url = Column(String)
    
    price = Column(Float)
    currency = Column(Enum(CurrencyType), default=CurrencyType.STARS)
    
    is_limited = Column(Boolean, default=False)
    limit_total = Column(Integer, nullable=True)
    limit_remaining = Column(Integer, nullable=True)
    
    items = relationship("CaseItem", back_populates="case")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    image_url = Column(String)
    rarity = Column(Enum(RarityType), default=RarityType.COMMON)
    value_stars = Column(Float)
    
    cases = relationship("CaseItem", back_populates="item")

class CaseItem(Base):
    __tablename__ = "case_items"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    probability = Column(Float)
    
    case = relationship("Case", back_populates="items")
    item = relationship("Item", back_populates="cases")

class UserItem(Base):
    __tablename__ = "user_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    obtained_at = Column(DateTime(timezone=True), server_default=func.now())
    is_sold = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="inventory")
    item = relationship("Item")

class Promocode(Base):
    __tablename__ = "promocodes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    max_usages = Column(Integer, default=10000)
    current_usages = Column(Integer, default=0)

class UserPromocode(Base):
    __tablename__ = "user_promocodes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    promocode_id = Column(Integer, ForeignKey("promocodes.id"))
    used_at = Column(DateTime(timezone=True), server_default=func.now())
