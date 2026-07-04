from __future__ import annotations

import re
from collections import Counter
from difflib import SequenceMatcher
from typing import Any

from .openrouter_ocr import merge_logsheet_daily_rows


DEFAULT_LATE_GRACE_MINUTES = 8
DEFAULT_EARLY_LEAVE_GRACE_MINUTES = 0
DEFAULT_EARLY_IN_GRACE_MINUTES = 0
DEFAULT_OVERTIME_GRACE_MINUTES = 0
MIN_LATE_GRACE_MINUTES = 0
MAX_LATE_GRACE_MINUTES = 14
MIN_NAME_MATCH_SCORE = 0.82
LOW_CONFIDENCE_NAME_SCORE = 0.95


def compare_schedule_to_ocr(
    schedule: dict[str, Any],
    ocr_rows: list[dict[str, Any]],
    *,
    late_grace_minutes: int = DEFAULT_LATE_GRACE_MINUTES,
    early_leave_grace_minutes: int = DEFAULT_EARLY_LEAVE_GRACE_MINUTES,
    count_early_in: bool = False,
    early_in_grace_minutes: int = DEFAULT_EARLY_IN_GRACE_MINUTES,
    count_overtime: bool = False,
    overtime_grace_minutes: int = DEFAULT_OVERTIME_GRACE_MINUTES,
) -> dict[str, Any]:
    """Compare parsed roster entries with OCR first-in/last-out rows."""
    late_grace_minutes = normalize_late_grace_minutes(late_grace_minutes)
    early_leave_grace_minutes = normalize_early_leave_grace_minutes(early_leave_grace_minutes)
    early_in_grace_minutes = normalize_early_in_grace_minutes(early_in_grace_minutes)
    overtime_grace_minutes = normalize_overtime_grace_minutes(overtime_grace_minutes)
    clean_schedule = _normalize_schedule(schedule)
    staff = clean_schedule["staff"]
    entries = clean_schedule["entries"]
    schedule_dates = {entry["date"] for entry in entries if entry.get("date")}
    actual_lookup, unmatched_actuals, matched_staff_names = _build_actual_lookup(ocr_rows, staff, schedule_dates)

    rows: list[dict[str, Any]] = []
    scheduled_keys: set[tuple[str, str]] = set()
    active_staff_names = matched_staff_names if ocr_rows else {entry["staff_name"] for entry in entries}

    for entry in sorted(entries, key=lambda item: (item["date"], item["staff_name"], item.get("schedule_cell", ""))):
        if entry["staff_name"] not in active_staff_names:
            continue
        key = (entry["staff_name"], entry["date"])
        scheduled_keys.add(key)
        rows.append(
            _compare_entry(
                entry,
                actual_lookup.get(key),
                late_grace_minutes,
                early_leave_grace_minutes,
                count_early_in,
                early_in_grace_minutes,
                count_overtime,
                overtime_grace_minutes,
            )
        )

    for key, actual in sorted(actual_lookup.items(), key=lambda item: (item[0][1], item[0][0])):
        if key in scheduled_keys:
            continue
        rows.append(_unscheduled_row(key, actual))

    for actual in unmatched_actuals:
        rows.append(_unmatched_actual_row(actual))

    rows.sort(key=_sort_compare_row)
    status_counts = Counter(row["status"] for row in rows)
    summary = {
        "sheet_name": clean_schedule["sheet_name"],
        "schedule_staff_count": len(staff),
        "schedule_entry_count": len(entries),
        "ocr_row_count": len(ocr_rows),
        "compared_rows": len(rows),
        "matched_rows": sum(1 for row in rows if row.get("has_schedule") and row.get("has_actual")),
        "missing_logsheet_rows": status_counts.get("Missing Logsheet", 0),
        "unscheduled_punch_rows": status_counts.get("Unscheduled Punch", 0),
        "unmatched_name_rows": status_counts.get("Name Not Matched", 0),
        "date_not_matched_rows": status_counts.get("Date Not Matched", 0),
        "name_check_rows": sum(1 for row in rows if "Name Check" in row.get("flags", [])),
        "late_rows": sum(1 for row in rows if "Late" in row.get("status", "")),
        "early_leave_rows": sum(1 for row in rows if "Early Leave" in row.get("status", "")),
        "early_in_rows": sum(1 for row in rows if int(row.get("early_in_minutes") or 0) > 0),
        "overtime_rows": sum(1 for row in rows if int(row.get("overtime_minutes") or 0) > 0),
        "matched_ocr_staff_count": len(matched_staff_names),
        "late_grace_minutes": late_grace_minutes,
        "early_leave_grace_minutes": early_leave_grace_minutes,
        "count_early_in": bool(count_early_in),
        "early_in_grace_minutes": early_in_grace_minutes,
        "count_overtime": bool(count_overtime),
        "overtime_grace_minutes": overtime_grace_minutes,
        "status_counts": dict(status_counts),
    }
    return {"summary": summary, "rows": rows}


