import importlib.util
import os
import sys
from pathlib import Path
from typing import Any

import pluggy

from app.core.acl_specs import HOOK_NAMESPACE, ACLExtractHookSpec


class DynamicACLManager:
    """
    Trình quản lý plugin ACL động (Dynamic ACL Plugin Manager).

    Cơ chế Drop-in Plugin Directory:
    - Tự động quét và nạp toàn bộ file `.py` trong thư mục `plugins/`.
    - Mọi file mới copy vào `plugins/` sẽ tự động được phát hiện và kích hoạt.
    - File bị xóa khỏi `plugins/` sẽ tự động bị gỡ bỏ (unregister) khỏi runtime.
    """

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir).resolve()
        self.pm = pluggy.PluginManager(HOOK_NAMESPACE)
        self.pm.add_hookspecs(ACLExtractHookSpec)
        self._registered_plugins: dict[str, Any] = {}
        self._plugin_metadata: dict[str, dict[str, Any]] = {}

    def scan_and_load_plugins(self) -> list[dict[str, Any]]:
        """
        Quét thư mục `plugins/` và đồng bộ toàn bộ plugin vào runtime.
        """
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)

        found_plugin_names = set()

        for file_path in sorted(self.plugins_dir.glob("*.py")):
            if file_path.name.startswith("_") or file_path.name.startswith("."):
                continue

            plugin_name = file_path.stem
            found_plugin_names.add(plugin_name)

            try:
                self.load_plugin_from_file(plugin_name, file_path)
            except Exception as e:
                print(f"[PluginManager] Cảnh báo: Không thể nạp plugin từ {file_path.name}: {e}")

        # Tự động gỡ bỏ hoàn toàn các plugin đã bị xóa file khỏi thư mục plugins/
        for existing_name in list(self._plugin_metadata.keys()):
            meta = self._plugin_metadata.get(existing_name, {})
            if meta.get("source_type") == "drop_in" and existing_name not in found_plugin_names:
                self.unregister_plugin(existing_name)
                self._plugin_metadata.pop(existing_name, None)

        return self.list_plugins()

    def load_plugin_from_file(self, name: str, file_path: Path | str, class_name: str | None = None) -> dict[str, Any]:
        """
        Đọc, compile và nạp plugin từ một file .py cụ thể.
        """
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {path}")

        module_name = f"dynamic_plugin_{name}"
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None:
            raise ImportError(f"Không thể đọc module từ file: {path}")

        sys.modules.pop(module_name, None)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        source_code = path.read_text(encoding="utf-8")
        code = compile(source_code, str(path), "exec")
        exec(code, module.__dict__)

        target_cls = None
        if class_name:
            if not hasattr(module, class_name):
                raise AttributeError(f"Module '{module_name}' không chứa class '{class_name}'")
            target_cls = getattr(module, class_name)
        else:
            # Tự động tìm class có implement hookimpl hoặc kết thúc bằng 'Plugin'
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and (attr_name.endswith("Plugin") or hasattr(attr, "__doc__")):
                    for method_name in dir(attr):
                        method = getattr(attr, method_name, None)
                        if hasattr(method, "graphrag_acl_impl") or method_name in ["allow_node", "filter_output_doc", "filter_input_docs"]:
                            target_cls = attr
                            break
                if target_cls:
                    break

        if target_cls is None:
            raise AttributeError(f"Không tìm thấy Plugin class hợp lệ trong file {path.name}")

        instance = target_cls()
        self.register_plugin(
            name=name,
            plugin_instance=instance,
            description=(instance.__doc__ or "").strip(),
            source=str(path),
            source_type="drop_in",
        )
        return self._plugin_metadata[name]

    def register_plugin(
        self,
        name: str,
        plugin_instance: Any,
        description: str | None = None,
        source: str = "builtin",
        source_type: str = "builtin",
    ):
        """
        Đăng ký một instance plugin vào Pluggy PluginManager.
        """
        if name in self._registered_plugins:
            old_plugin = self._registered_plugins.pop(name)
            self.pm.unregister(old_plugin)

        self.pm.register(plugin_instance, name=name)
        self._registered_plugins[name] = plugin_instance
        self._plugin_metadata[name] = {
            "name": name,
            "class_name": plugin_instance.__class__.__name__,
            "description": description or (plugin_instance.__doc__ or "").strip(),
            "source": source,
            "source_type": source_type,
            "is_active": True,
        }

    def unregister_plugin(self, name: str) -> bool:
        """
        Gỡ bỏ một plugin khỏi Pluggy runtime.
        """
        plugin = self._registered_plugins.pop(name, None)
        if plugin is not None:
            self.pm.unregister(plugin)
            if name in self._plugin_metadata:
                self._plugin_metadata[name]["is_active"] = False
            return True
        return False

    def list_plugins(self, active_only: bool = False) -> list[dict[str, Any]]:
        """
        Trả về danh sách các plugin kèm thông tin chi tiết.
        """
        result = []
        for name, meta in self._plugin_metadata.items():
            if active_only and not meta.get("is_active", False):
                continue
            result.append(dict(meta))
        return result

    def get_plugin(self, name: str) -> Any | None:
        return self._registered_plugins.get(name)

    def reset(self):
        """
        Khởi tạo lại toàn bộ plugin bằng cách quét lại thư mục `plugins/`.
        """
        for name in list(self._registered_plugins.keys()):
            self.unregister_plugin(name)
        self._registered_plugins.clear()
        self._plugin_metadata.clear()
        self.scan_and_load_plugins()


# Singleton instance quản lý thư mục plugins/
acl_manager = DynamicACLManager(plugins_dir=os.getenv("PLUGINS_DIR", "plugins"))


def get_acl_manager() -> DynamicACLManager:
    """Dependency provider cho FastAPI"""
    return acl_manager
