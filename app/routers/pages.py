from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import AgentRole, User, Tenant
from security import get_current_session
from avatars import generate_avatar_svg

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _roles_with_preview(roles):
    return [
        {"role": role, "preview_svg": generate_avatar_svg(f"preview-{role.slug}", role.color_accent)}
        for role in roles
    ]


@router.get("/")
async def landing(request: Request, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(AgentRole).order_by(AgentRole.created_at))
    roles = r.scalars().all()
    return templates.TemplateResponse(request, "landing.html", {"roles": _roles_with_preview(roles)})


@router.get("/register")
async def register_page(request: Request):
    if get_current_session(request):
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse(request, "register.html", {})


@router.get("/login")
async def login_page(request: Request):
    if get_current_session(request):
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse(request, "login.html", {})


@router.get("/dashboard")
async def dashboard_page(request: Request, db: AsyncSession = Depends(get_db)):
    session = get_current_session(request)
    if not session:
        return RedirectResponse("/login")

    user_r = await db.execute(select(User).where(User.id == session["uid"]))
    user = user_r.scalar_one_or_none()
    tenant_r = await db.execute(select(Tenant).where(Tenant.id == session["tid"]))
    tenant = tenant_r.scalar_one_or_none()

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"user": user, "tenant": tenant},
    )


@router.get("/katalog")
async def catalog_page(request: Request, db: AsyncSession = Depends(get_db)):
    session = get_current_session(request)
    if not session:
        return RedirectResponse("/login")
    r = await db.execute(select(AgentRole).order_by(AgentRole.created_at))
    roles = r.scalars().all()
    return templates.TemplateResponse(request, "catalog.html", {"roles": _roles_with_preview(roles)})


@router.get("/chat/{tenant_agent_id}")
async def chat_page(tenant_agent_id: str, request: Request):
    session = get_current_session(request)
    if not session:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "chat.html", {"tenant_agent_id": tenant_agent_id})


@router.get("/impressum")
async def impressum_page(request: Request):
    return templates.TemplateResponse(request, "impressum.html", {})


@router.get("/agb")
async def agb_page(request: Request):
    return templates.TemplateResponse(request, "agb.html", {})
