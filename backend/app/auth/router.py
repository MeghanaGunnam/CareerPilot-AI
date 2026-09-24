from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.auth.schemas import (
    ForgotPasswordRequest,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    VerifyEmailRequest,
)
from backend.app.auth.service import (
    authenticate_user,
    create_password_reset,
    create_user,
    create_user_session,
    create_verification_token,
    get_user_by_email,
    reset_password,
    revoke_refresh_token,
    rotate_refresh_token,
    verify_email_token,
)
from backend.app.core.database import get_db
from backend.app.email.service import (
    send_password_reset_email,
    send_verification_email,
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    data: UserRegister,
    db: Session = Depends(get_db),
) -> UserResponse:
    existing_user = get_user_by_email(
        db=db,
        email=data.email,
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = create_user(
        db=db,
        data=data,
    )

    verification_token = create_verification_token(
        db=db,
        user=user,
    )

    send_verification_email(
        email=user.email,
        token=verification_token,
    )

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login_user(
    data: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = authenticate_user(
        db=db,
        email=data.email,
        password=data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    access_token, refresh_token, expires_in = create_user_session(
        db=db,
        user=user,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def refresh_access_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    tokens = rotate_refresh_token(
        db=db,
        refresh_token=data.refresh_token,
    )

    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    access_token, new_refresh_token, expires_in = tokens

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=expires_in,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout_user(
    data: LogoutRequest,
    db: Session = Depends(get_db),
) -> None:
    revoke_refresh_token(
        db=db,
        refresh_token=data.refresh_token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.post(
    "/verify-email",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def verify_email(
    data: VerifyEmailRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    user = verify_email_token(
        db=db,
        token=data.token,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token.",
        )

    return user


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def resend_verification(
    data: ResendVerificationRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    user = get_user_by_email(
        db=db,
        email=data.email,
    )

    if (
        user is not None
        and user.is_active
        and not user.is_verified
    ):
        verification_token = create_verification_token(
            db=db,
            user=user,
        )

        send_verification_email(
            email=user.email,
            token=verification_token,
        )

    return MessageResponse(
        message=(
            "If the account exists and requires verification, "
            "a verification email will be sent."
        )
    )


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    user = get_user_by_email(
        db=db,
        email=data.email,
    )

    if user is not None and user.is_active:
        reset_token = create_password_reset(
            db=db,
            user=user,
        )

        send_password_reset_email(
            email=user.email,
            token=reset_token,
        )

    return MessageResponse(
        message=(
            "If an account exists for this email, "
            "password reset instructions will be sent."
        )
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def reset_user_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    user = reset_password(
        db=db,
        token=data.token,
        new_password=data.new_password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    return MessageResponse(
        message="Password reset successfully."
    )