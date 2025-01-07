from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# Base schema for common fields between create and update operations
class ProfileBase(BaseModel):
    fav_categories: Optional[List[str]] = None
    cart: Optional[List[dict]] = None
    wishlist: Optional[List[dict]] = None

# Schema for reading a profile (i.e., the complete Profile model)
class Profile(ProfileBase):
    id: UUID
    created_at: datetime
    user_id: UUID
    is_deleted: bool

    class Config:
        orm_mode = True

# Schema for creating a new profile
class ProfileCreate(ProfileBase):
    pass  # Inherits from ProfileBase, no additional fields

# Schema for updating an existing profile
class ProfileUpdate(BaseModel):
    fav_categories: Optional[List[str]] = None
    cart: Optional[List[dict]] = None
    wishlist: Optional[List[dict]] = None
    is_deleted: Optional[bool] = None
