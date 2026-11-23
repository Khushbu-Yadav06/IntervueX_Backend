
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.auth import UserRegister, UserLogin
from services.auth_service import register_user, authenticate_user
from services.security import create_access_token
from services.security import get_current_user
from database.models import User


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: UserRegister, db: Session = Depends(get_db)):

    user = register_user(
        db=db,
        full_name=request.full_name.strip(),
        email=request.email.lower(),
        password=request.password
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered."
        )

    return {
        "status": "success",
        "message": "User registered successfully.",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email
        }
    }


@router.post("/login")
def login(request: UserLogin, db: Session = Depends(get_db)):

    user = authenticate_user(
        db=db,
        email=request.email.lower(),
        password=request.password
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = create_access_token(user.id)

    return {
        "status": "success",
        "message": "Login successful.",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email
        }
    }

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):

    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email
    }