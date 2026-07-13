from __future__ import annotations

import calendar
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime
import json
import os
import re
import traceback
from typing import Any

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename

from .d_and_g import parse_d_and_g_schedule
from .image_enhancement import PreparedOcrSource, prepare_ocr_image, prepare_oil_street_timecard_sources
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
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_prefix=1)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
    app.config["SCHEDULE_PARSER_DEBUG"] = os.getenv("SCHEDULE_PARSER_DEBUG") == "1"
    app.config["ASSET_VERSION"] = _asset_version(app.static_folder)

    @app.get("/")
    def index():
        return render_template("parser_index.html", asset_version=app.config["ASSET_VERSION"])

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
            project_profile = _project_profile_from_request()
            prompt = _ocr_prompt_for_project(project_profile, request.form.get("prompt"))
            enhance_images = _coerce_bool(request.form.get("enhance_image"), default=True)
            staff_names = _staff_names_from_request()
            for uploaded, safe_name in prepared_uploads:
                raw_bytes = uploaded.read()
                if not raw_bytes:
                    return _error_response(f"{safe_name} 是空白檔案。", 400)
                sources = _prepared_ocr_sources(
                    project_profile,
                    raw_bytes,
                    safe_name,
                    mime_type=uploaded.mimetype or None,
                    enhance_images=enhance_images,
                    staff_names=staff_names,
                )
                source_results = _ocr_prepared_sources(
                    sources,
                    prompt=prompt,
                    fallback_mime_type=uploaded.mimetype or None,
                )
                for source, result in zip(sources, source_results):
                    result["preprocessing"] = source.preprocessing
                    result["source_metadata"] = {**(result.get("source_metadata") or {}), **source.metadata}
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
            project_profile = _project_profile_from_request()
            parsed = _parse_schedule_for_profile(project_profile, raw_bytes, safe_name)
            full_schedule = parsed.to_dict()
            full_schedule["project_profile"] = project_profile
            variants = _schedule_month_variants(full_schedule)
            inferred_key = _selected_schedule_variant_key(variants, safe_name)
            selected_key = "__all__" if variants else inferred_key
            data = full_schedule
            if raw_only:
                return jsonify(data)
            return jsonify({
                "ok": True,
                "schedule": data,
                "summary": _summary(data),
                "schedule_variants": variants,
                "selected_schedule_key": selected_key,
                "inferred_schedule_key": inferred_key,
            })
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


def _asset_version(static_folder: str | None) -> str:
    configured = os.getenv("SOLOMONSCAN_ASSET_VERSION") or os.getenv("APP_VERSION")
    if configured:
        return re.sub(r"[^A-Za-z0-9_.-]", "", configured) or "configured"
    if not static_folder:
        return "dev"
    try:
        mtimes = [
            os.path.getmtime(os.path.join(static_folder, filename))
            for filename in ("parser_app.js", "parser_styles.css")
        ]
    except OSError:
        return "dev"
    return str(int(max(mtimes)))


def _project_profile_from_request() -> str:
    value = (request.form.get("project_profile") or "oil_street").strip().lower()
    return value if value in {"oil_street", "heritage", "d_and_g"} else "oil_street"


def _prepared_ocr_sources(
    project_profile: str,
    raw_bytes: bytes,
    filename: str,
    *,
    mime_type: str | None,
    enhance_images: bool,
    staff_names: list[str] | None = None,
) -> list[PreparedOcrSource]:
    if project_profile == "oil_street":
        return prepare_oil_street_timecard_sources(
            raw_bytes,
            filename,
            mime_type=mime_type,
            enabled=enhance_images,
            staff_names=staff_names,
        )
    ocr_bytes, ocr_mime_type, preprocessing = prepare_ocr_image(
        raw_bytes,
        filename,
        mime_type=mime_type,
        enabled=enhance_images,
    )
    return [
        PreparedOcrSource(
            file_bytes=ocr_bytes,
            filename=filename,
            mime_type=ocr_mime_type,
            source_filename=filename,
            preprocessing=preprocessing,
            metadata={"source_type": "single", "source_part_count": 1},
        )
    ]


def _staff_names_from_request() -> list[str]:
    raw_value = request.form.get("staff_names")
    if not raw_value:
        return []
    try:
        values = json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(values, list):
        return []
    names: list[str] = []
    for value in values:
        name = str(value or "").strip()
        if name and name not in names:
            names.append(name)
    return names[:500]


