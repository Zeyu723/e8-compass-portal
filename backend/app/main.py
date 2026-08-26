from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import assessments, controls, demo, health

settings = get_settings()

app = FastAPI(
    title="E8 Compass API",
    description="FastAPI backend for E8 Compass Portal Essential Eight assessment demo.",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(controls.router)
app.include_router(demo.router)
app.include_router(assessments.router)
