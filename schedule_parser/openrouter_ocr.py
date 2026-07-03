from __future__ import annotations

import base64
import json
import mimetypes
import os
from functools import lru_cache
from pathlib import Path
import re
import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = "qwen/qwen3.6-35b-a3b"
DEFAULT_PDF_ENGINE = "mistral-ocr"
SUPPORTED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
SUPPORTED_PDF_MIME_TYPE = "application/pdf"
TIME_RE = re.compile(r"(?<!\d)([01]?\d|2[0-3])\s*[:：.]\s*([0-5]\d)(?!\d)")
MONTH_RE = re.compile(
    r"\b("
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|sept(?:ember)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?"
    r")\s+(\d{4})\b",
    re.IGNORECASE,
)
YEAR_MONTH_RE = re.compile(r"\b(\d{4})[-_/ ](0?[1-9]|1[0-2])\b")
ISO_DATE_RE = re.compile(r"\b(\d{4})[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b")
DATE_FIELD_NAMES = ("date", "day", "day_number", "date_number")
NAME_FIELD_NAMES = ("name", "staff_name", "employee_name", "worker_name")
PUNCH_TIME_FIELD_NAMES = (
    "in",
    "out",
    "first_in",
    "last_out",
    "actual_in",
    "actual_out",
    "morning_in",
    "morning_out",
    "afternoon_in",
    "afternoon_out",
    "overtime_in",
    "overtime_out",
    "break_in",
    "break_out",
    "times",
    "punches",
    "all_times",
    "raw_times",
    "source_text",
)
MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


class OpenRouterOCRConfigError(RuntimeError):
    """Raised when local OpenRouter configuration is incomplete."""


