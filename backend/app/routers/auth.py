from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import AuthConfigResponse, ChangePasswordRequest, LoginRequest, RegisterRequest, UserResponse
from app.services.auth import (
    count_users,
    create_access_token,
    generate_ntfy_topic,
    get_user_by_username,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


@router.get("/config", response_model=AuthConfigResponse)
async def auth_config():
    return AuthConfigResponse(allow_registration=settings.allow_registration)


@router.post("/register", response_model=UserResponse)
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    if not settings.allow_registration and (await count_users(db)) > 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration is disabled")
    existing = await get_user_by_username(db, body.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    is_first = (await count_users(db)) == 0
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        is_admin=is_first,
        ntfy_topic=generate_ntfy_topic(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(user.id, user.username)
    _set_auth_cookie(response, token)
    return user


@router.post("/login", response_model=UserResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_username(db, body.username)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.ntfy_topic:
        user.ntfy_topic = generate_ntfy_topic()
        await db.commit()
        await db.refresh(user)
    token = create_access_token(user.id, user.username)
    _set_auth_cookie(response, token)
    return user


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(settings.cookie_name, path="/")
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"ok": True}