def normalize_late_grace_minutes(value: Any) -> int:
    return _normalize_grace_minutes(value, default=DEFAULT_LATE_GRACE_MINUTES)


def normalize_early_leave_grace_minutes(value: Any) -> int:
    return _normalize_grace_minutes(value, default=DEFAULT_EARLY_LEAVE_GRACE_MINUTES)


def normalize_early_in_grace_minutes(value: Any) -> int:
    return _normalize_grace_minutes(value, default=DEFAULT_EARLY_IN_GRACE_MINUTES)


def normalize_overtime_grace_minutes(value: Any) -> int:
    return _normalize_grace_minutes(value, default=DEFAULT_OVERTIME_GRACE_MINUTES)


def _normalize_grace_minutes(value: Any, *, default: int) -> int:
    try:
        minutes = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(MIN_LATE_GRACE_MINUTES, min(minutes, MAX_LATE_GRACE_MINUTES))


def _normalize_schedule(schedule: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(schedule, dict):
        raise ValueError("schedule must be a JSON object")

    staff_rows = schedule.get("staff") or []
    entry_rows = schedule.get("entries") or []
    if not isinstance(staff_rows, list) or not isinstance(entry_rows, list):
        raise ValueError("schedule.staff and schedule.entries must be lists")

    staff_by_name: dict[str, dict[str, Any]] = {}
    for staff in staff_rows:
        if not isinstance(staff, dict):
            continue
        name = _clean_text(staff.get("name"))
        if not name:
            continue
        staff_by_name.setdefault(
            name,
            {
                "name": name,
                "staff_id": _clean_text(staff.get("staff_id")),
                "phone_last4": _normalize_phone(staff.get("phone_last4") or staff.get("mobile")),
                "row": staff.get("row"),
            },
        )

    entries: list[dict[str, Any]] = []
    for entry in entry_rows:
        if not isinstance(entry, dict):
            continue
        staff_name = _clean_text(entry.get("staff_name"))
        date = _normalize_iso_date(entry.get("date"))
        if not staff_name or not date:
            continue
        staff_by_name.setdefault(
            staff_name,
            {
                "name": staff_name,
                "staff_id": _clean_text(entry.get("staff_id")),
                "phone_last4": _normalize_phone(entry.get("phone_last4")),
                "row": entry.get("staff_row"),
            },
        )
        entries.append(
            {
                "staff_name": staff_name,
                "staff_id": _clean_text(entry.get("staff_id")),
                "phone_last4": _normalize_phone(entry.get("phone_last4")),
                "date": date,
                "shift_code": _clean_text(entry.get("shift_code") or entry.get("raw_shift_code")),
                "raw_shift_code": _clean_text(entry.get("raw_shift_code")),
                "scheduled_in": _normalize_time(entry.get("scheduled_in")),
                "scheduled_out": _normalize_time(entry.get("scheduled_out")),
                "scheduled_hours": entry.get("scheduled_hours"),
                "schedule_cell": _clean_text(entry.get("schedule_cell")),
                "resolution_source": _clean_text(entry.get("resolution_source")),
            }
        )

    return {
        "sheet_name": _clean_text(schedule.get("sheet_name")),
        "staff": list(staff_by_name.values()),
        "entries": entries,
    }


def _build_actual_lookup(
    rows: list[dict[str, Any]],
    staff: list[dict[str, Any]],
    schedule_dates: set[str],
) -> tuple[dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]], set[str]]:
    merged_rows = merge_logsheet_daily_rows([row for row in rows if isinstance(row, dict)])
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    unmatched: list[dict[str, Any]] = []
    matched_staff_names: set[str] = set()

    for row in merged_rows:
        actual = _normalize_actual_row(row, schedule_dates)
        match = _confirmed_staff_match(actual.get("assigned_staff_name", ""), staff)
        if not match:
            match = _best_staff_match(actual["ocr_name"], staff)
        if match:
            actual.update(match)
            matched_staff_names.add(match["staff_name"])
        if not actual.get("staff_name") or not actual.get("date"):
            unmatched.append(actual)
            continue

        key = (actual["staff_name"], actual["date"])
        existing = lookup.get(key)
        if not existing:
            lookup[key] = actual
        else:
            _merge_actual(existing, actual)

    return lookup, unmatched, matched_staff_names


