from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.utils.security import verify_password, create_access_token
from app.core.config import settings
from app.core.logging import get_logger
from pydantic import BaseModel

logger = get_logger("api.auth")
router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse, summary="Login to get access token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email})
    logger.info(f"User logged in: {user.email}")
    return TokenResponse(access_token=access_token)
