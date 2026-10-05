from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import AgentRole

router = APIRouter()


@router.get("/roles")
async def list_roles(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(AgentRole).order_by(AgentRole.created_at))
    roles = r.scalars().all()
    return [
        {
            "id": str(role.id),
            "slug": role.slug,
            "name": role.name,
            "tagline": role.tagline,
            "description": role.description,
            "color_accent": role.color_accent,
        }
        for role in roles
    ]
