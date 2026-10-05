import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from database import engine, Base, AsyncSessionLocal
from models import AgentRole
from seed_data import AGENT_ROLES
from routers import auth, catalog, agents, chat, pages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kollevio")


async def seed_agent_roles():
    async with AsyncSessionLocal() as db:
        for role_data in AGENT_ROLES:
            r = await db.execute(select(AgentRole).where(AgentRole.slug == role_data["slug"]))
            existing = r.scalar_one_or_none()
            if existing:
                existing.name = role_data["name"]
                existing.tagline = role_data["tagline"]
                existing.description = role_data["description"]
                existing.system_prompt = role_data["system_prompt"]
                existing.color_accent = role_data["color_accent"]
            else:
                db.add(AgentRole(**role_data))
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_agent_roles()
    logger.info("kollevio backend started, agent roles seeded")
    yield


app = FastAPI(title="kollevio", version="1.0.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages.router, tags=["Pages"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(catalog.router, prefix="/api/catalog", tags=["Catalog"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "kollevio", "version": "1.0.0"}
