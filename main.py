from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import RegisterRequest, LoginRequest, UserResponse
from app.auth import get_current_user
from app.services.user_service import login_user, register_user

app = FastAPI()



@app.get("/")
def test_database(db: Session = Depends(get_db)):
    return {"message": "Database session created successfully"}

@app.post("/register", response_model=UserResponse)
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    return register_user(user,db)

 
@app.post("/login")
def login(user: LoginRequest, db: Session = Depends(get_db)):
    return login_user(user, db)

@app.get("/profile", response_model=UserResponse)
def profile(current_user=Depends(get_current_user)):

    return current_user