def _normalize_actual_row(row: dict[str, Any], schedule_dates: set[str]) -> dict[str, Any]:
    explicit_in = _normalize_time(row.get("in") or row.get("in_time") or row.get("actual_in"))
    explicit_out = _normalize_time(row.get("out") or row.get("out_time") or row.get("actual_out"))
    punch_times = _extract_times([row.get("all_times")])
    use_punch_times = bool(punch_times) and not (not explicit_in and bool(explicit_out))
    actual_in = punch_times[0] if use_punch_times else explicit_in
    actual_out = punch_times[-1] if use_punch_times and len(punch_times) > 1 else explicit_out
    all_times = _extract_times([row.get("all_times"), explicit_in, explicit_out])
    if all_times:
        all_times = sorted(set(all_times), key=_time_minutes_safe)
    return {
        "ocr_name": _clean_text(row.get("ocr_name") or row.get("original_name") or row.get("name") or row.get("staff_name")),
        "assigned_staff_name": _clean_text(row.get("assigned_staff_name")),
        "staff_name": "",
        "date": _normalize_ocr_date(row.get("date"), schedule_dates),
        "ocr_date": _clean_text(row.get("date")),
        "actual_in": actual_in,
        "actual_out": actual_out,
        "source_filename": _clean_text(row.get("source_filename")),
        "source_filenames": [str(item) for item in row.get("source_filenames") or [] if item],
        "all_times": all_times,
        "warnings": [str(item) for item in row.get("warnings") or [] if item],
    }


def _confirmed_staff_match(name: str, staff: list[dict[str, Any]]) -> dict[str, Any] | None:
    query = _normalize_name_key(name)
    if not query:
        return None

    for item in staff:
        candidate_name = _clean_text(item.get("name"))
        if query != _normalize_name_key(candidate_name):
            continue
        return {
            "staff_name": candidate_name,
            "staff_id": item.get("staff_id") or "",
            "phone_last4": item.get("phone_last4") or "",
            "match_score": 1.0,
            "match_type": "confirmed",
        }
    return None


