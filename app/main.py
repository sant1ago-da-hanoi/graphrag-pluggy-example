from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.services.acl_manager import get_acl_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Tự động quét và nạp toàn bộ plugins trong thư mục plugins/
    acl_mgr = get_acl_manager()
    acl_mgr.scan_and_load_plugins()
    yield
    # Shutdown: Dọn dẹp nếu cần
    pass


app = FastAPI(
    title=settings.app_name,
    description="""
    ## 🚀 FastAPI Dynamic ACL Plugin Showcase for GraphRAG-Toolkit
    
    Hệ thống hỗ trợ **Drop-in Plugin Architecture**:
    * **📂 Tự Động Nhận Diện**: Mọi file Python `.py` nằm trong thư mục `plugins/` đều tự động được phát hiện và kích hoạt vào GraphRAG Extraction Pipeline.
    * **⚡ Zero Restart / Hot-Reload**: Chỉ cần copy file mới vào `plugins/` hoặc xóa file để tắt plugin ngay lập tức.
    * **🛡️ Phân Quyền Đa Lớp**: RBAC, Tenant Isolation, PII Masking.
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["Health Check"])
def root():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "docs_url": "/docs",
    }
