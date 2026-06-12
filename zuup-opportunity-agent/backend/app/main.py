"""
Zuup Opportunity Agent — FastAPI Application Entry Point.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api import auth, resume, profile, opportunities, applications, notifications
from app.core.rate_limit import RateLimitMiddleware

# ── App Instance ─────────────────────────────────────────────

app = FastAPI(
    title="Zuup Opportunity Agent API",
    description="Autonomous AI-powered opportunity discovery for students.",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# ── CORS ─────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

# ── Routes ───────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(profile.router)
app.include_router(opportunities.router)
app.include_router(applications.router)
app.include_router(notifications.router)

# ── Health Check ─────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "version": "1.0.0", "env": settings.app_env}


# ── Global Exception Handler ─────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred.", "code": "internal_error"},
    )
