from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from database import get_db
from models import TenantAgent, AgentRole, AgentConversation, AgentMessage
from security import require_session
from llm import get_agent_reply

router = APIRouter()


class ChatPayload(BaseModel):
    message: str


async def _get_owned_tenant_agent(db: AsyncSession, tenant_agent_id: str, tenant_id: str):
    r = await db.execute(select(TenantAgent).where(TenantAgent.id == tenant_agent_id))
    ta = r.scalar_one_or_none()
    if not ta or str(ta.tenant_id) != str(tenant_id):
        raise HTTPException(404, "Mitarbeiter nicht gefunden.")
    return ta


async def _get_or_create_conversation(db: AsyncSession, tenant_agent_id: str) -> AgentConversation:
    r = await db.execute(
        select(AgentConversation)
        .where(AgentConversation.tenant_agent_id == tenant_agent_id)
        .order_by(AgentConversation.created_at.desc())
    )
    conv = r.scalars().first()
    if conv:
        return conv
    conv = AgentConversation(tenant_agent_id=tenant_agent_id)
    db.add(conv)
    await db.flush()
    return conv


@router.get("/{tenant_agent_id}/history")
async def history(tenant_agent_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    session = require_session(request)
    ta = await _get_owned_tenant_agent(db, tenant_agent_id, session["tid"])
    conv = await _get_or_create_conversation(db, ta.id)
    await db.commit()

    r = await db.execute(
        select(AgentMessage).where(AgentMessage.conversation_id == conv.id).order_by(AgentMessage.created_at)
    )
    messages = r.scalars().all()
    return [
        {"sender": m.sender, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in messages
    ]


@router.post("/{tenant_agent_id}/message")
async def send_message(tenant_agent_id: str, payload: ChatPayload, request: Request, db: AsyncSession = Depends(get_db)):
    session = require_session(request)
    if not payload.message.strip():
        raise HTTPException(400, "Nachricht darf nicht leer sein.")

    ta = await _get_owned_tenant_agent(db, tenant_agent_id, session["tid"])
    role_r = await db.execute(select(AgentRole).where(AgentRole.id == ta.agent_role_id))
    role = role_r.scalar_one_or_none()
    if not role:
        raise HTTPException(404, "Rolle nicht gefunden.")

    conv = await _get_or_create_conversation(db, ta.id)

    user_msg = AgentMessage(conversation_id=conv.id, sender="user", content=payload.message.strip())
    db.add(user_msg)
    await db.flush()

    hist_r = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.conversation_id == conv.id)
        .order_by(AgentMessage.created_at)
    )
    history_rows = hist_r.scalars().all()
    history = [{"sender": m.sender, "content": m.content} for m in history_rows[:-1]][-20:]

    reply_text = await get_agent_reply(role.system_prompt, history, payload.message.strip())

    agent_msg = AgentMessage(conversation_id=conv.id, sender="agent", content=reply_text)
    db.add(agent_msg)
    await db.commit()

    return {
        "reply": reply_text,
        "created_at": agent_msg.created_at.isoformat() if agent_msg.created_at else None,
    }
