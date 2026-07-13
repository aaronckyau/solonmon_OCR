from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import secrets
import time
from typing import Any

from .image_enhancement import PreparedOcrSource


PREVIEW_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")
DEFAULT_PREVIEW_TTL_SECONDS = 24 * 60 * 60


@dataclass(slots=True)
class StoredOcrPreview:
    preview_id: str
    filename: str
    mime_type: str | None
    source_filename: str
    preprocessing: dict[str, Any]
    metadata: dict[str, Any]
    created_at: int

    @property
    def preview_path(self) -> str:
        return f"/api/ocr-preview/{self.preview_id}"

    def to_public_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "preview_path": self.preview_path,
        }


def store_prepared_ocr_source(source: PreparedOcrSource) -> StoredOcrPreview:
    root = preview_root()
    root.mkdir(parents=True, exist_ok=True)
    cleanup_expired_previews(root)

    preview_id = secrets.token_hex(16)
    created_at = int(time.time())
    metadata = dict(source.metadata)
    metadata["source_preview_path"] = f"/api/ocr-preview/{preview_id}"
    stored = StoredOcrPreview(
        preview_id=preview_id,
        filename=source.filename,
        mime_type=source.mime_type,
        source_filename=source.source_filename,
        preprocessing=dict(source.preprocessing),
        metadata=metadata,
        created_at=created_at,
    )
    _atomic_write_bytes(_preview_data_path(root, preview_id), source.file_bytes)
    _atomic_write_text(_preview_record_path(root, preview_id), json.dumps(asdict(stored), ensure_ascii=False))
    return stored


def load_stored_ocr_preview(preview_id: str) -> StoredOcrPreview | None:
    if not PREVIEW_ID_PATTERN.fullmatch(str(preview_id or "")):
        return None
    root = preview_root()
    record_path = _preview_record_path(root, preview_id)
    data_path = _preview_data_path(root, preview_id)
    if not record_path.is_file() or not data_path.is_file():
        return None
    try:
        payload = json.loads(record_path.read_text(encoding="utf-8"))
        stored = StoredOcrPreview(**payload)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None
    if int(time.time()) - stored.created_at > preview_ttl_seconds():
        _remove_preview_files(root, preview_id)
        return None
    return stored


def read_stored_ocr_preview_bytes(preview_id: str) -> bytes | None:
    stored = load_stored_ocr_preview(preview_id)
    if stored is None:
        return None
    try:
        return _preview_data_path(preview_root(), preview_id).read_bytes()
    except OSError:
        return None


def preview_data_path(preview_id: str) -> Path | None:
    if load_stored_ocr_preview(preview_id) is None:
        return None
    return _preview_data_path(preview_root(), preview_id)


def preview_root() -> Path:
    configured = os.getenv("OCR_PREVIEW_DIR", "runtime/ocr_previews").strip()
    path = Path(configured or "runtime/ocr_previews")
    return path if path.is_absolute() else Path.cwd() / path


def preview_ttl_seconds() -> int:
    try:
        return max(300, int(os.getenv("OCR_PREVIEW_TTL_SECONDS", str(DEFAULT_PREVIEW_TTL_SECONDS))))
    except (TypeError, ValueError):
        return DEFAULT_PREVIEW_TTL_SECONDS


def cleanup_expired_previews(root: Path | None = None) -> None:
    target = root or preview_root()
    if not target.is_dir():
        return
    cutoff = time.time() - preview_ttl_seconds()
    for record_path in target.glob("*.json"):
        try:
            if record_path.stat().st_mtime >= cutoff:
                continue
        except OSError:
            continue
        _remove_preview_files(target, record_path.stem)


def _preview_data_path(root: Path, preview_id: str) -> Path:
    return root / f"{preview_id}.source"


def _preview_record_path(root: Path, preview_id: str) -> Path:
    return root / f"{preview_id}.json"


def _remove_preview_files(root: Path, preview_id: str) -> None:
    for path in (_preview_data_path(root, preview_id), _preview_record_path(root, preview_id)):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


def _atomic_write_text(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)
