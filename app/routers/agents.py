import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models import AgentRole, TenantAgent
from security import require_session
from avatars import generate_avatar_svg

router = APIRouter()


class HirePayload(BaseModel):
    role_slug: str
    custom_name: Optional[str] = None


@router.get("/mine")
async def my_agents(request: Request, db: AsyncSession = Depends(get_db)):
    session = require_session(request)
    r = await db.execute(select(TenantAgent).where(TenantAgent.tenant_id == session["tid"]))
    tenant_agents = r.scalars().all()

    result = []
    for ta in tenant_agents:
        role_r = await db.execute(select(AgentRole).where(AgentRole.id == ta.agent_role_id))
        role = role_r.scalar_one_or_none()
        if not role:
            continue
        result.append({
            "id": str(ta.id),
            "custom_name": ta.custom_name,
            "role_slug": role.slug,
            "role_name": role.name,
            "color_accent": role.color_accent,
            "avatar_svg": generate_avatar_svg(ta.avatar_seed, role.color_accent),
            "hired_at": ta.hired_at.isoformat() if ta.hired_at else None,
        })
    return result


@router.post("/hire")
async def hire_agent(payload: HirePayload, request: Request, db: AsyncSession = Depends(get_db)):
    session = require_session(request)
    r = await db.execute(select(AgentRole).where(AgentRole.slug == payload.role_slug))
    role = r.scalar_one_or_none()
    if not role:
        raise HTTPException(404, "Rolle nicht gefunden.")

    avatar_seed = secrets.token_hex(8)
    tenant_agent = TenantAgent(
        tenant_id=session["tid"],
        agent_role_id=role.id,
        custom_name=payload.custom_name or role.name,
        avatar_seed=avatar_seed,
    )
    db.add(tenant_agent)
    await db.commit()
    await db.refresh(tenant_agent)

    return {
        "id": str(tenant_agent.id),
        "custom_name": tenant_agent.custom_name,
        "role_slug": role.slug,
        "role_name": role.name,
        "avatar_svg": generate_avatar_svg(avatar_seed, role.color_accent),
    }