def _best_staff_match(name: str, staff: list[dict[str, Any]]) -> dict[str, Any] | None:
    query = _normalize_name_key(name)
    if not query:
        return None

    candidates: list[dict[str, Any]] = []
    for item in staff:
        candidate_name = _clean_text(item.get("name"))
        candidate_key = _normalize_name_key(candidate_name)
        if not candidate_key:
            continue
        score, match_type = _name_score(query, candidate_key, name, candidate_name)
        candidates.append(
            {
                "staff_name": candidate_name,
                "staff_id": item.get("staff_id") or "",
                "phone_last4": item.get("phone_last4") or "",
                "match_score": round(score, 3),
                "match_type": match_type,
            }
        )

    candidates.sort(key=lambda item: item["match_score"], reverse=True)
    if not candidates or candidates[0]["match_score"] < MIN_NAME_MATCH_SCORE:
        return None
    if len(candidates) > 1 and candidates[0]["match_score"] - candidates[1]["match_score"] < 0.03:
        ambiguous = candidates[0].copy()
        ambiguous["ambiguous_match"] = candidates[1]["staff_name"]
        return ambiguous
    return candidates[0]


def _name_score(query_key: str, candidate_key: str, query_name: str, candidate_name: str) -> tuple[float, str]:
    if query_key == candidate_key:
        return 1.0, "exact"

    query_tokens = set(_name_tokens(query_name))
    candidate_tokens = set(_name_tokens(candidate_name))
    if query_tokens and candidate_tokens:
        if query_tokens <= candidate_tokens or candidate_tokens <= query_tokens:
            return 0.94, "token_subset"
        if query_tokens & candidate_tokens:
            overlap = len(query_tokens & candidate_tokens) / max(len(query_tokens), len(candidate_tokens))
            if overlap >= 0.5:
                return 0.9, "token_overlap"

    if len(query_key) >= 3 and len(candidate_key) >= 3 and (query_key in candidate_key or candidate_key in query_key):
        return 0.92, "contains"

    return SequenceMatcher(None, query_key, candidate_key).ratio(), "fuzzy"


def _merge_actual(target: dict[str, Any], source: dict[str, Any]) -> None:
    times = _extract_times([target.get("all_times"), source.get("all_times"), target.get("actual_in"), target.get("actual_out")])
    if times:
        target["all_times"] = times
        target["actual_in"] = times[0]
        target["actual_out"] = times[-1] if len(times) > 1 else ""
    if source.get("source_filename"):
        filenames = target.setdefault("source_filenames", [])
        if source["source_filename"] not in filenames:
            filenames.append(source["source_filename"])
    for warning in source.get("warnings") or []:
        if warning not in target.setdefault("warnings", []):
            target["warnings"].append(warning)