def _ocr_prepared_sources(
    sources: list[PreparedOcrSource],
    *,
    prompt: str | None,
    fallback_mime_type: str | None,
) -> list[dict[str, Any]]:
    def run(source: PreparedOcrSource) -> dict[str, Any]:
        return ocr_logsheet_with_openrouter(
            source.file_bytes,
            source.filename,
            mime_type=source.mime_type or fallback_mime_type,
            prompt=_ocr_prompt_for_source(prompt, source.metadata),
            source_filename=source.source_filename,
            source_metadata=source.metadata,
        )

    is_pdf_card_batch = len(sources) > 2 and all(
        source.metadata.get("source_type") == "pdf_timecard_pair"
        for source in sources
    )
    if not is_pdf_card_batch:
        return [run(source) for source in sources]
    max_workers = min(len(sources), _positive_env_int("OPENROUTER_PDF_CARD_PARALLELISM", 3))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(run, sources))


def _ocr_prompt_for_source(prompt: str | None, metadata: dict[str, Any]) -> str | None:
    staff_name_hint = str(metadata.get("source_staff_name_hint") or "").strip()
    if not staff_name_hint:
        return prompt
    instruction = (
        "Oil Street PDF card-pair instruction:\n"
        f"- The two visible half-month cards belong to exactly this staff member: {staff_name_hint}.\n"
        f"- Return the row-level name exactly as: {staff_name_hint}.\n"
        "- Extract every worked day from both Card 1 and Card 2; do not summarize or omit sparse rows."
    )
    return f"{prompt}\n\n{instruction}".strip() if prompt else instruction


def _positive_env_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default


def _parse_schedule_for_profile(project_profile: str, raw_bytes: bytes, filename: str):
    if project_profile == "d_and_g":
        return parse_d_and_g_schedule(raw_bytes, filename=filename)
    return parse_oil_street_schedule(raw_bytes, filename=filename)


def _ocr_prompt_for_project(project_profile: str, user_prompt: Any) -> str | None:
    extra = (str(user_prompt or "").strip()) or None
    if project_profile != "d_and_g":
        return extra
    default_year = datetime.today().year
    instructions = f"""
D&G project instruction:
- These files are Daniel & Co / D&G promoter work record sheets. A single photo can contain multiple separate paper forms.
- Extract every visible form independently. Use the handwritten staff name in the form's name field for each row.
- Do not infer a staff name from generic filenames such as "1 and 2 Apr 1.jpg", "3 Apr.jpg", or "Timesheet".
- The work table columns are date/day, in time, store signature, out time, store signature, then review columns. Use only handwritten in/out times from the same table row.
- The current sheet image is the source of truth for OCR rows. Count the visible handwritten person/table rows and output one daily_rows item for every visible row, even when a time cell is blank or unreadable.
- Include rows that have a visible person name, phone/name evidence, signature mark, or handwritten date/time evidence. Use null for missing in/out times instead of dropping the row.
- Dates may be d/m, d-MMM, or day numbers. Prefer full YYYY-MM-DD dates; use {default_year} when the year is not visible unless the user instruction says otherwise.
- Ignore blank printed am/pm markers, signatures, review stamps, and bank/account fields.
""".strip()
    if extra:
        return f"{instructions}\n\nUser note:\n{extra}"
    return instructions


def _schedule_month_variants(schedule: dict[str, Any]) -> list[dict[str, Any]]:
    months = _date_months(schedule.get("date_columns") or [])
    if len(months) <= 1:
        return []
    return [
        {
            "key": month,
            "month": month,
            "label": _month_label(month),
            "summary": _summary(month_schedule),
            "schedule": month_schedule,
        }
        for month in months
        for month_schedule in [_schedule_for_month(schedule, month)]
    ]


def _date_months(date_columns: list[dict[str, Any]]) -> list[str]:
    months = []
    for column in date_columns:
        date_text = str(column.get("date") or "")
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_text):
            month = date_text[:7]
            if month not in months:
                months.append(month)
    return months


