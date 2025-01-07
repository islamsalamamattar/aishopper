# app/schemas/user.py
from pydantic import BaseModel, EmailStr, validator, UUID4
from typing import Any, Optional
from datetime import datetime

class UserBase(BaseModel):
    country: str
    phone: str
    email: EmailStr
    first_name: str
    last_name: str
    image_url: Optional[str] = None
    gender: str
    age_group: str

class User(UserBase):
    id: UUID4
    created_at: datetime
    is_disabled: bool

    class Config:
        orm_mode = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    country: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    image_url: Optional[str] = None
    gender: Optional[str] = None
    age_group: Optional[str] = None
    is_disabled: Optional[bool] = None

class UserPatch(UserUpdate):
    pass

class UserRegister(UserBase):
    password: str
    confirm_password: str

    @validator("confirm_password")
    def verify_password_match(cls, v, values, **kwargs):
        password = values.get("password")
        if v != password:
            raise ValueError("The two passwords did not match.")
        return v 
    
    @validator("country")
    def lowercase_country(cls, v):
        return v.lower()

class UserLogin(BaseModel):
    phone: str
    password: str

class UserRegistered(BaseModel):
    phone: str

class ForgotPasswordSchema(BaseModel):
    phone: str

class PasswordResetSchema(BaseModel):
    password: str
    confirm_password: str

    @validator("confirm_password")
    def verify_password_match(cls, v, values, **kwargs):
        password = values.get("password")
        if v != password:
            raise ValueError("The two passwords did not match.")
        return v

class PasswordUpdateSchema(PasswordResetSchema):
    old_password: str

class OldPasswordErrorSchema(BaseModel):
    old_password: bool

    @validator("old_password")
    def check_old_password_status(cls, v, values, **kwargs):
        if not v:
            raise ValueError("Old password is not correct")
        return v
