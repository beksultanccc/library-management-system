from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.security import get_current_user
from src.models.user import User, Role

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    user = get_current_user(db, token)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пайдаланушы белсенді емес"
        )
    return user

def require_roles(required_roles: list):
    def role_checker(current_user: User = Depends(get_current_active_user)):
        role_name = current_user.role.role_name.lower()
        if role_name not in required_roles and role_name != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Рұқсат жеткіліксіз"
            )
        return current_user
    return role_checker

def get_admin_user(current_user: User = Depends(get_current_active_user)):
    if current_user.role.role_name.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тек әкімшілерге рұқсат"
        )
    return current_user

def get_librarian_user(current_user: User = Depends(get_current_active_user)):
    role_name = current_user.role.role_name.lower()
    if role_name not in ["librarian", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тек кітапханашыларға рұқсат"
        )
    return current_user