import re
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import BaseModel, EmailStr

from database import get_db
from models import Tenant, User
from security import hash_password, verify_password, make_token, COOKIE_NAME

router = APIRouter()

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_\-.]{3,50}$")


class RegisterPayload(BaseModel):
    company_name: str
    name: str
    email: EmailStr
    username: str
    password: str


class LoginPayload(BaseModel):
    identifier: str  # email or username
    password: str


def _set_cookie(response: Response, token: str):
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 30,
        path="/",
    )


@router.post("/register")
async def register(payload: RegisterPayload, response: Response, db: AsyncSession = Depends(get_db)):
    if len(payload.password) < 8:
        raise HTTPException(400, "Passwort muss mindestens 8 Zeichen haben.")
    if not USERNAME_RE.match(payload.username):
        raise HTTPException(400, "Benutzername ungültig (3-50 Zeichen, Buchstaben/Zahlen/_-.).")
    if not payload.company_name.strip():
        raise HTTPException(400, "Firmenname darf nicht leer sein.")

    r = await db.execute(
        select(User).where(or_(User.email == payload.email.lower(), User.username == payload.username))
    )
    if r.scalar_one_or_none():
        raise HTTPException(400, "E-Mail oder Benutzername bereits vergeben.")

    tenant = Tenant(company_name=payload.company_name.strip())
    db.add(tenant)
    await db.flush()

    user = User(
        tenant_id=tenant.id,
        name=payload.name.strip(),
        email=payload.email.lower(),
        username=payload.username,
        password_hash=hash_password(payload.password),
        role="owner",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = make_token(str(user.id), str(tenant.id), user.email, user.role)
    _set_cookie(response, token)
    return {"ok": True, "redirect": "/dashboard"}


@router.post("/login")
async def login(payload: LoginPayload, response: Response, db: AsyncSession = Depends(get_db)):
    ident = payload.identifier.strip().lower()
    r = await db.execute(select(User).where(or_(User.email == ident, User.username == payload.identifier.strip())))
    user = r.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Anmeldedaten ungültig.")

    token = make_token(str(user.id), str(user.tenant_id), user.email, user.role)
    _set_cookie(response, token)
    return {"ok": True, "redirect": "/dashboard"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True, "redirect": "/"}
