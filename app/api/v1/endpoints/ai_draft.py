from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contact import Contact
from app.models.whatsapp import WhatsAppMessage
from app.schemas.ai_draft import (
    AIDraftBatchRequest,
    AIDraftBatchResponse,
    AIDraftGenerateResponse,
    AIDraftRequest,
    AIDraftResponse,
)
from app.services.ai_draft import AIDraftService

router = APIRouter(prefix="/ai-draft", tags=["ai-draft"])


async def _get_contact_info(db: AsyncSession, contact_id: int) -> tuple[str | None, str | None]:
    stmt = select(Contact.first_name, Contact.last_name, Contact.phone).where(Contact.id == contact_id)
    result = await db.execute(stmt)
    row = result.one_or_none()
    if row is None:
        return None, None
    contact_name = f"{row[0]} {row[1]}"
    contact_phone = row[2]
    return contact_name, contact_phone


@router.post("/generate", response_model=AIDraftGenerateResponse)
async def generate_ai_draft(
    data: AIDraftRequest,
    church_id: int = Query(..., description="Church ID"),
    user_id: int = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    ai_service = AIDraftService(db)
    try:
        body, fallback_used, template_name, template_id, token_count = await ai_service.generate_draft(
            contact_id=data.contact_id,
            category=data.category,
            channel=data.channel,
            branch_id=data.branch_id,
            church_id=church_id,
            tone=data.tone,
            additional_context=data.additional_context,
            override_prompt=data.override_prompt,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    contact_name, contact_phone = await _get_contact_info(db, data.contact_id)

    message = WhatsAppMessage(
        church_id=church_id,
        branch_id=data.branch_id,
        contact_id=data.contact_id,
        template_id=template_id,
        body=body,
        status="draft",
        priority="normal",
        created_by=user_id,
    )
    db.add(message)
    await db.flush()
    await db.refresh(message)

    source = "template" if fallback_used else "ai"
    source_label = "Template Fallback" if fallback_used else "AI Generated"

    return AIDraftGenerateResponse(
        success=True,
        draft=AIDraftResponse(
            id=message.id,
            contact_id=message.contact_id,
            body=message.body,
            status=message.status,
            source=source,
            source_label=source_label,
            template_used=template_name,
            template_id=template_id,
            token_count=token_count,
            contact_name=contact_name,
            contact_phone=contact_phone,
            category=data.category,
            created_at=message.created_at.isoformat(),
        ),
        source=source,
        message=f"Draft created via {source_label.lower()}",
        fallback_used=fallback_used,
    )


@router.post("/batch", response_model=AIDraftBatchResponse)
async def generate_ai_drafts_batch(
    data: AIDraftBatchRequest,
    church_id: int = Query(..., description="Church ID"),
    user_id: int = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    ai_service = AIDraftService(db)
    results = []
    success_count = 0
    failed_count = 0
    skipped_count = 0

    for contact_id in data.contact_ids:
        try:
            body, fallback_used, template_name, template_id, token_count = await ai_service.generate_draft(
                contact_id=contact_id,
                category=data.category,
                channel=data.channel,
                branch_id=data.branch_id,
                church_id=church_id,
                tone=data.tone,
                additional_context=data.additional_context,
            )

            contact_name, contact_phone = await _get_contact_info(db, contact_id)

            message = WhatsAppMessage(
                church_id=church_id,
                branch_id=data.branch_id,
                contact_id=contact_id,
                template_id=template_id,
                body=body,
                status="draft",
                priority="normal",
                created_by=user_id,
            )
            db.add(message)
            await db.flush()
            await db.refresh(message)

            source = "template" if fallback_used else "ai"
            source_label = "Template Fallback" if fallback_used else "AI Generated"

            results.append(AIDraftGenerateResponse(
                success=True,
                draft=AIDraftResponse(
                    id=message.id,
                    contact_id=message.contact_id,
                    body=message.body,
                    status=message.status,
                    source=source,
                    source_label=source_label,
                    template_used=template_name,
                    template_id=template_id,
                    token_count=token_count,
                    contact_name=contact_name,
                    contact_phone=contact_phone,
                    category=data.category,
                    created_at=message.created_at.isoformat(),
                ),
                source=source,
                message=f"Draft created via {source_label.lower()}",
                fallback_used=fallback_used,
            ))
            success_count += 1
        except (ValueError, RuntimeError) as exc:
            results.append(AIDraftGenerateResponse(
                success=False,
                source="error",
                message=str(exc),
            ))
            failed_count += 1

    return AIDraftBatchResponse(
        success=success_count,
        failed=failed_count,
        skipped=skipped_count,
        results=results,
    )
