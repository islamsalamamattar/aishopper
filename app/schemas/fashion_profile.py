# app/schemas/FashionProfile.py
from pydantic import BaseModel, UUID4, Field
from typing import Optional
from datetime import datetime


class FashionProfileBase(BaseModel):
    name: str
    category: str  # Male | Female | Kids
    relation: Optional[str] = None  # Self | Spouse | Child | Parent | Friend
    age: Optional[int] = None
    weight: Optional[int] = None
    height: Optional[int] = None
    chest_shape: Optional[str] = None
    abdomen_shape: Optional[str] = None
    hip_shape: Optional[str] = None
    fitting: Optional[str] = None
    bra_sizing: Optional[str] = None  # European,Korean | American,English | French,Spanish | Italian
    bra_underband: Optional[int] = None  # 60 > 125 | 28 > 54 | 75 > 140 | 0 > 12
    bra_cup: Optional[str] = None


class FashionProfileCreate(FashionProfileBase):
    pass


class FashionProfileUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    relation: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[int] = None
    height: Optional[int] = None
    chest_shape: Optional[str] = None
    abdomen_shape: Optional[str] = None
    hip_shape: Optional[str] = None
    fitting: Optional[str] = None
    bra_sizing: Optional[str] = None
    bra_underband: Optional[int] = None
    bra_cup: Optional[str] = None


class FashionProfile(FashionProfileBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    is_deleted: bool

    class Config:
        orm_mode = True
