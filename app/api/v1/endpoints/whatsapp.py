from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.whatsapp import (
    WhatsAppApprovalAction,
    WhatsAppDeliveryLogListResponse,
    WhatsAppMessageCreate,
    WhatsAppMessageFilter,
    WhatsAppMessageListResponse,
    WhatsAppMessageResponse,
    WhatsAppMessageUpdate,
    WhatsAppOptOutCreate,
    WhatsAppOptOutFilter,
    WhatsAppOptOutListResponse,
    WhatsAppOptOutResponse,
    WhatsAppQueueStatusResponse,
    WhatsAppWebhookPayload,
)
from app.services.whatsapp_message import WhatsAppMessageService
from app.services.whatsapp_opt_out import WhatsAppOptOutService
from app.services.whatsapp_queue import WhatsAppQueueService
from app.services.whatsapp_webhook import WhatsAppWebhookService

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.post("/draft", response_model=WhatsAppMessageResponse, status_code=201)
async def create_draft(
    data: WhatsAppMessageCreate,
    church_id: int = Query(..., description="Church ID"),
    user_id: int = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    service = WhatsAppMessageService(db)
    try:
        message = await service.create_draft(data, church_id, user_id)
        return service._to_response(message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{message_id}/submit", response_model=WhatsAppMessageResponse)
async def submit_for_approval(
    message_id: int,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = WhatsAppMessageService(db)
    try:
        message = await service.submit_for_approval(message_id, church_id)
        if message is None:
            raise HTTPException(status_code=404, detail="Message not found")
        return service._to_response(message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{message_id}/approve", response_model=WhatsAppMessageResponse)
async def approve_message(
    message_id: int,
    data: WhatsAppApprovalAction,
    church_id: int = Query(..., description="Church ID"),
    user_id: int = Query(..., description="Approver user ID"),
    db: AsyncSession = Depends(get_db),
):
    service = WhatsAppMessageService(db)
    try:
        message = await service.approve(message_id, data, church_id, user_id)
        if message is None:
            raise HTTPException(status_code=404, detail="Message not found")
        return service._to_response(message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{message_id}/enqueue", response_model=WhatsAppMessageResponse)
async def enqueue_message(
    message_id: int,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = WhatsAppMessageService(db)
    try:
        result = await service.enqueue(message_id, church_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Message not found")
        message, queue_item = result
        from app.tasks.whatsapp_tasks import send_whatsapp_message

        contact_phone = None
        if message.contact:
            contact_phone = message.contact.phone
        if contact_phone:
            send_whatsapp_message.delay(
                queue_item_id=queue_item.id,
                contact_phone=contact_phone,
                body=message.body,
            )
        return service._to_response(message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/messages", response_model=WhatsAppMessageListResponse)
async def list_messages(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    contact_id: int | None = Query(None),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    template_id: int | None = Query(None),
    created_by: int | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = WhatsAppMessageFilter(
        contact_id=contact_id,
        status=status,
        priority=priority,
        template_id=template_id,
        created_by=created_by,
        search=search,
        page=page,
        page_size=page_size,
    )
    service = WhatsAppMessageService(db)
    messages, total = await service.get_messages(church_id, filters)
    return WhatsAppMessageListResponse(
        items=[service._to_response(m) for m in messages],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/messages/{message_id}", response_model=WhatsAppMessageResponse)
async def get_message(
    message_id: int,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = WhatsAppMessageService(db)
    message = await service.get_message(message_id, church_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return service._to_response(message)


@router.put("/messages/{message_id}", response_model=WhatsAppMessageResponse)
async def update_message(
    message_id: int,
    data: WhatsAppMessageUpdate,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = WhatsAppMessageService(db)
    try:
        message = await service.update_message(message_id, data, church_id)
        if message is None:
            raise HTTPException(status_code=404, detail="Message not found")
        return service._to_response(message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/webhook", include_in_schema=False)
async def verify_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if not mode or not token or not challenge:
        raise HTTPException(status_code=400, detail="Missing parameters")

    service = WhatsAppWebhookService(db)
    result = await service.verify_token(mode, token, challenge)
    if result is None:
        raise HTTPException(status_code=403, detail="Verification failed")
    return int(result)


@router.post("/webhook", include_in_schema=False)
async def receive_webhook(
    payload: WhatsAppWebhookPayload,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    service = WhatsAppWebhookService(db)
    if payload.object and payload.entry:
        body = await request.json()
        results = await service.process_webhook(body)
        return {"status": "processed", **results}

    raw_body = await request.body()
    import json
    try:
        body = json.loads(raw_body)
        results = await service.process_webhook(body)
        return {"status": "processed", **results}
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid payload")


@router.get("/delivery/{message_id}", response_model=WhatsAppDeliveryLogListResponse)
async def get_delivery_logs(
    message_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = WhatsAppWebhookService(db)
    items, total = await service.get_delivery_logs(message_id)
    return service._to_delivery_list_response(items, total)


@router.get("/queue/status", response_model=WhatsAppQueueStatusResponse)
async def get_queue_status(
    db: AsyncSession = Depends(get_db),
):
    service = WhatsAppQueueService(db)
    return await service.get_queue_status()


@router.post("/opt-out", response_model=WhatsAppOptOutResponse, status_code=201)
async def record_opt_out(
    data: WhatsAppOptOutCreate,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = WhatsAppOptOutService(db)
    opt_out = await service.record_opt_out(data, church_id)
    return service._to_response(opt_out)


@router.get("/opt-outs", response_model=WhatsAppOptOutListResponse)
async def list_opt_outs(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    phone_number: str | None = Query(None),
    contact_id: int | None = Query(None),
    source: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = WhatsAppOptOutFilter(
        phone_number=phone_number,
        contact_id=contact_id,
        source=source,
        page=page,
        page_size=page_size,
    )
    service = WhatsAppOptOutService(db)
    items, total = await service.get_opt_outs(church_id, filters)
    return WhatsAppOptOutListResponse(
        items=[service._to_response(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )
