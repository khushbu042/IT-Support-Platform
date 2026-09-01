from enum import Enum
from app.core.permissions import Permission, ROLE_PERMISSIONS

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import SECRET_KEY
from app.database import get_db
from app.models import User

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        user_id = payload.get("user_id")

        current_user = db.query(User).filter(User.id == user_id).first()

        if not current_user:
            raise HTTPException(status_code=401, detail="User not found")
        return current_user

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_permission(*required: Permission):
    def checker(current_user: User = Depends(get_current_user)):
        user_permissions = ROLE_PERMISSIONS.get(current_user.role.value, set())
        if not set(required).issubset(user_permissions):
            raise HTTPException(
                status_code=403,
                detail=f"Missing required permission(s): {required}"
            )
        return current_user
    return checker