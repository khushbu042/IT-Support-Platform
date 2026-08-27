from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.config import SECRET_KEY
from app.models import User
from app.schemas import LoginRequest, RegisterRequest
from app.services.rate_limit.login import check_login_rate_limit, record_failed_login, check_ip_rate_limit

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


async def login_user(user: LoginRequest, db: Session, ip_address: str):
    existing_user = db.query(User).filter(User.email == user.email).first()

    if not existing_user:

        rate_limit = await check_ip_rate_limit(ip_address)
        if not rate_limit["allowed"]:
            raise HTTPException(
                status_code=429,
                detail="Too many failed login attempts. Please try again later.",
            )

        await record_failed_login(
            user_id=None,
            ip_address=ip_address,
        )

        raise HTTPException(
            status_code=400, detail="User email does not exist. Please register."
        )

    rate_limit = await check_login_rate_limit(
        user_id=existing_user.id,
        ip_address=ip_address
    )

    if not rate_limit["allowed"]:
        raise HTTPException(
            status_code=429,
            detail="Too many Failed login attempts. Please try again with correct Credentials",
        )

    if not password_hash.verify(user.password_hash, existing_user.password_hash):
        await record_failed_login(
            user_id=existing_user.id,
            ip_address=ip_address
        )
        raise HTTPException(status_code=401, detail="Password is incorrect")

    payload = {
        "user_id": existing_user.id,
        "role": existing_user.role.value,
        "exp": datetime.now(UTC) + timedelta(minutes=30),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return {
        "success": True,
        "message": "Login successful",
        "access_token": token,
        "token_type": "Bearer",
    }
