from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.schemas import LoginRequest, RegisterRequest, UserResponse, LoginResponseSchema
from app.services.user_service import login_user, register_user

router = APIRouter()


# @router.get("/")
# def test_database(db: Session = Depends(get_db)):
#     return {"message": "Database session created successfully"}


@router.post("/register", response_model=UserResponse)
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    return register_user(user, db)


@router.post("/login")
async def login(
    user: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    print(request)
    return await login_user(user=user, db=db, ip_address=request.client.host)


@router.get("/profile", response_model=UserResponse)
def profile(current_user=Depends(get_current_user)):
    return current_user
