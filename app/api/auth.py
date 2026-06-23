from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.config import settings
from app.utils.auth import create_token

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    if data.username != settings.ADMIN_USERNAME or \
       data.password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )
    token = create_token(data.username)
    return TokenResponse(access_token=token)
