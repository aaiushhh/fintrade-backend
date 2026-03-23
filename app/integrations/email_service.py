"""Email service stub — ready for SMTP integration."""

from typing import Optional

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
) -> bool:
    """Send an email via SMTP.

    Currently a stub that logs the email. Replace with real SMTP
    integration (e.g. aiosmtplib) for production.
    """
    logger.info(
        "email_sent",
        to=to_email,
        subject=subject,
        smtp_host=settings.SMTP_HOST,
    )

    # ── Production implementation would look like: ──
    # import aiosmtplib
    # from email.mime.text import MIMEText
    # from email.mime.multipart import MIMEMultipart
    #
    # msg = MIMEMultipart("alternative")
    # msg["Subject"] = subject
    # msg["From"] = settings.EMAIL_FROM
    # msg["To"] = to_email
    # msg.attach(MIMEText(body, "plain"))
    # if html_body:
    #     msg.attach(MIMEText(html_body, "html"))
    #
    # await aiosmtplib.send(
    #     msg,
    #     hostname=settings.SMTP_HOST,
    #     port=settings.SMTP_PORT,
    #     username=settings.SMTP_USER,
    #     password=settings.SMTP_PASSWORD,
    #     use_tls=True,
    # )

    return True


async def send_welcome_email(to_email: str, full_name: str) -> bool:
    """Send a welcome email after registration."""
    return await send_email(
        to_email=to_email,
        subject=f"Welcome to {settings.APP_NAME}!",
        body=f"Hi {full_name},\n\nWelcome to {settings.APP_NAME}! Your account is ready.\n\nBest,\nThe Team",
    )


async def send_exam_result_email(to_email: str, full_name: str, passed: bool, percentage: float) -> bool:
    """Notify student about exam result."""
    status_text = "Passed ✅" if passed else "Failed ❌"
    return await send_email(
        to_email=to_email,
        subject=f"Entrance Exam Result — {status_text}",
        body=(
            f"Hi {full_name},\n\n"
            f"Your entrance exam result: {status_text}\n"
            f"Score: {percentage:.1f}%\n\n"
            f"{'Congratulations! You can now enroll in the course.' if passed else 'You may reattempt after 30 days.'}\n\n"
            f"Best,\nThe {settings.APP_NAME} Team"
        ),
    )