def _schedule_for_month(schedule: dict[str, Any], month: str) -> dict[str, Any]:
    result = deepcopy(schedule)
    date_columns = [
        column for column in schedule.get("date_columns") or []
        if str(column.get("date") or "").startswith(f"{month}-")
    ]
    entries = [
        entry for entry in schedule.get("entries") or []
        if str(entry.get("date") or "").startswith(f"{month}-")
    ]
    result["date_columns"] = date_columns
    result["entries"] = entries
    result["schedule_month"] = month
    result["schedule_month_label"] = _month_label(month)
    warnings = _filter_messages_for_month(schedule.get("warnings") or [], date_columns, entries)
    errors = _filter_messages_for_month(schedule.get("errors") or [], date_columns, entries)
    result["warnings"] = warnings
    result["errors"] = errors
    result["diagnostics"] = _month_diagnostics(schedule, month, date_columns, entries, warnings, errors)
    return result


def _filter_messages_for_month(
    messages: list[dict[str, Any]],
    date_columns: list[dict[str, Any]],
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cells = set()
    cells.update(str(entry.get("date_cell") or "") for entry in entries)
    cells.update(str(entry.get("schedule_cell") or "") for entry in entries)
    for column in date_columns:
        letter = str(column.get("letter") or "")
        if letter:
            cells.add(letter)
    return [
        message for message in messages
        if not message.get("cell") or str(message.get("cell")) in cells
    ]


def _month_diagnostics(
    schedule: dict[str, Any],
    month: str,
    date_columns: list[dict[str, Any]],
    entries: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    diagnostics = deepcopy(schedule.get("diagnostics") or {})
    diagnostics["date_count"] = len(date_columns)
    diagnostics["entry_count"] = len(entries)
    diagnostics["warning_count"] = len(warnings)
    diagnostics["error_count"] = len(errors)
    diagnostics["month_split"] = {
        "month": month,
        "label": _month_label(month),
        "source_sheet_name": schedule.get("sheet_name") or "",
        "source_date_count": len(schedule.get("date_columns") or []),
        "source_entry_count": len(schedule.get("entries") or []),
        "date_count": len(date_columns),
        "entry_count": len(entries),
    }
    return diagnostics


def _selected_schedule_variant_key(variants: list[dict[str, Any]], filename: str) -> str:
    if not variants:
        return ""
    inferred = _infer_month_from_filename(filename, [str(variant["key"]) for variant in variants])
    if inferred:
        return inferred
    return str(variants[-1]["key"])


def _infer_month_from_filename(filename: str, available_months: list[str]) -> str:
    text = filename.lower()
    for month_index in range(1, 13):
        names = {calendar.month_name[month_index].lower(), calendar.month_abbr[month_index].lower()}
        if not any(re.search(rf"\b{re.escape(name)}\b", text) for name in names if name):
            continue
        year_match = re.search(r"\b(20\d{2})\b", text)
        if year_match:
            candidate = f"{year_match.group(1)}-{month_index:02d}"
            if candidate in available_months:
                return candidate
        month_matches = [month for month in available_months if month.endswith(f"-{month_index:02d}")]
        if len(month_matches) == 1:
            return month_matches[0]
    return ""


def _month_label(month: str) -> str:
    try:
        year, month_number = month.split("-")
        return f"{calendar.month_name[int(month_number)]} {year}"
    except (ValueError, IndexError):
        return month


def _combined_ocr_result(results: list[dict[str, Any]], daily_rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_filenames = _unique_non_empty(result.get("source_filename") for result in results)
    source_part_filenames = _unique_non_empty(
        result.get("source_part_filename")
        or (result.get("source_metadata") or {}).get("source_part_filename")
        for result in results
    )
    if len(results) == 1 and isinstance(results[0].get("page_results"), list):
        merged_rows = results[0].get("daily_rows") or daily_rows
    else:
        merged_rows = merge_logsheet_daily_rows(daily_rows)
    page_results = [
        page
        for result in results
        for page in (result.get("page_results") or [])
        if isinstance(page, dict)
    ]
    return {
        "source_count": len(source_filenames),
        "ocr_part_count": len(results),
        "source_filename": ", ".join(source_filenames),
        "source_filenames": source_filenames,
        "source_part_filenames": source_part_filenames,
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
        "page_results": page_results,
        "usage": _combined_usage(results),
    }


def _unique_non_empty(values) -> list[str]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return result


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
        "schedule_month": schedule.get("schedule_month") or "",
        "schedule_month_label": schedule.get("schedule_month_label") or "",
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
