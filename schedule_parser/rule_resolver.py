from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from .schema import ParsedShiftOption, ParsedShiftTime
from .time_utils import calculate_hours, coerce_hours_value, normalize_time, parse_date, parse_time_minutes, parse_time_range


SHIFT_CODE_RE = re.compile(r"^[A-Z](?:\d)?$", re.IGNORECASE)
OR_SHIFT_CODE_RE = re.compile(r"^[A-Z](?:\d)?(?:/[A-Z](?:\d)?)+$", re.IGNORECASE)
SHIFT_DEFINITION_CODE_RE = re.compile(r"^[A-Z](?:\d)?(?:/[A-Z](?:\d)?)*$", re.IGNORECASE)


class ShiftRuleAIResolver:
    def resolve(self, compact_context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


def normalize_shift_code(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "").strip().upper())


def is_or_shift_code(raw_code: Any) -> bool:
    return OR_SHIFT_CODE_RE.fullmatch(normalize_shift_code(raw_code)) is not None


def split_or_shift_code(raw_code: Any) -> list[str]:
    clean = normalize_shift_code(raw_code)
    if not is_or_shift_code(clean):
        return []
    return [part for part in clean.split("/") if part]


def parse_direct_time_cell(value: Any, adjacent_hours: Any = None) -> dict[str, Any] | None:
    parsed = parse_time_range(value)
    if not parsed:
        return None
    hours = coerce_hours_value(adjacent_hours)
    if hours is not None:
        parsed["hours"] = hours
    return {
        "shift_code": "",
        "scheduled_in": parsed["start"],
        "scheduled_out": parsed["end"],
        "scheduled_hours": parsed["hours"],
        "resolution_source": "direct_time",
        "source_text": parsed["source_text"],
        "warnings": [],
    }


def parse_legend_from_sheet(ws_formula, ws_values, header_row: int, staff_end_row: int | None) -> dict[str, ParsedShiftTime]:
    shift_times: dict[str, ParsedShiftTime] = {}
    current_section = "default"
    current_dates: list[str] = []
    start_row = max((staff_end_row or header_row) + 1, header_row + 1)
    variant_counts: dict[str, int] = {}

    for row in range(start_row, ws_values.max_row + 1):
        cells = [ws_values.cell(row, col) for col in range(1, ws_values.max_column + 1)]
        non_empty = [cell for cell in cells if cell.value not in (None, "")]
        if not non_empty:
            continue
        row_text = " ".join(str(cell.value).strip() for cell in non_empty if str(cell.value).strip())
        applies_to, dates = section_applies_to(row_text)
        if is_section_header(row_text):
            current_section = applies_to
            current_dates = dates
            continue

        definitions = _shift_definitions_from_row(non_empty, current_section, current_dates)
        for definition in definitions:
            code = definition.code
            key = code
            if key in shift_times:
                variant_counts[code] = variant_counts.get(code, 1) + 1
                key = f"{code}@{definition.applies_to or 'default'}"
                if key in shift_times:
                    key = f"{key}:{variant_counts[code]}"
            shift_times[key] = definition
    return shift_times


def resolve_shift_code(raw_code: Any, date_value: str | date | None, shift_times: dict[str, ParsedShiftTime]) -> dict[str, Any]:
    inline = parse_inline_override(raw_code, shift_times)
    if inline:
        return inline

    clean = normalize_shift_code(raw_code)
    if not clean:
        return _unresolved(clean, "EMPTY_SHIFT_CODE")

    if is_or_shift_code(clean):
        return resolve_or_shift_code(clean, date_value, shift_times)

    shift = _best_shift_for_date(clean, date_value, shift_times)
    if shift:
        return _resolved(clean, shift, "legend", [])
    return _unresolved(clean, "UNKNOWN_SHIFT_CODE", f"Unknown shift code: {clean}")


def resolve_or_shift_code(
    raw_code: Any,
    date_value: str | date | None,
    shift_times: dict[str, ParsedShiftTime],
) -> dict[str, Any]:
    clean = normalize_shift_code(raw_code)
    direct_shift = _best_shift_for_date(clean, date_value, shift_times)
    if direct_shift:
        return _resolved(clean, direct_shift, "legend_combined_code", [], [_option_from_shift(direct_shift)])

    parts = split_or_shift_code(clean)
    if not parts:
        return _unresolved(clean, "AMBIGUOUS_SHIFT_CODE", f"Could not parse slash shift code: {clean}")

    resolved_parts = [(part, _best_shift_for_date(part, date_value, shift_times)) for part in parts]
    known_options = [_option_from_shift(shift, code=part) for part, shift in resolved_parts if shift is not None]
    unknown_parts = [part for part, shift in resolved_parts if shift is None]
    if unknown_parts:
        message = f"OR shift code {clean} contains unknown part {', '.join(unknown_parts)}"
        return {
            "shift_code": clean,
            "scheduled_in": "",
            "scheduled_out": "",
            "scheduled_hours": None,
            "resolution_source": "unresolved_or_options",
            "source_text": "",
            "warnings": ["UNKNOWN_OR_SHIFT_PART"],
            "message": message,
            "shift_options": known_options,
        }

    if not known_options:
        return _unresolved(clean, "UNKNOWN_SHIFT_CODE", f"Unknown shift code: {clean}")

    first = known_options[0]
    if all(_same_option(first, option) for option in known_options[1:]):
        return {
            "shift_code": clean,
            "scheduled_in": first.start,
            "scheduled_out": first.end,
            "scheduled_hours": first.hours,
            "resolution_source": "or_equivalent",
            "source_text": "",
            "warnings": [],
            "shift_options": known_options,
        }

    return {
        "shift_code": clean,
        "scheduled_in": "",
        "scheduled_out": "",
        "scheduled_hours": None,
        "resolution_source": "or_options",
        "source_text": "",
        "warnings": [],
        "shift_options": known_options,
    }


