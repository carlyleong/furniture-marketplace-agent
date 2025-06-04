from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
from datetime import datetime

class ImageData(BaseModel):
    id: str
    filename: str
    url: str
    original_name: str

class ListingBase(BaseModel):
    title: str
    price: float
    condition: str
    description: str
    category: str

class ListingCreate(ListingBase):
    images: List[Dict[str, Any]] = []
    auto_enhance_description: bool = False

class ListingResponse(ListingBase):
    id: str
    images: List[Dict[str, Any]]
    created_at: datetime
    user_id: Optional[str] = None

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str

class DescriptionRequest(BaseModel):
    title: str
    condition: str
    category: str
    description: Optional[str] = None 