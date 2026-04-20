import logging
from typing import Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

async def send_whatsapp_message(to_phone: str, template_name: str, template_data: Dict[str, Any] = None) -> bool:
    """
    Stub for sending WhatsApp Template Messages via Meta/Twilio API.
    Used for student reminders (e.g. class starting, assignment due).
    
    Args:
        to_phone: The recipient's phone number with country code.
        template_name: The registered WhatsApp template name.
        template_data: Dynamic parameters for the template.
    """
    if not settings.WHATSAPP_API_TOKEN:
        logger.warning(f"[WhatsApp Stub] API Token not configured. Simulated sending '{template_name}' to {to_phone}")
        return False
        
    # TODO: Implement HTTP POST to Meta Graph API or Twilio API
    # headers = { "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}" }
    logger.info(f"[WhatsApp] Sending {template_name} to {to_phone}")
    return True

async def send_reminder_for_lecture(student_phone: str, lecture_title: str, time_str: str) -> bool:
    """Convenience function to dispatch a lecture reminder."""
    return await send_whatsapp_message(
        to_phone=student_phone,
        template_name="lecture_reminder",
        template_data={"title": lecture_title, "time": time_str}
    )