def parse_inline_override(raw_code: Any, base_shift_times: dict[str, ParsedShiftTime]) -> dict[str, Any] | None:
    text = str(raw_code or "").strip()
    if not text:
        return None
    match = re.match(r"^\s*([A-Z]\d?)\s*(?:\((.+)\)|(.+))\s*$", text, re.IGNORECASE)
    if not match:
        return None
    base_code = normalize_shift_code(match.group(1))
    override_text = (match.group(2) or match.group(3) or "").strip()
    if not override_text or override_text.startswith("/"):
        return None
    if not re.search(r"\d", override_text) and not re.search(r"\b(?:till|til|until|to)\b", override_text, re.IGNORECASE):
        return None

    base_shift = _best_shift_for_date(base_code, None, base_shift_times)
    range_override = parse_time_range(override_text)
    start = range_override.get("start") if range_override else None
    end = range_override.get("end") if range_override else None

    till_match = re.search(r"\b(?:till|til|until|to)\s*(\d{1,2}(?:(?::|\.)?\d{2})?\s*(?:am|pm)?)", override_text, re.IGNORECASE)
    if till_match:
        start = base_shift.start if base_shift else None
        end = normalize_time(till_match.group(1))

    if not start and base_shift:
        start = base_shift.start
    if not end and base_shift:
        end = base_shift.end
    if not start or not end:
        return None
    hours = calculate_hours(start, end)
    return {
        "shift_code": base_code,
        "scheduled_in": start,
        "scheduled_out": end,
        "scheduled_hours": hours,
        "resolution_source": "inline_override",
        "source_text": text,
        "warnings": [],
    }


def section_applies_to(text: str) -> tuple[str, list[str]]:
    lower = text.lower()
    dates = _extract_specific_dates(text)
    if "christmas eve" in lower or dates and "for " in lower:
        return "specific", dates
    if "public holiday" in lower or "holiday" in lower or "sunday" in lower:
        return "holidays", dates
    if "mon" in lower:
        return "mondays", dates
    if "tue" in lower or "normal working" in lower or "normal" in lower:
        return "default", dates
    return "default", dates


def is_section_header(text: str) -> bool:
    lower = text.strip().lower().rstrip(":")
    return (
        lower.startswith("for ")
        or lower in {"mon", "monday", "mondays", "sun", "sunday", "public holidays", "public holiday"}
        or "tue - sun" in lower
        or "tue-sun" in lower
        or "christmas eve" in lower
    )


def _shift_definitions_from_row(cells: list[Any], applies_to: str, specific_dates: list[str]) -> list[ParsedShiftTime]:
    definitions: list[ParsedShiftTime] = []
    row_text = " ".join(str(cell.value).strip() for cell in cells if str(cell.value).strip())
    first_text = str(cells[0].value or "").strip()

    if SHIFT_DEFINITION_CODE_RE.fullmatch(normalize_shift_code(first_text)):
        parsed = parse_time_range(row_text)
        if parsed:
            definitions.append(
                ParsedShiftTime(
                    code=normalize_shift_code(first_text),
                    start=parsed["start"],
                    end=parsed["end"],
                    hours=parsed["hours"],
                    source="legend",
                    source_text=row_text,
                    source_cell=cells[0].coordinate,
                    applies_to=applies_to,
                    specific_dates=specific_dates,
                )
            )
            return definitions

    for cell in cells:
        text = str(cell.value or "").strip()
        definition = _parse_shift_definition_text(text, cell.coordinate, applies_to, specific_dates)
        if definition:
            definitions.append(definition)
    if not definitions:
        definition = _parse_shift_definition_text(row_text, cells[0].coordinate, applies_to, specific_dates)
        if definition:
            definitions.append(definition)
    return definitions


