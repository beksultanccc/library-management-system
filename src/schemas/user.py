from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime


class RoleBase(BaseModel):
    role_name: str
    permissions: Optional[str] = "{}"


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    role_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль кемінде 8 таңбадан тұруы керек')
        if not any(char.isdigit() for char in v):
            raise ValueError('Пароль кемінде бір санды қамтуы керек')
        if not any(char.isupper() for char in v):
            raise ValueError('Пароль кемінде бір бас әріптен тұруы керек')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    user_id: int
    role_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None