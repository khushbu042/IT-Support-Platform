from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.config import SECRET_KEY
from app.models import User, UserStatus
from app.schemas import LoginRequest, RegisterRequest

password_hash = PasswordHash.recommended()


def register_user(user: RegisterRequest, db: Session):

    existing_user = (
        db.query(User).filter(User.email == user.email).first()
    )

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = password_hash.hash(user.password)

    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        role=user.role,
        department=user.department,
        team=user.team,
        status=UserStatus.ACTIVE,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def login_user(user: LoginRequest, db: Session):
    existing_user = db.query(User).filter(User.email == user.email).first()

    if not existing_user:
        raise HTTPException(
            status_code=400, detail="User email does not exist. Please register."
        )

    if not password_hash.verify(user.password, existing_user.password):
        raise HTTPException(status_code=400, detail="Password is incorrect")

    payload = {
        "user_id": existing_user.id,
        "exp": datetime.now(UTC) + timedelta(minutes=30),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 1800,
            "user": {
                "id": existing_user.id,
                "name": existing_user.name,
                "email": existing_user.email,
                "role": existing_user.role,
                "department": existing_user.department,
                "team": existing_user.team,
                "status": existing_user.status,
            },
        },
    }
