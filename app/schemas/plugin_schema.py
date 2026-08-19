from pydantic import BaseModel, Field


class PluginInfo(BaseModel):
    name: str = Field(..., description="Tên định danh của plugin")
    class_name: str = Field(..., description="Tên Python class của plugin")
    description: str | None = Field(None, description="Mô tả chức năng plugin")
    source: str = Field("builtin", description="Nguồn gốc plugin (builtin hoặc đường dẫn file)")
    is_active: bool = Field(True, description="Trạng thái hoạt động")


class PluginListResponse(BaseModel):
    total: int = Field(..., description="Tổng số plugins đã đăng ký")
    plugins: list[PluginInfo] = Field(..., description="Danh sách chi tiết các plugins")


class PluginRegisterRequest(BaseModel):
    name: str = Field(..., description="Tên định danh muốn đặt cho plugin")
    file_path: str = Field(
        ..., description="Đường dẫn tuyệt đối hoặc tương đối tới file .py chứa plugin"
    )
    class_name: str | None = Field(None, description="Tên class plugin (để trống nếu tự động tìm)")


class PluginReloadRequest(BaseModel):
    name: str = Field(..., description="Tên plugin cần hot-reload")
    file_path: str = Field(..., description="Đường dẫn tới file mã nguồn cập nhật")
    class_name: str | None = Field(None, description="Tên class plugin")


class PluginActionResponse(BaseModel):
    success: bool = Field(..., description="Trạng thái thành công của thao tác")
    message: str = Field(..., description="Thông báo kết quả")
    plugin: PluginInfo | None = Field(None, description="Thông tin plugin sau thao tác")
