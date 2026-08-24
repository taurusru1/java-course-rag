from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ImportManifest:
    """保存 source_file -> hash；仅在向量写入成功后更新。"""

    def __init__(self, path: str | Path = ".runtime/import_manifest.json"):
        self.path = Path(path)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "files": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("files"), dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
        return {"version": 1, "files": {}}

    def has_same_hash(self, source_file: str, file_hash: str) -> bool:
        return self._read()["files"].get(source_file, {}).get("file_hash") == file_hash

    def record(self, source_file: str, file_hash: str, chunk_count: int) -> None:
        data = self._read()
        data["files"][source_file] = {"file_hash": file_hash, "chunk_count": chunk_count}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)
