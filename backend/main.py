from collections import defaultdict, deque
import hashlib
import hmac
import secrets
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend import crud
from backend.config import settings
from backend.database import SessionLocal, init_db
from backend.routers import admin, cart, catalog, coupons, discord_integration, feedback, orders, profile
from backend.services.catalog import seed_catalog


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="Cloudverse Store")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.state.templates = templates

DISCORD_API_BASE = "https://discord.com/api"
DISCORD_AUTH_URL = f"{DISCORD_API_BASE}/oauth2/authorize"
DISCORD_TOKEN_URL = f"{DISCORD_API_BASE}/oauth2/token"
DISCORD_USER_URL = f"{DISCORD_API_BASE}/users/@me"
SESSION_COOKIE = "cloudverse_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7

sessions: dict[str, dict[str, Any]] = {}
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 180
_rate_limit_hits: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def basic_protection_middleware(request: Request, call_next):
    now = time.time()
    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "unknown")
    hits = _rate_limit_hits[client_ip]
    while hits and now - hits[0] > RATE_LIMIT_WINDOW_SECONDS:
        hits.popleft()
    hits.append(now)
    if len(hits) > RATE_LIMIT_MAX_REQUESTS:
        return JSONResponse({"detail": "Too many requests. Please try again soon."}, status_code=429)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


def discord_redirect_uri() -> str:
    return settings.discord_redirect_uri or ""


def auth_config_error(missing: list[str]) -> HTMLResponse:
    missing_items = "".join(f"<li><code>{name}</code></li>" for name in missing)
    return HTMLResponse(
        f"""
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>Cloudverse Auth Setup Needed</title>
          <style>
            body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #050711; color: #f3f6ff; font-family: system-ui, sans-serif; }}
            main {{ max-width: 680px; padding: 32px; border: 1px solid rgba(72,215,255,.28); border-radius: 18px; background: rgba(14,18,32,.92); box-shadow: 0 24px 80px rgba(0,0,0,.34); }}
            h1 {{ margin-top: 0; }}
            code {{ color: #48d7ff; }}
            a {{ color: #35f2ba; }}
          </style>
        </head>
        <body>
          <main>
            <h1>Discord login is not configured yet</h1>
            <p>Add these missing values to your <code>.env</code> file, then restart FastAPI:</p>
            <ul>{missing_items}</ul>
            <p>Use <code>.env.example</code> as the template. No secrets are sent to the browser.</p>
            <p><a href="/">Back to store</a></p>
          </main>
        </body>
        </html>
        """,
        status_code=500,
    )


def sign_session_id(session_id: str) -> str:
    secret = settings.session_secret or ""
    signature = hmac.new(secret.encode("utf-8"), session_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{session_id}.{signature}"


def read_session_id(request: Request) -> str | None:
    cookie_value = request.cookies.get(SESSION_COOKIE)
    if not cookie_value or "." not in cookie_value or not settings.session_secret:
        return None
    session_id, signature = cookie_value.rsplit(".", 1)
    expected = sign_session_id(session_id).rsplit(".", 1)[1]
    if not hmac.compare_digest(signature, expected):
        return None
    return session_id


def discord_avatar_url(user: dict[str, Any]) -> str:
    user_id = str(user.get("id", "0"))
    avatar = user.get("avatar")
    if avatar:
        extension = "gif" if str(avatar).startswith("a_") else "png"
        return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.{extension}?size=128"
    default_index = (int(user_id) >> 22) % 6 if user_id.isdigit() else 0
    return f"https://cdn.discordapp.com/embed/avatars/{default_index}.png"


def get_or_create_session(request: Request) -> tuple[str, dict[str, Any], bool]:
    session_id = read_session_id(request)
    session = sessions.get(session_id or "")
    if session:
        session["last_seen"] = time.time()
        return str(session_id), session, False

    session_id = secrets.token_urlsafe(32)
    session = {"created_at": time.time(), "last_seen": time.time()}
    sessions[session_id] = session
    return session_id, session, True


def set_session_cookie(response, session_id: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        sign_session_id(session_id),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def current_user(request: Request) -> dict[str, Any] | None:
    session_id = read_session_id(request)
    session = sessions.get(session_id or "")
    if not session:
        return None
    session["last_seen"] = time.time()
    return session.get("user")


app.state.current_user = current_user


@app.on_event("startup")
def startup() -> None:
    init_db()
    with SessionLocal() as db:
        seed_catalog(db)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


@app.get("/login")
async def login(request: Request):
    missing = settings.missing_auth_values
    if missing:
        return auth_config_error(missing)

    session_id, session, _ = get_or_create_session(request)
    state = secrets.token_urlsafe(24)
    session["oauth_state"] = state

    params = {
        "client_id": settings.discord_client_id,
        "redirect_uri": discord_redirect_uri(),
        "response_type": "code",
        "scope": "identify",
        "state": state,
        "prompt": "none",
    }
    response = RedirectResponse(f"{DISCORD_AUTH_URL}?{urlencode(params)}")
    set_session_cookie(response, session_id)
    return response


@app.get("/auth/callback", name="auth_callback")
async def auth_callback(request: Request, code: str | None = None, state: str | None = None):
    missing = settings.missing_auth_values
    if missing:
        return auth_config_error(missing)
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing Discord OAuth callback parameters.")

    session_id = read_session_id(request)
    session = sessions.get(session_id or "")
    if not session or not secrets.compare_digest(str(session.get("oauth_state", "")), state):
        raise HTTPException(status_code=400, detail="Invalid Discord OAuth state.")

    token_payload = {
        "client_id": settings.discord_client_id,
        "client_secret": settings.discord_client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": discord_redirect_uri(),
    }
    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post(
            DISCORD_TOKEN_URL,
            data=token_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_response.status_code >= 400:
            raise HTTPException(status_code=400, detail="Discord login failed while requesting token.")

        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Discord did not return an access token.")

        user_response = await client.get(DISCORD_USER_URL, headers={"Authorization": f"Bearer {access_token}"})
        if user_response.status_code >= 400:
            raise HTTPException(status_code=400, detail="Discord login failed while fetching user.")

    discord_user = user_response.json()
    avatar_url = discord_avatar_url(discord_user)
    with SessionLocal() as db:
        crud.upsert_discord_user(db, discord_user, avatar_url)

    session.pop("oauth_state", None)
    session["user"] = {
        "id": discord_user.get("id"),
        "username": discord_user.get("global_name") or discord_user.get("username"),
        "discord_username": discord_user.get("username"),
        "avatar": avatar_url,
    }

    response = RedirectResponse("/")
    set_session_cookie(response, str(session_id))
    return response


@app.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    session_id = read_session_id(request)
    if session_id:
        sessions.pop(session_id, None)
    response = RedirectResponse("/")
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.get("/api/user")
async def api_user(request: Request) -> JSONResponse:
    user = current_user(request)
    if user and user.get("id"):
        db = SessionLocal()
        try:
            db_user = crud.get_user_by_discord_id(db, str(user["id"]))
            user = {**user, "is_admin": bool(db_user and db_user.is_admin)}
        finally:
            db.close()
    return JSONResponse({"authenticated": bool(user), "user": user})


app.include_router(catalog.router)
app.include_router(cart.router)
app.include_router(coupons.router)
app.include_router(orders.router)
app.include_router(admin.router)
app.include_router(discord_integration.router)
app.include_router(profile.router)
app.include_router(feedback.router)


