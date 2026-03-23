"""Notification service stub — ready for push notification / webhook integration."""

from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


async def send_notification(
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    channel: str = "in_app",
) -> bool:
    """Send a notification to a user.

    Channels: in_app, push, sms
    Types: info, warning, success, error

    Currently a stub that logs the notification.
    Replace with Firebase Cloud Messaging, OneSignal, or similar for production.
    """
    logger.info(
        "notification_sent",
        user_id=user_id,
        title=title,
        type=notification_type,
        channel=channel,
    )
    return True


async def notify_exam_result(user_id: int, passed: bool, percentage: float) -> bool:
    """Send exam result notification."""
    status = "passed" if passed else "failed"
    return await send_notification(
        user_id=user_id,
        title=f"Exam Result: {status.title()}",
        message=f"You {status} with {percentage:.1f}%. "
        + ("You can now enroll!" if passed else "Retry after 30 days."),
        notification_type="success" if passed else "warning",
    )


async def notify_lecture_reminder(user_id: int, lecture_title: str, minutes_before: int = 15) -> bool:
    """Send a lecture reminder notification."""
    return await send_notification(
        user_id=user_id,
        title="Lecture Reminder",
        message=f"'{lecture_title}' starts in {minutes_before} minutes.",
        notification_type="info",
    )