class OpenRouterOCRAPIError(RuntimeError):
    """Raised when OpenRouter rejects or cannot complete the OCR request."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def ocr_logsheet_with_openrouter(
    file_bytes: bytes,
    filename: str,
    *,
    mime_type: str | None = None,
    prompt: str | None = None,
) -> dict[str, Any]:
    api_key = _config_value("OPENROUTER_API_KEY") or _config_value("OPENROUTER") or _config_value("openrouter")
    if not api_key:
        raise OpenRouterOCRConfigError("OPENROUTER_API_KEY is not set.")

    model = _config_value("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)
    payload = build_logsheet_ocr_payload(
        file_bytes,
        filename,
        model=model,
        mime_type=mime_type,
        prompt=prompt,
    )
    response = _post_openrouter(payload, api_key=api_key)
    choice = _first_choice(response)
    message = choice.get("message") if isinstance(choice.get("message"), dict) else {}
    text = _message_text(message.get("content"))
    structured = _extract_json_object(text)
    daily_rows = normalize_logsheet_daily_rows(structured, filename, context_hint=prompt)

    return {
        "source_filename": filename,
        "configured_model": model,
        "response_model": response.get("model") or "",
        "finish_reason": choice.get("finish_reason") or "",
        "text": text,
        "structured": structured,
        "daily_rows": daily_rows,
        "usage": response.get("usage") or {},
        "annotations": message.get("annotations") or [],
    }


def build_logsheet_ocr_payload(
    file_bytes: bytes,
    filename: str,
    *,
    model: str = DEFAULT_OPENROUTER_MODEL,
    mime_type: str | None = None,
    prompt: str | None = None,
) -> dict[str, Any]:
    detected_mime = _normalize_mime_type(filename, mime_type)
    encoded = base64.b64encode(file_bytes).decode("ascii")
    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": _build_prompt(prompt, filename),
        }
    ]

    if detected_mime == SUPPORTED_PDF_MIME_TYPE:
        content.append(
            {
                "type": "file",
                "file": {
                    "filename": filename,
                    "file_data": f"data:{detected_mime};base64,{encoded}",
                },
            }
        )
    elif detected_mime in SUPPORTED_IMAGE_MIME_TYPES:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{detected_mime};base64,{encoded}",
                },
            }
        )
    else:
        raise ValueError("Unsupported logsheet file type.")

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": content,
            }
        ],
        "temperature": 0,
        "max_tokens": _config_int("OPENROUTER_MAX_TOKENS", 4096),
        "stream": False,
    }
    reasoning_effort = _config_value("OPENROUTER_REASONING_EFFORT", "none").strip().lower()
    if reasoning_effort:
        payload["reasoning"] = {
            "effort": reasoning_effort,
            "exclude": True,
        }

    if detected_mime == SUPPORTED_PDF_MIME_TYPE:
        pdf_engine = _config_value("OPENROUTER_PDF_ENGINE", DEFAULT_PDF_ENGINE).strip()
        if pdf_engine:
            payload["plugins"] = [
                {
                    "id": "file-parser",
                    "pdf": {"engine": pdf_engine},
                }
            ]

    return payload


def _post_openrouter(payload: dict[str, Any], *, api_key: str) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    site_url = _config_value("OPENROUTER_SITE_URL")
    app_name = _config_value("OPENROUTER_APP_NAME", "Solonmon OCR")
    if site_url:
        headers["HTTP-Referer"] = site_url
    if app_name:
        headers["X-Title"] = app_name

    request = Request(
        _config_value("OPENROUTER_API_URL", DEFAULT_OPENROUTER_URL),
        data=data,
        headers=headers,
        method="POST",
    )
    timeout = _config_int("OPENROUTER_TIMEOUT_SECONDS", 90)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise OpenRouterOCRAPIError(_read_http_error(exc), exc.code) from exc
    except (URLError, TimeoutError, socket.timeout) as exc:
        raise OpenRouterOCRAPIError(f"OpenRouter request failed: {exc}") from exc

    try:
        return json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise OpenRouterOCRAPIError("OpenRouter returned invalid JSON.") from exc


def normalize_logsheet_daily_rows(
    structured: Any,
    source_filename: str,
    *,
    context_hint: str | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(structured, (dict, list)):
        return []

    filename_name_hint = _infer_staff_name_from_filename(source_filename)
    structured_name_hint = _extract_name_hint(structured)
    year_month = _extract_year_month_hint(structured, source_filename, context_hint)
    rows: list[dict[str, Any]] = []
    for item in _candidate_logsheet_rows(structured):
        if not isinstance(item, dict):
            continue
        times = _extract_times_from_row(item)
        if not times:
            continue
        ocr_name_hint = _string_or_none(_first_present(item, NAME_FIELD_NAMES)) or structured_name_hint
        row_name = filename_name_hint or ocr_name_hint
        row = {
            "name": row_name,
            "date": _normalize_date(_first_present(item, DATE_FIELD_NAMES), year_month),
            "in": None,
            "out": None,
            "source_filename": source_filename,
            "source_filenames": [source_filename],
            "all_times": sorted(set(times), key=_time_minutes),
            "warnings": item.get("warnings") if isinstance(item.get("warnings"), list) else [],
        }
        row["in"] = row["all_times"][0]
        row["out"] = row["all_times"][-1] if len(row["all_times"]) > 1 else None
        rows.append(row)

    return merge_logsheet_daily_rows(rows)


def merge_logsheet_daily_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    order: list[tuple[str, str, str]] = []
    for index, row in enumerate(rows):
        name = _string_or_none(row.get("name"))
        date = _string_or_none(row.get("date"))
        source_filename = _string_or_none(row.get("source_filename")) or ""
        key = (name or "", date or "", "" if date else f"{source_filename}:{index}")
        if key not in merged:
            merged[key] = {
                "name": name,
                "date": date,
                "in": None,
                "out": None,
                "source_filename": source_filename,
                "source_filenames": [],
                "all_times": [],
                "warnings": [],
            }
            order.append(key)
        target = merged[key]
        target["name"] = target["name"] or name
        target["date"] = target["date"] or date
        target["source_filename"] = target["source_filename"] or source_filename
        _append_unique(target["source_filenames"], row.get("source_filenames") or [source_filename])
        _append_unique(target["warnings"], row.get("warnings") or [])
        punch_times = _extract_time_values([row.get("all_times")])
        explicit_in = _extract_time_values([row.get("in")])
        explicit_out = _extract_time_values([row.get("out")])
        times = punch_times or [*explicit_in, *explicit_out]
        _append_unique(target["all_times"], times)
        target["all_times"] = sorted(set(target["all_times"]), key=_time_minutes)
        if punch_times and target["all_times"]:
            target["in"] = target["all_times"][0]
            target["out"] = target["all_times"][-1] if len(target["all_times"]) > 1 else None
        else:
            if explicit_in:
                current_in = _string_or_none(target.get("in"))
                target["in"] = min([time for time in [current_in, explicit_in[0]] if time], key=_time_minutes)
            if explicit_out:
                current_out = _string_or_none(target.get("out"))
                target["out"] = max([time for time in [current_out, explicit_out[0]] if time], key=_time_minutes)

    return [merged[key] for key in order]


def _build_prompt(extra_prompt: str | None, filename: str) -> str:
    base_prompt = f"""
You are OCRing a staff logsheet or timecard image/PDF.
Return only compact valid JSON. Do not wrap it in markdown.
Source filename or path: {filename}

Required JSON shape:
{{
  "document_type": "logsheet",
  "staff_name": null,
  "month_year": null,
  "daily_rows": [
    {{
      "name": null,
      "date": null,
      "in": null,
      "out": null,
      "all_times": [],
      "warnings": []
    }}
  ],
  "warnings": []
}}

Rules:
- Preserve exact names, dates, times, handwritten marks, and table text.
- Use null for unreadable or missing values; do not guess.
- Keep all row order from the source document.
- For each date/day row, collect every readable handwritten punch time in that row from MORNING, AFTERNOON, and OVER TIME columns.
- If a handwritten time includes the day prefix, such as "21 09:40", normalize the time to "09:40".
- The printed or left-margin row number is the date/day only. Never combine that row number with a nearby time, and never treat it as a punch time.
- Ignore grid row numbers, column headers, SIGNATURE, CHECK, ADMIN, and other printed form labels as punch times.
- Only use handwritten punch times that are on the same horizontal row as the date/day. If row alignment is uncertain, keep the row but add a Traditional Chinese warning.
- In "daily_rows", output one row per worked day only.
- In "daily_rows", "in" must be the first/earliest readable punch time of that day, and "out" must be the last/latest readable punch time of that day.
- If there is only one readable punch time for a day, put that time in "in" and use null for "out".
- If the staff name is blank on the card, infer it from the source filename when the filename contains a human name.
- If month/year is blank on the card, infer it only from the source filename/path or user instruction; otherwise keep date as the visible day number.
- Put any uncertainty in "warnings" in Traditional Chinese.
- Do not include raw_text, tables, entries, markdown, explanations, or duplicated OCR transcript.
""".strip()
    extra = (extra_prompt or "").strip()
    if not extra:
        return base_prompt
    return f"{base_prompt}\n\nAdditional user instruction:\n{extra}"


def _candidate_logsheet_rows(structured: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(structured, list):
        return [item for item in structured if isinstance(item, dict)]
    for key in ("daily_rows", "entries", "rows"):
        value = structured.get(key)
        if isinstance(value, list):
            rows.extend(item for item in value if isinstance(item, dict))
    tables = structured.get("tables")
    if isinstance(tables, list):
        for table in tables:
            if not isinstance(table, dict):
                continue
            columns = table.get("columns") if isinstance(table.get("columns"), list) else []
            for row in table.get("rows") or []:
                if isinstance(row, dict):
                    rows.append(row)
                elif isinstance(row, list) and columns:
                    rows.append({str(column): row[index] if index < len(row) else None for index, column in enumerate(columns)})
    return rows


def _extract_name_hint(structured: Any) -> str | None:
    if isinstance(structured, dict):
        value = _first_present(structured, NAME_FIELD_NAMES)
        if value:
            return _string_or_none(value)
    return None


def _extract_year_month_hint(structured: Any, source_filename: str, context_hint: str | None = None) -> tuple[int, int] | None:
    values = [source_filename]
    if context_hint:
        values.append(context_hint)
    if isinstance(structured, dict):
        values.extend(
            str(value)
            for key, value in structured.items()
            if key in {"month_year", "month", "year", "source_filename"} and value
        )
    joined = " ".join(values)
    iso_match = YEAR_MONTH_RE.search(joined)
    if iso_match:
        return int(iso_match.group(1)), int(iso_match.group(2))
    month_match = MONTH_RE.search(joined)
    if month_match:
        month_name = month_match.group(1).lower()
        month = MONTHS.get(month_name[:3]) or MONTHS.get(month_name)
        if month:
            return int(month_match.group(2)), month
    return None


def _normalize_date(value: Any, year_month: tuple[int, int] | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    iso_match = ISO_DATE_RE.search(text)
    if iso_match:
        year, month, day = (int(part) for part in iso_match.groups())
        return f"{year:04d}-{month:02d}-{day:02d}"
    day_match = re.search(r"(?<!\d)([1-9]|[12]\d|3[01])(?!\d)", text)
    if not day_match:
        return text
    day = int(day_match.group(1))
    if not year_month:
        return str(day)
    year, month = year_month
    return f"{year:04d}-{month:02d}-{day:02d}"


def _extract_times_from_row(row: dict[str, Any]) -> list[str]:
    values: list[Any] = []
    for key in PUNCH_TIME_FIELD_NAMES:
        if key in row:
            values.append(row[key])
    return _extract_time_values(values)


def _extract_time_values(values: list[Any]) -> list[str]:
    times: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, list):
            times.extend(_extract_time_values(value))
            continue
        if isinstance(value, dict):
            times.extend(_extract_time_values(list(value.values())))
            continue
        normalized = _normalize_time_text(str(value))
        _append_unique(times, normalized)
    return times


def _normalize_time_text(text: str) -> list[str]:
    times: list[str] = []
    for match in TIME_RE.finditer(text):
        hour = int(match.group(1))
        minute = int(match.group(2))
        if hour > 23:
            continue
        times.append(f"{hour:02d}:{minute:02d}")
    return times


def _time_minutes(value: str) -> int:
    match = TIME_RE.search(value)
    if not match:
        return 24 * 60
    return int(match.group(1)) * 60 + int(match.group(2))


def _first_present(row: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if row.get(name) not in (None, ""):
            return row.get(name)
    return None


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _append_unique(target: list[Any], values: Any) -> None:
    source = values if isinstance(values, list) else [values]
    for value in source:
        if value in (None, ""):
            continue
        if value not in target:
            target.append(value)


def _infer_staff_name_from_filename(source_filename: str) -> str | None:
    stem = Path(source_filename).stem
    stem = re.sub(r"[_-]+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    stem = re.sub(r"(?i)^oil street\s+", "", stem)
    stem = re.sub(r"(?i)\b(?:timecard|timesheet|logsheet)\b", "", stem)
    stem = re.sub(r"\s*\(\d+\)\s*$", "", stem)
    stem = re.sub(r"\s+\d+\s*$", "", stem)
    stem = re.sub(r"\s+", " ", stem).strip(" ,-_")
    return stem or None


def _normalize_mime_type(filename: str, mime_type: str | None) -> str:
    guessed = mimetypes.guess_type(filename)[0]
    normalized = (mime_type or guessed or "").split(";")[0].strip().lower()
    if normalized in {"image/jpg", "image/pjpeg"}:
        return "image/jpeg"
    if normalized in SUPPORTED_IMAGE_MIME_TYPES or normalized == SUPPORTED_PDF_MIME_TYPE:
        return normalized
    extension = os.path.splitext(filename.lower())[1]
    if extension == ".pdf":
        return SUPPORTED_PDF_MIME_TYPE
    if extension in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if extension == ".png":
        return "image/png"
    if extension == ".webp":
        return "image/webp"
    return normalized


def _first_choice(response: dict[str, Any]) -> dict[str, Any]:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise OpenRouterOCRAPIError("OpenRouter response did not include choices.")
    first = choices[0]
    if not isinstance(first, dict):
        raise OpenRouterOCRAPIError("OpenRouter response included an invalid choice.")
    return first


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts).strip()
    return ""


def _extract_json_object(text: str) -> dict[str, Any] | list[Any] | None:
    cleaned = text.strip()
    cleaned = _strip_json_fence(cleaned)
    for candidate in (cleaned, _between_outer_json_delimiters(cleaned)):
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, (dict, list)):
            return parsed
    fallback = _extract_daily_rows_payload(cleaned)
    if fallback:
        return fallback
    return None


def _strip_json_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _extract_daily_rows_payload(text: str) -> dict[str, Any] | None:
    match = re.search(r'"daily_rows"\s*:\s*\[', text)
    if not match:
        return None
    array_start = text.find("[", match.start())
    array_end = _matching_bracket_end(text, array_start)
    if array_end is None:
        return None
    array_text = text[array_start : array_end + 1]
    try:
        rows = json.loads(array_text)
    except json.JSONDecodeError:
        return None
    if not isinstance(rows, list):
        return None
    payload: dict[str, Any] = {
        "document_type": _extract_json_scalar(text, "document_type") or "logsheet",
        "staff_name": _extract_json_scalar(text, "staff_name"),
        "month_year": _extract_json_scalar(text, "month_year"),
        "daily_rows": rows,
        "warnings": [],
    }
    return payload


def _matching_bracket_end(text: str, start: int) -> int | None:
    if start < 0 or start >= len(text) or text[start] not in "[{":
        return None
    opening = text[start]
    closing = "]" if opening == "[" else "}"
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return index
    return None


def _extract_json_scalar(text: str, key: str) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*(".*?"|null)', text, flags=re.DOTALL)
    if not match:
        return None
    raw_value = match.group(1)
    if raw_value == "null":
        return None
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        return None
    return str(value) if value is not None else None


def _between_outer_json_delimiters(text: str) -> str | None:
    starts = [index for index in (text.find("{"), text.find("[")) if index != -1]
    if not starts:
        return None
    start = min(starts)
    end = max(text.rfind("}"), text.rfind("]"))
    if end <= start:
        return None
    return text[start : end + 1]


def _read_http_error(exc: HTTPError) -> str:
    body = exc.read().decode("utf-8", errors="replace")
    if not body:
        return f"OpenRouter request failed with HTTP {exc.code}."
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return f"OpenRouter HTTP {exc.code}: {body[:500]}"
    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        message = error.get("message") or error.get("code") or str(error)
    else:
        message = str(error or payload)
    return f"OpenRouter HTTP {exc.code}: {message}"


def _config_value(name: str, default: str = "") -> str:
    raw_value = os.getenv(name)
    if raw_value:
        return raw_value.strip()
    env_values = _read_dotenv_values()
    for candidate in (name, name.lower(), name.upper()):
        raw_value = env_values.get(candidate)
        if raw_value:
            return raw_value.strip()
    return default


def _config_int(name: str, default: int) -> int:
    raw_value = _config_value(name)
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return max(1, value)


@lru_cache(maxsize=1)
def _read_dotenv_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for path in _dotenv_candidates():
        if not path.exists() or not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            key, value = _parse_dotenv_line(line)
            if key and key not in values:
                values[key] = value
    return values


def _dotenv_candidates() -> list[Path]:
    module_root = Path(__file__).resolve().parents[1]
    candidates = [Path.cwd() / ".env", module_root / ".env"]
    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            unique.append(resolved)
            seen.add(resolved)
    return unique


def _parse_dotenv_line(line: str) -> tuple[str | None, str]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None, ""
    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        return None, ""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return key, value
