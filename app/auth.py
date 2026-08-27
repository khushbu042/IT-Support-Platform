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

def require_role(*allowed_roles: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code = 403,
                detail = f"Requires one of roles: {allowed_roles}"
            )

        return current_user
    return role_checker