def _compare_entry(
    entry: dict[str, Any],
    actual: dict[str, Any] | None,
    late_grace_minutes: int,
    early_leave_grace_minutes: int,
    count_early_in: bool,
    early_in_grace_minutes: int,
    count_overtime: bool,
    overtime_grace_minutes: int,
) -> dict[str, Any]:
    row = {
        **entry,
        "ocr_name": actual.get("ocr_name", "") if actual else "",
        "actual_in": actual.get("actual_in", "") if actual else "",
        "actual_out": actual.get("actual_out", "") if actual else "",
        "source_filename": actual.get("source_filename", "") if actual else "",
        "source_filenames": actual.get("source_filenames", []) if actual else [],
        "name_match_score": actual.get("match_score", "") if actual else "",
        "name_match_type": actual.get("match_type", "") if actual else "",
        "raw_late_minutes": "",
        "rounded_late_minutes": "",
        "late_minutes": "",
        "raw_early_in_minutes": 0,
        "early_in_minutes": 0,
        "early_leave_minutes": "",
        "raw_overtime_minutes": 0,
        "overtime_minutes": 0,
        "status": "",
        "flags": [],
        "notes": "",
        "has_schedule": True,
        "has_actual": bool(actual),
    }

    if not actual:
        row["status"] = "Missing Logsheet"
        row["notes"] = "Roster 有排班，但找不到同員工/日期的 OCR logsheet row。"
        return row

    _append_name_flags(row, actual)

    scheduled_in = _time_minutes(entry.get("scheduled_in"))
    scheduled_out = _time_minutes(entry.get("scheduled_out"))
    actual_in = _time_minutes(actual.get("actual_in"))
    actual_out = _time_minutes(actual.get("actual_out"))

    if actual_in is None:
        row["status"] = "Missing In"
    if actual_out is None:
        row["status"] = "Missing Out" if not row["status"] else "Missing In/Out"

    if scheduled_in is None or scheduled_out is None:
        row["flags"].append("Schedule Time Missing")
        if not row["status"]:
            row["status"] = "Matched"
        return row

    if scheduled_out <= scheduled_in:
        scheduled_out += 24 * 60
    if actual_out is not None and actual_in is not None and actual_out < actual_in:
        actual_out += 24 * 60

    if scheduled_in is not None and actual_in is not None:
        raw_early_in = max(0, scheduled_in - actual_in)
        raw_late = max(0, actual_in - scheduled_in)
        rounded_in = _round_oil_street_in_minutes(actual_in, late_grace_minutes)
        charged_late = max(0, rounded_in - scheduled_in)
        row["raw_early_in_minutes"] = raw_early_in
        row["early_in_minutes"] = (
            _round_down_to_block(raw_early_in)
            if count_early_in and raw_early_in > early_in_grace_minutes
            else 0
        )
        row["raw_late_minutes"] = raw_late
        row["rounded_late_minutes"] = charged_late
        row["late_minutes"] = charged_late

    if scheduled_out is not None and actual_out is not None:
        diff = scheduled_out - actual_out
        if diff > 0:
            row["early_leave_minutes"] = 0 if diff <= early_leave_grace_minutes else _round_up_to_block(diff)
            row["overtime_minutes"] = 0
        else:
            raw_overtime = -diff
            row["early_leave_minutes"] = 0
            row["raw_overtime_minutes"] = raw_overtime
            row["overtime_minutes"] = (
                _round_down_to_block(raw_overtime)
                if count_overtime and raw_overtime > overtime_grace_minutes
                else 0
            )

    if not row["status"]:
        late = int(row["late_minutes"] or 0)
        early = int(row["early_leave_minutes"] or 0)
        if late and early:
            row["status"] = "Late + Early Leave"
        elif late:
            row["status"] = "Late"
        elif early:
            row["status"] = "Early Leave"
        elif actual_in is not None and actual_in < scheduled_in:
            row["status"] = "Early In"
        else:
            row["status"] = "Matched"
    return row


def _append_name_flags(row: dict[str, Any], actual: dict[str, Any]) -> None:
    score = actual.get("match_score")
    if actual.get("ambiguous_match"):
        row["flags"].append("Name Check")
        row["notes"] = f"OCR 姓名配對不唯一；也接近 {actual['ambiguous_match']}。"
        return
    if isinstance(score, (int, float)) and score < LOW_CONFIDENCE_NAME_SCORE:
        row["flags"].append("Name Check")
        row["notes"] = "OCR 姓名是部分或模糊配對，匯出前請覆核。"


def _unscheduled_row(key: tuple[str, str], actual: dict[str, Any]) -> dict[str, Any]:
    return {
        "staff_name": key[0],
        "staff_id": actual.get("staff_id", ""),
        "phone_last4": actual.get("phone_last4", ""),
        "date": key[1],
        "shift_code": "",
        "raw_shift_code": "",
        "scheduled_in": "",
        "scheduled_out": "",
        "scheduled_hours": "",
        "schedule_cell": "",
        "resolution_source": "",
        "ocr_name": actual.get("ocr_name", ""),
        "actual_in": actual.get("actual_in", ""),
        "actual_out": actual.get("actual_out", ""),
        "source_filename": actual.get("source_filename", ""),
        "source_filenames": actual.get("source_filenames", []),
        "name_match_score": actual.get("match_score", ""),
        "name_match_type": actual.get("match_type", ""),
        "raw_late_minutes": "",
        "rounded_late_minutes": "",
        "late_minutes": "",
        "raw_early_in_minutes": 0,
        "early_in_minutes": 0,
        "early_leave_minutes": "",
        "raw_overtime_minutes": 0,
        "overtime_minutes": 0,
        "status": "Unscheduled Punch",
        "flags": ["Name Check"] if actual.get("match_score", 1) < LOW_CONFIDENCE_NAME_SCORE else [],
        "notes": "OCR 有打卡紀錄，但 roster 同員工/日期沒有排班。",
        "has_schedule": False,
        "has_actual": True,
    }


