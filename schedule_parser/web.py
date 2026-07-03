from __future__ import annotations

import os
import traceback
from typing import Any

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from .image_enhancement import prepare_ocr_image
from .oil_street import parse_oil_street_schedule
from .openrouter_ocr import (
    OpenRouterOCRAPIError,
    OpenRouterOCRConfigError,
    merge_logsheet_daily_rows,
    ocr_logsheet_with_openrouter,
)
from .roster_compare import (
    compare_schedule_to_ocr,
    normalize_early_in_grace_minutes,
    normalize_early_leave_grace_minutes,
    normalize_late_grace_minutes,
    normalize_overtime_grace_minutes,
)


ALLOWED_EXTENSIONS = {".xlsx", ".xlsm"}
OCR_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
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

    @app.post("/api/ocr-logsheet")
    def ocr_logsheet():
        uploads = [item for item in request.files.getlist("logsheet") if item and item.filename]
        if not uploads:
            return _error_response("請上傳 logsheet 圖片或 PDF。", 400)

        prepared_uploads = []
        for uploaded in uploads:
            safe_name = secure_filename(uploaded.filename)
            if not safe_name:
                return _error_response("檔案名稱無效。", 400)
            if not _allowed_ocr_filename(safe_name):
                return _error_response("只支援 .jpg、.jpeg、.png、.webp 或 .pdf logsheet。", 400)
            prepared_uploads.append((uploaded, safe_name))

        try:
            results = []
            daily_rows = []
            prompt = (request.form.get("prompt") or "").strip() or None
            enhance_images = _coerce_bool(request.form.get("enhance_image"), default=True)
            for uploaded, safe_name in prepared_uploads:
                raw_bytes = uploaded.read()
                if not raw_bytes:
                    return _error_response(f"{safe_name} 是空白檔案。", 400)
                ocr_bytes, ocr_mime_type, preprocessing = prepare_ocr_image(
                    raw_bytes,
                    safe_name,
                    mime_type=uploaded.mimetype or None,
                    enabled=enhance_images,
                )
                result = ocr_logsheet_with_openrouter(
                    ocr_bytes,
                    safe_name,
                    mime_type=ocr_mime_type or uploaded.mimetype or None,
                    prompt=prompt,
                )
                result["preprocessing"] = preprocessing
                results.append(result)
                daily_rows.extend(result.get("daily_rows") or [])
            return jsonify({"ok": True, "ocr": _combined_ocr_result(results, daily_rows)})
        except OpenRouterOCRConfigError as exc:
            return _error_response(str(exc), 503)
        except OpenRouterOCRAPIError as exc:
            return _error_response(str(exc), 502)
        except ValueError as exc:
            return _error_response(str(exc), 400)
        except Exception as exc:  # pragma: no cover - exercised only for unexpected failures
            details = traceback.format_exc() if app.config["SCHEDULE_PARSER_DEBUG"] else None
            return _error_response(str(exc) or "OCR 時發生未預期錯誤。", 500, details)

    @app.post("/api/compare-roster")
    def compare_roster():
        payload = request.get_json(silent=True) or {}
        schedule = payload.get("schedule")
        if not isinstance(schedule, dict):
            return _error_response("缺少 schedule JSON。", 400)
        try:
            comparison = compare_schedule_to_ocr(
                schedule,
                _ocr_rows_from_payload(payload),
                late_grace_minutes=_coerce_late_grace_minutes(payload.get("late_grace_minutes")),
                early_leave_grace_minutes=_coerce_early_leave_grace_minutes(payload.get("early_leave_grace_minutes")),
                count_early_in=_coerce_bool(payload.get("count_early_in"), default=False),
                early_in_grace_minutes=_coerce_early_in_grace_minutes(payload.get("early_in_grace_minutes")),
                count_overtime=_coerce_bool(payload.get("count_overtime"), default=False),
                overtime_grace_minutes=_coerce_overtime_grace_minutes(payload.get("overtime_grace_minutes")),
            )
            return jsonify({"ok": True, "comparison": comparison})
        except ValueError as exc:
            return _error_response(str(exc), 400)
        except Exception as exc:  # pragma: no cover - exercised only for unexpected failures
            details = traceback.format_exc() if app.config["SCHEDULE_PARSER_DEBUG"] else None
            return _error_response(str(exc) or "核對時發生未預期錯誤。", 500, details)

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


def _allowed_ocr_filename(filename: str) -> bool:
    lower = filename.lower()
    return any(lower.endswith(ext) for ext in OCR_ALLOWED_EXTENSIONS)


def _combined_ocr_result(results: list[dict[str, Any]], daily_rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_filenames = [result.get("source_filename") or "" for result in results if result.get("source_filename")]
    merged_rows = merge_logsheet_daily_rows(daily_rows)
    return {
        "source_count": len(results),
        "source_filename": ", ".join(source_filenames),
        "source_filenames": source_filenames,
        "configured_model": _first_non_empty(result.get("configured_model") for result in results),
        "response_model": _first_non_empty(result.get("response_model") for result in results),
        "finish_reason": _first_non_empty(result.get("finish_reason") for result in results),
        "daily_rows": merged_rows,
        "structured": {
            "document_type": "logsheet",
            "daily_rows": merged_rows,
            "results": [result.get("structured") for result in results],
        },
        "results": results,
        "usage": _combined_usage(results),
    }


def _combined_usage(results: list[dict[str, Any]]) -> dict[str, Any]:
    usage: dict[str, Any] = {}
    for result in results:
        result_usage = result.get("usage")
        if not isinstance(result_usage, dict):
            continue
        for key, value in result_usage.items():
            if isinstance(value, (int, float)):
                usage[key] = usage.get(key, 0) + value
    return usage


def _first_non_empty(values) -> str:
    for value in values:
        if value:
            return str(value)
    return ""


def _ocr_rows_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("ocr_rows")
    if rows is None:
        ocr = payload.get("ocr")
        if isinstance(ocr, dict):
            rows = ocr.get("daily_rows")
            if rows is None and isinstance(ocr.get("structured"), dict):
                rows = ocr["structured"].get("daily_rows")
    if rows is None:
        return []
    if not isinstance(rows, list):
        raise ValueError("ocr_rows must be a list")
    return [row for row in rows if isinstance(row, dict)]


def _coerce_late_grace_minutes(value: Any) -> int:
    return normalize_late_grace_minutes(value)


def _coerce_early_leave_grace_minutes(value: Any) -> int:
    return normalize_early_leave_grace_minutes(value)


def _coerce_early_in_grace_minutes(value: Any) -> int:
    return normalize_early_in_grace_minutes(value)


def _coerce_overtime_grace_minutes(value: Any) -> int:
    return normalize_overtime_grace_minutes(value)


def _coerce_bool(value: Any, *, default: bool = False) -> bool:
    if value in (None, ""):
        return default
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


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
