from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from openpyxl.utils.datetime import from_excel


TIME_TOKEN_RE = re.compile(r"\b\d{1,2}(?:(?::|\.)?\d{2})?\s*(?:am|pm)?\b", re.IGNORECASE)


def normalize_time(value: Any) -> str | None:
    minutes = parse_time_minutes(value)
    if minutes is None:
        return None
    return format_time_minutes(minutes)


def parse_time_minutes(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip().lower().replace(".", ":")
    if not text:
        return None
    match = re.fullmatch(r"(\d{1,2})(?::?(\d{2}))?\s*(am|pm)?", text, re.IGNORECASE)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or "0")
    suffix = (match.group(3) or "").lower()
    if minute > 59:
        return None
    if suffix == "am":
        if hour == 12:
            hour = 0
        elif hour > 12:
            return None
    elif suffix == "pm":
        if hour == 12:
            hour = 12
        elif 1 <= hour <= 11:
            hour += 12
        else:
            return None
    elif hour > 23:
        return None
    return hour * 60 + minute


def format_time_minutes(minutes: int) -> str:
    minutes = int(minutes) % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        return excel_serial_to_date(value)
    text = str(value).strip()
    if not text:
        return None
    for pattern in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d-%m-%y",
        "%d/%m",
        "%d-%m",
    ):
        try:
            parsed = datetime.strptime(text, pattern)
            if pattern in {"%d/%m", "%d-%m"}:
                parsed = parsed.replace(year=datetime.today().year)
            return parsed.date()
        except ValueError:
            continue
    return None


def coerce_excel_date(value: Any) -> date | None:
    return parse_date(value)


def excel_serial_to_date(value: Any) -> date | None:
    if not isinstance(value, (int, float)) or value <= 0:
        return None
    try:
        return from_excel(value).date()
    except (TypeError, ValueError, OverflowError):
        return None


def calculate_hours(start: Any, end: Any) -> float | None:
    start_minutes = parse_time_minutes(start)
    end_minutes = parse_time_minutes(end)
    if start_minutes is None or end_minutes is None:
        return None
    if end_minutes <= start_minutes:
        end_minutes += 24 * 60
    return round((end_minutes - start_minutes) / 60, 2)


def coerce_hours_value(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0 or number > 24:
        return None
    return round(number, 2)


def parse_time_range(text: Any) -> dict[str, Any] | None:
    source = str(text or "").strip()
    if not source:
        return None
    tokens = [token.strip() for token in TIME_TOKEN_RE.findall(source) if re.search(r"\d", token)]
    if len(tokens) < 2:
        return None

    duration_hours = parse_duration_hours(source)
    best: tuple[tuple[float, int, int, int, int, int], int, int, int] | None = None
    for start_index, start_token in enumerate(tokens[:-1]):
        start_candidates = time_token_candidates(start_token)
        if not start_candidates:
            continue
        for end_index, end_token in enumerate(tokens[start_index + 1 :], start=start_index + 1):
            end_candidates = time_token_candidates(end_token)
            if not end_candidates:
                continue
            for start_minutes in start_candidates:
                for end_minutes in end_candidates:
                    delta = end_minutes - start_minutes
                    overnight = 0
                    if delta <= 0:
                        delta += 24 * 60
                        overnight = 1
                    if delta > 20 * 60:
                        continue
                    early_start = 1 if start_minutes < 6 * 60 else 0
                    score = abs(delta / 60 - duration_hours) if duration_hours is not None else 0
                    specificity = _time_token_specificity(start_token) + _time_token_specificity(end_token)
                    token_distance = end_index - start_index
                    # Prefer duration match, explicit time tokens, earlier nearby tokens, then ordinary day shifts.
                    sort_key = (score, specificity, start_index, token_distance, overnight + early_start, delta)
                    if best is None or sort_key < best[0]:
                        best = (sort_key, start_minutes, end_minutes, delta)

    if best is None:
        return None
    _, start_minutes, end_minutes, delta = best
    return {
        "start": format_time_minutes(start_minutes),
        "end": format_time_minutes(end_minutes),
        "hours": round(delta / 60, 2),
        "source_text": source,
    }


def parse_duration_hours(text: str) -> float | None:
    match = re.search(r"\((\d+(?:\.\d+)?)\s*(?:hr|hrs|hour|hours)\b", text, re.IGNORECASE)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _time_token_specificity(token: str) -> int:
    text = str(token or "").strip().lower()
    score = 0
    if ":" not in text and "." not in text:
        score += 1
    if "am" not in text and "pm" not in text:
        score += 1
    return score


def time_token_candidates(token: str) -> list[int]:
    text = str(token or "").strip().lower().replace(".", ":")
    match = re.fullmatch(r"(\d{1,2})(?::?(\d{2}))?\s*(am|pm)?", text)
    if not match:
        return []
    hour = int(match.group(1))
    minute = int(match.group(2) or "0")
    suffix = match.group(3)
    if minute > 59:
        return []

    candidates: list[int] = []
    if suffix == "am":
        if hour == 12:
            candidates.append(minute)
        elif 1 <= hour <= 11:
            candidates.append(hour * 60 + minute)
            candidates.append((hour + 12) * 60 + minute)
    elif suffix == "pm":
        if hour == 12:
            candidates.append(12 * 60 + minute)
        elif 1 <= hour <= 11:
            candidates.append((hour + 12) * 60 + minute)
            candidates.append(hour * 60 + minute)
    elif 0 <= hour <= 23:
        candidates.append(hour * 60 + minute)
        if 1 <= hour <= 11:
            candidates.append((hour + 12) * 60 + minute)
    return list(dict.fromkeys(candidates))