def _unmatched_actual_row(actual: dict[str, Any]) -> dict[str, Any]:
    status = "Date Not Matched" if actual.get("staff_name") and not actual.get("date") else "Name Not Matched"
    note = "OCR 日期無法對齊到已解析 roster。" if status == "Date Not Matched" else "OCR 員工姓名無法配對到已解析 roster。"
    return {
        "staff_name": actual.get("staff_name", ""),
        "staff_id": actual.get("staff_id", ""),
        "phone_last4": actual.get("phone_last4", ""),
        "date": actual.get("date", "") or actual.get("ocr_date", ""),
        "shift_code": "",
        "raw_shift_code": "",
        "scheduled_in": "",
        "scheduled_out": "",
        "scheduled_hours": "",
        "schedule_cell": "",
        "resolution_source": "",
        "ocr_name": actual.get("ocr_name", ""),
        "actual_in": actual.get("actual_in", ""),
        "actual_out": actual.get("actual_out", ""),
        "source_filename": actual.get("source_filename", ""),
        "source_filenames": actual.get("source_filenames", []),
        "name_match_score": actual.get("match_score", ""),
        "name_match_type": actual.get("match_type", ""),
        "raw_late_minutes": "",
        "rounded_late_minutes": "",
        "late_minutes": "",
        "raw_early_in_minutes": 0,
        "early_in_minutes": 0,
        "early_leave_minutes": "",
        "raw_overtime_minutes": 0,
        "overtime_minutes": 0,
        "status": status,
        "flags": ["Name Check"] if status == "Name Not Matched" else [],
        "notes": note,
        "has_schedule": False,
        "has_actual": True,
    }


def _normalize_ocr_date(value: Any, schedule_dates: set[str]) -> str:
    iso = _normalize_iso_date(value)
    if iso:
        return _align_iso_to_schedule_date(iso, schedule_dates) or iso
    text = _clean_text(value)
    if not text:
        return ""

    day_match = re.fullmatch(r"(?:day\s*)?([0-3]?\d)", text, flags=re.IGNORECASE)
    if day_match:
        return _date_for_day(int(day_match.group(1)), schedule_dates)

    numeric = re.fullmatch(r"([0-3]?\d)[./-]([01]?\d)(?:[./-](\d{2,4}))?", text)
    if numeric:
        day = int(numeric.group(1))
        month = int(numeric.group(2))
        year = numeric.group(3)
        return (
            _date_for_day_month(day, month, year, schedule_dates)
            or _date_for_day_month(day, month, None, schedule_dates)
            or _date_for_day(day, schedule_dates)
        )

    text_match = re.search(r"\b([0-3]?\d)(?:st|nd|rd|th)?\b", text, flags=re.IGNORECASE)
    if text_match:
        return _date_for_day(int(text_match.group(1)), schedule_dates)
    return ""


def _align_iso_to_schedule_date(iso: str, schedule_dates: set[str]) -> str:
    if iso in schedule_dates:
        return iso
    _, month, day = iso.split("-")
    return _date_for_day_month(int(day), int(month), None, schedule_dates) or _date_for_day(int(day), schedule_dates)


