from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminUserSummary(BaseModel):
    id: int
    username: str
    is_admin: bool
    onboarded: bool
    created_at: str | None = None

    model_config = {"from_attributes": True}


class AdminUserPatch(BaseModel):
    is_admin: bool | None = None


@router.get("/users", response_model=list[AdminUserSummary])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).order_by(User.username))
    users = result.scalars().all()
    return [
        AdminUserSummary(
            id=u.id,
            username=u.username,
            is_admin=u.is_admin,
            onboarded=u.onboarded,
            created_at=u.created_at.isoformat() if u.created_at else None,
        )
        for u in users
    ]


@router.patch("/users/{user_id}", response_model=AdminUserSummary)
async def update_user(
    user_id: int,
    body: AdminUserPatch,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == admin.id and body.is_admin is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot demote yourself")
    if body.is_admin is not None:
        user.is_admin = body.is_admin
    await db.commit()
    await db.refresh(user)
    return AdminUserSummary(
        id=user.id,
        username=user.username,
        is_admin=user.is_admin,
        onboarded=user.onboarded,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )
