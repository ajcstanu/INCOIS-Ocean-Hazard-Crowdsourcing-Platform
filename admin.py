from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.models.user import User, UserRole
from app.middleware.auth import require_admin
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin"])


class UpdateUserRoleRequest(BaseModel):
    role: UserRole


class UpdateUserStatusRequest(BaseModel):
    is_active: bool


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    _=Depends(require_admin),
):
    query = {}
    if role:
        query["role"] = role
    if is_active is not None:
        query["is_active"] = is_active

    skip = (page - 1) * limit
    users = await User.find(query).skip(skip).limit(limit).sort("-created_at").to_list()
    total = await User.find(query).count()

    return {
        "success": True,
        "data": [
            {
                "id": str(u.id),
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "reports_count": u.reports_count,
                "created_at": u.created_at,
                "last_login": u.last_login,
            }
            for u in users
        ],
        "pagination": {"page": page, "limit": limit, "total": total},
    }


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    body: UpdateUserRoleRequest,
    _=Depends(require_admin),
):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = body.role
    await user.save()
    return {"success": True, "message": f"Role updated to {body.role}"}


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    body: UpdateUserStatusRequest,
    _=Depends(require_admin),
):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = body.is_active
    await user.save()
    status_str = "activated" if body.is_active else "deactivated"
    return {"success": True, "message": f"User {status_str}"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, _=Depends(require_admin)):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user.delete()
    return {"success": True, "message": "User deleted"}
