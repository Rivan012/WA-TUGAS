from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from backend.config import DASHBOARD_TOKEN_EXPIRE_HOURS
from backend.services.auth_service import (
    COOKIE_NAME,
    create_access_token,
    get_current_user,
    verify_login,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(data: LoginRequest, response: Response):
    if not verify_login(data.username, data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah.",
        )

    token = create_access_token(data.username)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=DASHBOARD_TOKEN_EXPIRE_HOURS * 3600,
    )
    return {"success": True, "username": data.username}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"success": True}


@router.get("/me")
def me(username: str = Depends(get_current_user)):
    return {"username": username}
