from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

from app.api.v1.router import api_v1_router
from app.config import settings
from app.database import Base, engine


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **_kw):
    return "JSON"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    asyncio.create_task(_seed_on_startup())
    yield


async def _seed_on_startup():
    from app.database import async_session
    from app.models.church import Church, Branch
    from app.models.user import Role, User
    from app.auth import hash_password
    from sqlalchemy import select

    async with async_session() as db:
        existing = (await db.execute(select(User).where(User.email == "pastor@potters.org"))).scalar_one_or_none()
        if existing and existing.hashed_password:
            return

        church = Church(id=1, name="Potter Tabernacle Ministry")
        db.add(church)
        await db.flush()
        branch = Branch(id=1, church_id=1, name="Main Branch")
        db.add(branch)
        await db.flush()
        role = Role(id=1, name="Admin", description="Full access")
        db.add(role)
        await db.flush()
        user = User(
            id=1, church_id=1, branch_id=1, role_id=1,
            name="Pastor Yinka", email="pastor@potters.org",
            phone="+2347065510101", active=True,
            hashed_password=hash_password("admin123"),
        )
        db.add(user)
        await db.commit()
        print("Database tables created and demo user seeded")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
