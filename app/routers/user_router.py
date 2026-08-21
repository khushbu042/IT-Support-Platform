from fastapi import APIRouter, Depends
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


@router.post("/login", response_model=LoginResponseSchema)
def login(user: LoginRequest, db: Session = Depends(get_db)):
    return login_user(user, db)


@router.get("/profile", response_model=UserResponse)
def profile(current_user=Depends(get_current_user)):
    return current_user
