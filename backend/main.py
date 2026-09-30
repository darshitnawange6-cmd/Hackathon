import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from backend.config import PORT, HOST, CORS_ORIGINS, AI_PROVIDER
from backend.database import init_db
from backend.routers import chat, campus, documents

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize and seed SQLite database
    print(f"Initializing VocaGuide Campus Database (Active AI Provider: {AI_PROVIDER})...")
    init_db()
    yield
    print("VocaGuide Assistant Backend shutting down.")

app = FastAPI(
    title="VocaGuide – AI Voice-Powered Campus Assistant API",
    description="Backend API providing conversational voice intelligence, intent detection, and campus knowledge retrieval.",
    version="1.0.0",
    lifespan=lifespan
)

# Production CORS configuration
if CORS_ORIGINS == ["*"]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
else:
    # Explicit origins (e.g. Vercel production domain + localhost) with Vercel preview deploys regex
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

# Global unhandled exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[Unhandled Server Error] {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred while processing the campus assistant request.",
            "type": exc.__class__.__name__
        }
    )

# Include routers
app.include_router(chat.router)
app.include_router(campus.router)
app.include_router(documents.router)

# Health check endpoints
@app.get("/health", tags=["Health"])
async def root_health_check():
    """Cloud platform health check endpoint (Render, AWS, Kubernetes)."""
    return {
        "status": "healthy",
        "service": "vocaguide-api",
        "version": "1.0.0",
        "provider": AI_PROVIDER
    }

@app.get("/", tags=["Root"])
async def root():
    return {
        "project": "VocaGuide – AI Voice-Powered Campus Assistant",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/health",
        "api_health_url": "/api/health"
    }

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=False)
