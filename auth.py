from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from app.models.user import User, UserRole
from app.utils.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import limiter
from app.routes.schemas.auth_schemas import (
    RegisterRequest, LoginRequest, RefreshTokenRequest,
    TokenResponse, ChangePasswordRequest,
)
from fastapi import Request

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _user_to_dict(user: User) -> dict:
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "language": user.language,
        "avatar_url": user.avatar_url,
        "is_verified": user.is_verified,
        "reports_count": user.reports_count,
    }


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest):
    existing = await User.find_one(User.email == body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        language=body.language,
        phone=body.phone,
    )
    await user.insert()

    token_data = {"sub": str(user.id), "role": user.role}
    access_token  = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    user.refresh_token = refresh_token
    await user.save()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_to_dict(user),
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest):
    user = await User.find_one(User.email == body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    token_data = {"sub": str(user.id), "role": user.role}
    access_token  = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    user.refresh_token = refresh_token
    user.last_login = datetime.utcnow()
    await user.save()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_to_dict(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshTokenRequest):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = await User.get(payload["sub"])
    if not user or user.refresh_token != body.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token mismatch",
        )

    token_data = {"sub": str(user.id), "role": user.role}
    access_token  = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    user.refresh_token = refresh_token
    await user.save()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_to_dict(user),
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    current_user.refresh_token = None
    await current_user.save()
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"success": True, "user": _user_to_dict(current_user)}


@router.put("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.password_hash = hash_password(body.new_password)
    await current_user.save()
    return {"success": True, "message": "Password updated"}
