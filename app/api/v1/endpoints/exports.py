from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.export import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])


def _response(content: bytes, filename: str, media_type: str) -> StreamingResponse:
    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/contacts")
async def export_contacts(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    category: str | None = Query(None, description="Contact category filter"),
    format: str = Query("csv", description="Export format: csv, xlsx, pdf"),
):
    service = ExportService(db)
    rows = await service.export_contacts(church_id, category)
    label = category or "contacts"
    now = __import__("datetime").datetime.now().strftime("%Y%m%d")

    if format == "csv":
        buf = service.to_csv(rows)
        return _response(buf.getvalue(), f"{label}_{now}.csv", "text/csv")
    elif format == "xlsx":
        buf = service.to_excel(rows, label.replace("_", " ").title())
        return _response(buf.getvalue(), f"{label}_{now}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    elif format == "pdf":
        buf = service.to_pdf(rows, f"{label.replace('_', ' ').title()} Report")
        return _response(buf.getvalue(), f"{label}_{now}.pdf", "application/pdf")
    else:
        buf = service.to_csv(rows)
        return _response(buf.getvalue(), f"{label}_{now}.csv", "text/csv")


@router.get("/follow-ups")
async def export_follow_ups(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    format: str = Query("csv", description="Export format: csv, xlsx, pdf"),
):
    service = ExportService(db)
    rows = await service.export_follow_ups(church_id)
    now = __import__("datetime").datetime.now().strftime("%Y%m%d")

    if format == "csv":
        buf = service.to_csv(rows)
        return _response(buf.getvalue(), f"follow_ups_{now}.csv", "text/csv")
    elif format == "xlsx":
        buf = service.to_excel(rows, "Follow-Ups")
        return _response(buf.getvalue(), f"follow_ups_{now}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    elif format == "pdf":
        buf = service.to_pdf(rows, "Follow-Ups Report")
        return _response(buf.getvalue(), f"follow_ups_{now}.pdf", "application/pdf")
    else:
        buf = service.to_csv(rows)
        return _response(buf.getvalue(), f"follow_ups_{now}.csv", "text/csv")


@router.get("/communication-logs")
async def export_communication_logs(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    format: str = Query("csv", description="Export format: csv, xlsx, pdf"),
):
    service = ExportService(db)
    rows = await service.export_communication_logs(church_id)
    now = __import__("datetime").datetime.now().strftime("%Y%m%d")

    if format == "csv":
        buf = service.to_csv(rows)
        return _response(buf.getvalue(), f"comm_logs_{now}.csv", "text/csv")
    elif format == "xlsx":
        buf = service.to_excel(rows, "Communication Logs")
        return _response(buf.getvalue(), f"comm_logs_{now}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    elif format == "pdf":
        buf = service.to_pdf(rows, "Communication Logs Report")
        return _response(buf.getvalue(), f"comm_logs_{now}.pdf", "application/pdf")
    else:
        buf = service.to_csv(rows)
        return _response(buf.getvalue(), f"comm_logs_{now}.csv", "text/csv")
