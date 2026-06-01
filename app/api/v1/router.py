from fastapi import APIRouter

from app.api.v1.endpoints.ai_draft import router as ai_draft_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.communication_logs import router as comm_logs_router
from app.api.v1.endpoints.contacts import router as contacts_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.exports import router as exports_router
from app.api.v1.endpoints.follow_up import router as follow_up_router
from app.api.v1.endpoints.foundation_class import router as foundation_class_router
from app.api.v1.endpoints.journey import router as journey_router
from app.api.v1.endpoints.message_templates import router as templates_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.service_units import router as service_units_router
from app.api.v1.endpoints.whatsapp import router as whatsapp_router
from app.api.v1.endpoints.workflows import router as workflows_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(contacts_router)
api_v1_router.include_router(service_units_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(follow_up_router)
api_v1_router.include_router(foundation_class_router)
api_v1_router.include_router(exports_router)
api_v1_router.include_router(journey_router)
api_v1_router.include_router(templates_router)
api_v1_router.include_router(workflows_router)
api_v1_router.include_router(whatsapp_router)
api_v1_router.include_router(ai_draft_router)
api_v1_router.include_router(comm_logs_router)


@api_v1_router.get("/")
async def v1_root():
    return {"message": "ChurchFlow AI API v1"}
