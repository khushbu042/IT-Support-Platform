from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.config import SECRET_KEY
from app.models import User
from app.schemas import LoginRequest, RegisterRequest

password_hash = PasswordHash.recommended()


def register_user(user: RegisterRequest, db: Session):

    existing_user = (
        db.query(User).filter(User.email == user.email).first()
    )

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = password_hash.hash(user.password_hash)

    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hashed_password,
        role=user.role,
       
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

    if not password_hash.verify(user.password_hash, existing_user.password_hash):
        raise HTTPException(status_code=400, detail="Password is incorrect")

    payload = {
        "user_id": existing_user.id,
        "exp": datetime.now(UTC) + timedelta(minutes=30),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return {
        "success": True,
        "message": "Login successful",
        "access_token": token,
        "token_type": "Bearer",
    }
