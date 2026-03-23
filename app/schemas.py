from pydantic import BaseModel, EmailStr
from typing import Optional

# --- USER SCHEMAS ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool

    model_config = {"from_attributes": True}

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token: str
    new_password: str

# --- POST SCHEMAS ---
class PostResponse(BaseModel):
    id: int
    content: str
    image_url: Optional[str] = None
    owner_id: int

    model_config = {"from_attributes": True}

# --- AUTH SCHEMAS ---
class Token(BaseModel):
    access_token: str
    token_type: str