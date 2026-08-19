from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.plugin_schema import (
    PluginActionResponse,
    PluginInfo,
    PluginListResponse,
)
from app.services.acl_manager import DynamicACLManager, get_acl_manager

router = APIRouter(prefix="/plugins", tags=["Plugins Management"])


@router.get("", response_model=PluginListResponse, summary="Liệt kê danh sách plugin")
def list_plugins(
    active_only: bool = Query(False, description="Chỉ lấy danh sách các plugin đang kích hoạt (is_active=True)"),
    sync: bool = Query(True, description="Tự động đồng bộ với thư mục plugins/ trước khi trả kết quả"),
    acl_mgr: DynamicACLManager = Depends(get_acl_manager),
) -> PluginListResponse:
    """
    Lấy danh sách các plugin trong hệ thống.
    - Mặc định tự động quét thư mục `plugins/` để cập nhật trạng thái mới nhất.
    """
    if sync:
        acl_mgr.scan_and_load_plugins()
    raw_plugins = acl_mgr.list_plugins(active_only=active_only)
    plugins = [PluginInfo(**p) for p in raw_plugins]
    return PluginListResponse(total=len(plugins), plugins=plugins)


@router.post("/sync", response_model=PluginListResponse, summary="Đồng bộ lại thư mục plugins/")
def sync_plugins(acl_mgr: DynamicACLManager = Depends(get_acl_manager)) -> PluginListResponse:
    """
    Quét lại thư mục `plugins/` để nạp các file mới và gỡ bỏ các file đã bị xóa.
    """
    raw_plugins = acl_mgr.scan_and_load_plugins()
    plugins = [PluginInfo(**p) for p in raw_plugins]
    return PluginListResponse(total=len(plugins), plugins=plugins)


@router.post("/unregister/{name}", response_model=PluginActionResponse, summary="Tắt / Gỡ bỏ plugin khỏi runtime")
def unregister_plugin(
    name: str,
    acl_mgr: DynamicACLManager = Depends(get_acl_manager),
) -> PluginActionResponse:
    """
    Gỡ bỏ một plugin khỏi runtime.
    """
    success = acl_mgr.unregister_plugin(name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy plugin active có tên '{name}'",
        )
    return PluginActionResponse(
        success=True,
        message=f"Đã gỡ bỏ plugin '{name}' thành công khỏi pipeline runtime",
    )


@router.post("/reset", response_model=PluginActionResponse, summary="Khôi phục trạng thái từ thư mục plugins/")
def reset_plugins(acl_mgr: DynamicACLManager = Depends(get_acl_manager)) -> PluginActionResponse:
    """
    Reset toàn bộ plugin và quét lại thư mục `plugins/`.
    """
    acl_mgr.reset()
    return PluginActionResponse(
        success=True,
        message="Đã đồng bộ lại toàn bộ plugins từ thư mục plugins/",
    )
