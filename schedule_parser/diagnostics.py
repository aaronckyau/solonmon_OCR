from __future__ import annotations

from .schema import ParsedScheduleEntry, ParserError, ParserWarning


def collect_unknown_shift_codes(entries: list[ParsedScheduleEntry]) -> list[str]:
    codes = []
    for entry in entries:
        if "UNKNOWN_SHIFT_CODE" not in entry.warnings:
            continue
        if entry.shift_code and entry.shift_code not in codes:
            codes.append(entry.shift_code)
    return codes


def build_parse_diagnostics(
    *,
    selected_sheet_score: float | int | None,
    layout_confidence: float,
    header_row: int | None,
    staff_row_range: dict[str, int | None],
    date_count: int,
    staff_count: int,
    entry_count: int,
    entries: list[ParsedScheduleEntry],
    warnings: list[ParserWarning],
    errors: list[ParserError],
    ai_used: bool,
) -> dict:
    unknown_shift_codes = collect_unknown_shift_codes(entries)
    return {
        "selected_sheet_score": selected_sheet_score,
        "layout_confidence": layout_confidence,
        "header_row": header_row,
        "staff_row_range": staff_row_range,
        "date_count": date_count,
        "staff_count": staff_count,
        "entry_count": entry_count,
        "unknown_shift_codes": unknown_shift_codes,
        "ai_used": ai_used,
        "warning_count": len(warnings) + sum(len(entry.warnings) for entry in entries),
        "error_count": len(errors),
    }
