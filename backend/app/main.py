from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from app.config import settings
from app.db import engine, Base, SessionLocal
from app.seed import seed_database
from app.api import users, dev

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("intentpay")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed if empty
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db, force=False)
    finally:
        db.close()
    yield
    # Shutdown logic if any

app = FastAPI(
    title="IntentPay API",
    description="Programmable Payments That Understand Your Intent — Policy and Decision Layer",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers ensuring unified JSON error envelopes
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = []
    for err in exc.errors():
        loc = ".".join(str(l) for l in err.get("loc", []))
        details.append(f"{loc}: {err.get('msg')}")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed: " + "; ".join(details),
                "fields": details
            }
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_SERVER_ERROR"
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code_map.get(exc.status_code, "ERROR"),
                "message": str(exc.detail),
                "fields": []
            }
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "fields": []
            }
        }
    )

from app.api import users, dev, intents, policies, payments, conflicts, suggestions, dashboard, analytics, simulator

from fastapi.responses import JSONResponse, RedirectResponse

# Root redirect to Swagger docs
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

# Base health route
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "intentpay",
        "demo_mode": settings.DEMO_MODE,
        "ai_configured": bool(settings.GEMINI_API_KEY)
    }

# Mount Routers
app.include_router(users.router)
app.include_router(intents.router)
app.include_router(policies.router)
app.include_router(payments.router)
app.include_router(conflicts.router)
app.include_router(suggestions.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)
app.include_router(simulator.router)
app.include_router(dev.router)
