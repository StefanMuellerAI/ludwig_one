"""
LudwigOne API - Main application entry point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.database import init_db, close_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configure rate limiter
limiter = Limiter(key_func=get_remote_address)


# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting LudwigOne API...")
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down LudwigOne API...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="LudwigOne API",
    description="KI-gestützte Dokumentenverarbeitungs-Plattform",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS (more restrictive)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "ludwigone-api",
            "version": "1.0.0"
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LudwigOne API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Import and include routers
from app.api.v1 import jobs, auth
from app.api.v1.admin import categories, config, prompts

# Public routes
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

# Admin routes (protected)
app.include_router(categories.router, prefix="/api/v1/admin/categories", tags=["admin-categories"])
app.include_router(config.router, prefix="/api/v1/admin/config", tags=["admin-config"])
app.include_router(prompts.router, prefix="/api/v1/admin/prompts", tags=["admin-prompts"])
# TODO: Add more admin routers (documents, analytics)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
