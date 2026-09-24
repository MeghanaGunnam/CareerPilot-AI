from backend.app.core.config import settings


def build_verification_url(token: str) -> str:
    return f"{settings.frontend_url}/verify-email?token={token}"


def build_password_reset_url(token: str) -> str:
    return f"{settings.frontend_url}/reset-password?token={token}"


def send_verification_email(
    email: str,
    token: str,
) -> None:
    verification_url = build_verification_url(token)

    if settings.app_env == "development":
        print()
        print("=" * 70)
        print("CAREERPILOT DEVELOPMENT EMAIL")
        print(f"To: {email}")
        print("Subject: Verify your CareerPilot AI account")
        print(f"Verification URL: {verification_url}")
        print("=" * 70)
        print()
        return

    # Production email provider will be connected later.
    raise RuntimeError(
        "Production email provider is not configured."
    )


def send_password_reset_email(
    email: str,
    token: str,
) -> None:
    reset_url = build_password_reset_url(token)

    if settings.app_env == "development":
        print()
        print("=" * 70)
        print("CAREERPILOT DEVELOPMENT EMAIL")
        print(f"To: {email}")
        print("Subject: Reset your CareerPilot AI password")
        print(f"Password Reset URL: {reset_url}")
        print("=" * 70)
        print()
        return

    # Production email provider will be connected later.
    raise RuntimeError(
        "Production email provider is not configured."
    )