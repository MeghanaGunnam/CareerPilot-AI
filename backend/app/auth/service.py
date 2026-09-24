from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from backend.app.auth.models import (
    EmailVerificationToken,
    PasswordResetToken,
    Session as AuthSession,
    User,
)
from backend.app.auth.schemas import UserRegister
from backend.app.auth.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    get_email_verification_expiry,
    get_password_reset_expiry,
    get_refresh_token_expiry,
    hash_email_verification_token,
    hash_password,
    hash_password_reset_token,
    hash_refresh_token,
    verify_password,
)


def get_user_by_email(
    db: DBSession,
    email: str,
) -> User | None:
    statement = select(User).where(
        User.email == email.lower()
    )

    return db.scalar(statement)


def create_user(
    db: DBSession,
    data: UserRegister,
) -> User:
    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: DBSession,
    email: str,
    password: str,
) -> User | None:
    user = get_user_by_email(
        db=db,
        email=email,
    )

    if user is None:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user


def create_user_session(
    db: DBSession,
    user: User,
) -> tuple[str, str, int]:
    access_token, expires_in = create_access_token(
        user.id
    )

    refresh_token = create_refresh_token()

    session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(
            refresh_token
        ),
        expires_at=get_refresh_token_expiry(),
    )

    db.add(session)
    db.commit()

    return (
        access_token,
        refresh_token,
        expires_in,
    )


def rotate_refresh_token(
    db: DBSession,
    refresh_token: str,
) -> tuple[str, str, int] | None:
    token_hash = hash_refresh_token(
        refresh_token
    )

    statement = select(AuthSession).where(
        AuthSession.refresh_token_hash == token_hash
    )

    session = db.scalar(statement)

    if session is None:
        return None

    now = datetime.now(timezone.utc)

    if session.revoked_at is not None:
        return None

    if session.expires_at <= now:
        return None

    user = db.get(
        User,
        session.user_id,
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    # Revoke the refresh token that was just used.
    session.revoked_at = now

    access_token, expires_in = create_access_token(
        user.id
    )

    # Rotate to a completely new refresh token.
    new_refresh_token = create_refresh_token()

    new_session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(
            new_refresh_token
        ),
        expires_at=get_refresh_token_expiry(),
    )

    db.add(new_session)
    db.commit()

    return (
        access_token,
        new_refresh_token,
        expires_in,
    )


def revoke_refresh_token(
    db: DBSession,
    refresh_token: str,
) -> bool:
    token_hash = hash_refresh_token(
        refresh_token
    )

    statement = select(AuthSession).where(
        AuthSession.refresh_token_hash == token_hash
    )

    session = db.scalar(statement)

    if session is None:
        return False

    if session.revoked_at is not None:
        return False

    now = datetime.now(timezone.utc)

    if session.expires_at <= now:
        return False

    session.revoked_at = now

    db.commit()

    return True


def create_verification_token(
    db: DBSession,
    user: User,
) -> str:
    now = datetime.now(timezone.utc)

    # Invalidate previous unused verification tokens.
    statement = select(
        EmailVerificationToken
    ).where(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.used_at.is_(None),
    )

    existing_tokens = db.scalars(
        statement
    ).all()

    for existing_token in existing_tokens:
        existing_token.used_at = now

    raw_token = create_email_verification_token()

    verification_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_email_verification_token(
            raw_token
        ),
        expires_at=get_email_verification_expiry(),
    )

    db.add(verification_token)
    db.commit()

    return raw_token


def verify_email_token(
    db: DBSession,
    token: str,
) -> User | None:
    token_hash = hash_email_verification_token(
        token
    )

    statement = select(
        EmailVerificationToken
    ).where(
        EmailVerificationToken.token_hash == token_hash
    )

    verification_token = db.scalar(
        statement
    )

    if verification_token is None:
        return None

    now = datetime.now(timezone.utc)

    if verification_token.used_at is not None:
        return None

    if verification_token.expires_at <= now:
        return None

    user = db.get(
        User,
        verification_token.user_id,
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    verification_token.used_at = now
    user.is_verified = True

    db.commit()
    db.refresh(user)

    return user


def create_password_reset(
    db: DBSession,
    user: User,
) -> str:
    now = datetime.now(timezone.utc)

    # Invalidate previous unused password-reset tokens.
    statement = select(
        PasswordResetToken
    ).where(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    )

    existing_tokens = db.scalars(
        statement
    ).all()

    for existing_token in existing_tokens:
        existing_token.used_at = now

    raw_token = create_password_reset_token()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_password_reset_token(
            raw_token
        ),
        expires_at=get_password_reset_expiry(),
    )

    db.add(reset_token)
    db.commit()

    return raw_token


def reset_password(
    db: DBSession,
    token: str,
    new_password: str,
) -> User | None:
    token_hash = hash_password_reset_token(
        token
    )

    statement = select(
        PasswordResetToken
    ).where(
        PasswordResetToken.token_hash == token_hash
    )

    reset_token = db.scalar(
        statement
    )

    if reset_token is None:
        return None

    now = datetime.now(timezone.utc)

    if reset_token.used_at is not None:
        return None

    if reset_token.expires_at <= now:
        return None

    user = db.get(
        User,
        reset_token.user_id,
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    # Store the new password as an Argon2id hash.
    user.password_hash = hash_password(
        new_password
    )

    # Make the current reset token single-use.
    reset_token.used_at = now

    # Invalidate any other unused reset tokens.
    other_tokens_statement = select(
        PasswordResetToken
    ).where(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    )

    other_tokens = db.scalars(
        other_tokens_statement
    ).all()

    for other_token in other_tokens:
        other_token.used_at = now

    # Revoke every existing refresh-token session.
    sessions_statement = select(
        AuthSession
    ).where(
        AuthSession.user_id == user.id,
        AuthSession.revoked_at.is_(None),
    )

    active_sessions = db.scalars(
        sessions_statement
    ).all()

    for session in active_sessions:
        session.revoked_at = now

    # Password change, reset-token consumption and
    # session revocation are committed together.
    db.commit()
    db.refresh(user)

    return user