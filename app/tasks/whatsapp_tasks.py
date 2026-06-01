import httpx

from app.celery import celery_app
from app.config import settings


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_whatsapp_message(self, queue_item_id: int, contact_phone: str, body: str):
    url = f"{settings.WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": contact_phone,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            external_id = data.get("messages", [{}])[0].get("id")
            return {
                "queue_item_id": queue_item_id,
                "success": True,
                "external_message_id": external_id,
                "status_code": response.status_code,
            }
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text[:500] if e.response else str(e)
        raise self.retry(exc=e, countdown=settings.WHATSAPP_RETRY_DELAY_SECONDS)
    except httpx.RequestError as e:
        error_detail = str(e)[:500]
        raise self.retry(exc=e, countdown=settings.WHATSAPP_RETRY_DELAY_SECONDS)


@celery_app.task
def process_whatsapp_queue(limit: int = 10):
    return {"processed": 0, "detail": "Queue processing delegated to async worker context"}
