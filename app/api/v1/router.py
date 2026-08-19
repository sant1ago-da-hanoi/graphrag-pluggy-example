from fastapi import APIRouter

from app.api.v1.endpoints_pipeline import router as pipeline_router
from app.api.v1.endpoints_plugins import router as plugins_router

api_router = APIRouter()
api_router.include_router(plugins_router)
api_router.include_router(pipeline_router)