def _normalize_iso_date(value: Any) -> str:
    text = _clean_text(value)
    if not text:
        return ""
    match = re.fullmatch(r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})", text)
    if not match:
        return ""
    year, month, day = (int(part) for part in match.groups())
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return ""
    return f"{year:04d}-{month:02d}-{day:02d}"


def _date_for_day(day: int, schedule_dates: set[str]) -> str:
    matches = [date for date in schedule_dates if date.endswith(f"-{day:02d}")]
    return matches[0] if len(matches) == 1 else ""


def _date_for_day_month(day: int, month: int, year: str | None, schedule_dates: set[str]) -> str:
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return ""
    matches = []
    for date in schedule_dates:
        date_year, date_month, date_day = date.split("-")
        if int(date_month) != month or int(date_day) != day:
            continue
        if year:
            full_year = int(year) + 2000 if len(year) == 2 else int(year)
            if int(date_year) != full_year:
                continue
        matches.append(date)
    return matches[0] if len(matches) == 1 else ""


def _normalize_time(value: Any) -> str:
    text = _clean_text(value)
    if not text:
        return ""
    match = re.search(r"\b([01]?\d|2[0-3])[:.：]([0-5]\d)\b", text)
    if not match:
        return ""
    return f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"


def _extract_times(values: list[Any]) -> list[str]:
    times: list[str] = []
    for value in values:
        if value is None or value == "":
            continue
        if isinstance(value, list):
            times.extend(_extract_times(value))
            continue
        for match in re.findall(r"\b(?:[01]?\d|2[0-3])[:.：][0-5]\d\b", str(value)):
            normalized = _normalize_time(match)
            if normalized:
                times.append(normalized)
    return sorted(set(times), key=_time_minutes_safe)


def _time_minutes(value: Any) -> int | None:
    normalized = _normalize_time(value)
    if not normalized:
        return None
    hour, minute = normalized.split(":")
    return int(hour) * 60 + int(minute)


def _time_minutes_safe(value: Any) -> int:
    minutes = _time_minutes(value)
    return minutes if minutes is not None else 24 * 60


def _round_oil_street_in_minutes(in_minutes: int, grace_minutes: int) -> int:
    block_minutes = 15
    remainder = in_minutes % block_minutes
    if remainder == 0 or remainder <= grace_minutes:
        return in_minutes - remainder
    return in_minutes + (block_minutes - remainder)


def _round_up_to_block(minutes: int, block_minutes: int = 15) -> int:
    if minutes <= 0:
        return 0
    return ((minutes + block_minutes - 1) // block_minutes) * block_minutes


def _round_down_to_block(minutes: int, block_minutes: int = 15) -> int:
    if minutes <= 0:
        return 0
    return (minutes // block_minutes) * block_minutes


def _normalize_name_key(value: Any) -> str:
    return re.sub(r"[\W_]+", "", str(value or "").casefold(), flags=re.UNICODE)


def _name_tokens(value: Any) -> list[str]:
    return [token for token in re.split(r"[\W_]+", str(value or "").casefold()) if token]


def _normalize_phone(value: Any) -> str:
    digits = re.sub(r"\D+", "", str(value or ""))
    return digits[-4:] if len(digits) > 4 else digits


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _sort_compare_row(row: dict[str, Any]) -> tuple[str, str, int, str]:
    status_order = {
        "Late + Early Leave": 0,
        "Late": 1,
        "Early Leave": 1,
        "Missing In/Out": 2,
        "Missing In": 2,
        "Missing Out": 2,
        "Missing Logsheet": 3,
        "Unscheduled Punch": 4,
        "Name Not Matched": 5,
        "Date Not Matched": 5,
        "Early In": 6,
        "Matched": 7,
    }
    return (
        str(row.get("date") or ""),
        str(row.get("staff_name") or row.get("ocr_name") or ""),
        status_order.get(str(row.get("status") or ""), 9),
        str(row.get("schedule_cell") or ""),
    )
