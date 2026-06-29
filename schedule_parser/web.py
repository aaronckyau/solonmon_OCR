from __future__ import annotations

import os
import traceback
from typing import Any

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from .oil_street import parse_oil_street_schedule


ALLOWED_EXTENSIONS = {".xlsx", ".xlsm"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5050


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
    app.config["SCHEDULE_PARSER_DEBUG"] = os.getenv("SCHEDULE_PARSER_DEBUG") == "1"

    @app.get("/")
    def index():
        return render_template("parser_index.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/api/parse")
    def parse_schedule():
        return _parse_upload(raw_only=False)

    @app.post("/api/parse-json")
    def parse_schedule_json():
        return _parse_upload(raw_only=True)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_upload(_exc):
        return _error_response("上傳檔案超過 20 MB。", 400)

    @app.errorhandler(400)
    def handle_bad_request(exc):
        return _error_response(str(exc.description or "無效的請求。"), 400)

    @app.errorhandler(500)
    def handle_server_error(exc):
        details = traceback.format_exc() if app.config["SCHEDULE_PARSER_DEBUG"] else None
        return _error_response("解析器網頁發生未預期錯誤。", 500, details)

    def _parse_upload(*, raw_only: bool):
        uploaded = request.files.get("schedule")
        if uploaded is None or not uploaded.filename:
            return _error_response("缺少上傳欄位：schedule。", 400)

        safe_name = secure_filename(uploaded.filename)
        if not safe_name:
            return _error_response("檔案名稱無效。", 400)
        if not _allowed_filename(safe_name):
            return _error_response("只支援 .xlsx 和 .xlsm 排班表檔案。", 400)

        try:
            raw_bytes = uploaded.read()
            if not raw_bytes:
                return _error_response("上傳檔案是空的。", 400)
            parsed = parse_oil_street_schedule(raw_bytes, filename=safe_name)
            data = parsed.to_dict()
            if raw_only:
                return jsonify(data)
            return jsonify({"ok": True, "schedule": data, "summary": _summary(data)})
        except ValueError as exc:
            return _error_response(str(exc), 400)
        except Exception as exc:  # pragma: no cover - exercised only for unexpected failures
            details = traceback.format_exc() if app.config["SCHEDULE_PARSER_DEBUG"] else None
            return _error_response(str(exc) or "解析時發生未預期錯誤。", 500, details)

    return app


def _allowed_filename(filename: str) -> bool:
    lower = filename.lower()
    return any(lower.endswith(ext) for ext in ALLOWED_EXTENSIONS)


def _summary(schedule: dict[str, Any]) -> dict[str, Any]:
    diagnostics = schedule.get("diagnostics") if isinstance(schedule.get("diagnostics"), dict) else {}
    return {
        "source_filename": schedule.get("source_filename") or "",
        "sheet_name": schedule.get("sheet_name") or "",
        "layout_type": schedule.get("layout_type") or "",
        "header_row": schedule.get("header_row"),
        "date_count": len(schedule.get("date_columns") or []),
        "staff_count": len(schedule.get("staff") or []),
        "entry_count": len(schedule.get("entries") or []),
        "shift_time_count": len(schedule.get("shift_times") or {}),
        "warning_count": diagnostics.get("warning_count", len(schedule.get("warnings") or [])),
        "error_count": diagnostics.get("error_count", len(schedule.get("errors") or [])),
        "unknown_shift_codes": diagnostics.get("unknown_shift_codes", []),
        "ai_used": bool(diagnostics.get("ai_used", False)),
    }


def _error_response(error: str, status_code: int, details: str | None = None):
    payload: dict[str, Any] = {"ok": False, "error": error}
    if details:
        payload["details"] = details
    return jsonify(payload), status_code


def main() -> int:
    app = create_app()
    host = os.getenv("SCHEDULE_PARSER_HOST", DEFAULT_HOST)
    port = int(os.getenv("SCHEDULE_PARSER_PORT", str(DEFAULT_PORT)))
    debug = os.getenv("SCHEDULE_PARSER_DEBUG") == "1"
    print("Schedule Parser Web UI running at:")
    print(f"http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