def _parse_shift_definition_text(text: str, coordinate: str, applies_to: str, specific_dates: list[str]) -> ParsedShiftTime | None:
    match = re.match(r"^\s*([A-Z]\d?(?:/[A-Z]\d?)*)\s*[.:\-]?\s*(.+)$", text, re.IGNORECASE)
    if not match:
        return None
    code = normalize_shift_code(match.group(1))
    body = match.group(2).strip()
    parsed = parse_time_range(body)
    if not parsed:
        return None
    return ParsedShiftTime(
        code=code,
        start=parsed["start"],
        end=parsed["end"],
        hours=parsed["hours"],
        source="legend",
        source_text=text.strip(),
        source_cell=coordinate,
        applies_to=applies_to,
        specific_dates=specific_dates,
    )


def _best_shift_for_date(code: str, date_value: str | date | None, shift_times: dict[str, ParsedShiftTime]) -> ParsedShiftTime | None:
    target_code = normalize_shift_code(code)
    variants = [shift for shift in shift_times.values() if normalize_shift_code(shift.code) == target_code]
    if not variants:
        return None
    target_date = parse_date(date_value) if not isinstance(date_value, date) else date_value
    if target_date:
        for variant in variants:
            if (variant.applies_to or "").lower() == "specific" and _date_matches(target_date, variant.specific_dates):
                return variant
        if target_date.weekday() == 6:
            for variant in variants:
                if (variant.applies_to or "").lower() == "holidays":
                    return variant
        if target_date.weekday() == 0:
            for variant in variants:
                if (variant.applies_to or "").lower() == "mondays":
                    return variant
    for variant in variants:
        if (variant.applies_to or "default").lower() == "default":
            return variant
    return variants[0]


def _resolved(
    clean_code: str,
    shift: ParsedShiftTime,
    source: str,
    warnings: list[str],
    shift_options: list[ParsedShiftOption] | None = None,
) -> dict[str, Any]:
    return {
        "shift_code": clean_code,
        "scheduled_in": shift.start,
        "scheduled_out": shift.end,
        "scheduled_hours": shift.hours if shift.hours is not None else calculate_hours(shift.start, shift.end),
        "resolution_source": source,
        "source_text": shift.source_text,
        "warnings": warnings,
        "shift_options": shift_options or [],
    }


def _unresolved(
    clean_code: str,
    warning_code: str,
    message: str | None = None,
    alternatives: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result = {
        "shift_code": clean_code,
        "scheduled_in": "",
        "scheduled_out": "",
        "scheduled_hours": None,
        "resolution_source": "unresolved",
        "source_text": "",
        "warnings": [warning_code],
    }
    if message:
        result["message"] = message
    if alternatives:
        result["alternatives"] = alternatives
    return result


def _same_shift(left: ParsedShiftTime, right: ParsedShiftTime | None) -> bool:
    if right is None:
        return False
    return left.start == right.start and left.end == right.end and left.hours == right.hours


def _option_from_shift(shift: ParsedShiftTime, code: str | None = None) -> ParsedShiftOption:
    hours = shift.hours if shift.hours is not None else calculate_hours(shift.start, shift.end)
    return ParsedShiftOption(
        code=code or shift.code,
        start=shift.start,
        end=shift.end,
        hours=hours,
        source=shift.source,
        source_cell=shift.source_cell,
        source_text=shift.source_text,
    )


def _same_option(left: ParsedShiftOption, right: ParsedShiftOption) -> bool:
    return left.start == right.start and left.end == right.end and left.hours == right.hours


def _shift_to_dict(shift: ParsedShiftTime) -> dict[str, Any]:
    return {
        "code": shift.code,
        "start": shift.start,
        "end": shift.end,
        "hours": shift.hours,
        "applies_to": shift.applies_to,
    }


def _date_matches(target: date, specific_dates: list[str]) -> bool:
    target_iso = target.isoformat()
    target_md = target.strftime("%m-%d")
    for item in specific_dates:
        text = str(item).strip()
        if text in {target_iso, target_md}:
            return True
    return False


def _extract_specific_dates(text: str) -> list[str]:
    pieces = re.findall(r"\d{1,2}\s*(?:/\s*\d{1,2})?", text)
    if not pieces:
        return []
    last_month = None
    for piece in reversed(pieces):
        if "/" not in piece:
            continue
        _, month_text = piece.split("/", 1)
        try:
            last_month = int(month_text.strip())
            break
        except ValueError:
            continue
    dates = []
    for piece in pieces:
        if "/" in piece:
            day_text, month_text = piece.split("/", 1)
            try:
                day = int(day_text.strip())
                month = int(month_text.strip())
            except ValueError:
                continue
        elif last_month is not None:
            try:
                day = int(piece.strip())
                month = last_month
            except ValueError:
                continue
        else:
            continue
        if 1 <= month <= 12 and 1 <= day <= 31:
            value = f"{month:02d}-{day:02d}"
            if value not in dates:
                dates.append(value)
    return dates
