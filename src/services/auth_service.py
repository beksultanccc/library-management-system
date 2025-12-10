from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from ..models.user import User, Role
from ..schemas.user import UserCreate
from ..core.security import get_password_hash
from ..services.audit_service import AuditService


class AuthService:
    @staticmethod
    async def register_user(db: Session, user_data: UserCreate) -> User:
        role = db.query(Role).filter(Role.role_name == "student").first()
        if not role:

            role = Role(role_name="student", permissions='{"basic": true}')
            db.add(role)
            db.flush()

        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            role_id=role.role_id
        )

        try:
            db.add(user)
            db.commit()
            db.refresh(user)

            await AuditService.log_action(
                db,
                user_id=user.user_id,
                action="user_registered",
                details={"username": user.username, "email": user.email}
            )

            return user
        except IntegrityError:
            db.rollback()
            raise ValueError("Пайдаланушы аты немесе email бұрыннан бар")

    @staticmethod
    async def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        from ..core.security import verify_password

        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        await AuditService.log_action(
            db,
            user_id=user.user_id,
            action="user_login",
            details={"username": user.username}
        )

        return user

    @staticmethod
    async def change_password(db: Session, user_id: int, old_password: str, new_password: str) -> bool:
        from ..core.security import verify_password, get_password_hash

        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return False

        if not verify_password(old_password, user.password_hash):
            return False

        user.password_hash = get_password_hash(new_password)
        db.commit()

        await AuditService.log_action(
            db,
            user_id=user.user_id,
            action="password_changed",
            details={}
        )

        return True