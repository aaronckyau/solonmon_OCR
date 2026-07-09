from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


DIRECT_TIME_WITH_HOURS_COLUMNS = "direct_time_with_hours_columns"
SHIFT_CODE_MATRIX_WITH_LEGEND = "shift_code_matrix_with_legend"
UNKNOWN = "unknown"
FIRST_SHEET_SELECTED_OVER_HIGHER_SCORING_SHEET = "FIRST_SHEET_SELECTED_OVER_HIGHER_SCORING_SHEET"


@dataclass(slots=True)
class LayoutDetectionResult:
    sheet_name: str | None
    header_row: int | None
    layout_type: str
    likely_date_columns: list[dict[str, Any]] = field(default_factory=list)
    likely_staff_row_range: dict[str, int | None] = field(default_factory=dict)
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


TIME_RANGE_RE = re.compile(r"\d{1,2}(?::|\.)\d{2}\s*[-–]\s*\d{1,2}(?::|\.)\d{2}", re.IGNORECASE)
SHIFT_CODE_RE = re.compile(r"^[A-Z](?:\d)?(?:/[A-Z](?:\d)?)*$", re.IGNORECASE)


def detect_schedule_layout(inspected_workbook: dict[str, Any]) -> LayoutDetectionResult:
    candidates: list[LayoutDetectionResult] = []
    sheets = inspected_workbook.get("sheets", [])
    for sheet_index, sheet in enumerate(sheets):
        header_options = sheet.get("candidate_header_rows") or []
        if not header_options:
            candidates.append(
                LayoutDetectionResult(
                    sheet_name=sheet.get("sheet_name"),
                    header_row=None,
                    layout_type=UNKNOWN,
                    confidence=0.05,
                    warnings=["NO_HEADER_ROW"],
                    diagnostics={
                        "sheet_index": sheet_index,
                        "sheet_score": _sheet_base_score(sheet),
                        "reason": "No candidate header row",
                    },
                )
            )
            continue
        for header in header_options:
            header_row = header["row"]
            date_columns = [
                col for col in sheet.get("candidate_date_columns", []) if col.get("row") == header_row
            ]
            candidate = _score_layout_for_header(sheet, header, date_columns)
            candidate.diagnostics["sheet_index"] = sheet_index
            candidates.append(candidate)

    if not candidates:
        return LayoutDetectionResult(
            sheet_name=None,
            header_row=None,
            layout_type=UNKNOWN,
            confidence=0.0,
            warnings=["NO_SHEETS"],
        )
    best_candidate = max(candidates, key=_candidate_score)
    first_sheet_name = sheets[0].get("sheet_name") if sheets else None
    first_sheet_candidates = [
        candidate for candidate in candidates if candidate.sheet_name == first_sheet_name and _is_usable_candidate(candidate)
    ]
    if not first_sheet_candidates:
        return best_candidate

    selected = max(first_sheet_candidates, key=_candidate_score)
    selected.diagnostics["selection_reason"] = "first_sheet_priority"
    selected.diagnostics["selected_first_sheet"] = selected.sheet_name
    if best_candidate.sheet_name != selected.sheet_name and _candidate_score(best_candidate) > _candidate_score(selected):
        if FIRST_SHEET_SELECTED_OVER_HIGHER_SCORING_SHEET not in selected.warnings:
            selected.warnings.append(FIRST_SHEET_SELECTED_OVER_HIGHER_SCORING_SHEET)
        selected.diagnostics["ignored_higher_scoring_sheet"] = {
            "sheet_name": best_candidate.sheet_name,
            "header_row": best_candidate.header_row,
            "layout_type": best_candidate.layout_type,
            "overall_score": best_candidate.diagnostics.get("overall_score"),
        }
    return selected


def _score_layout_for_header(sheet: dict[str, Any], header: dict[str, Any], date_columns: list[dict[str, Any]]) -> LayoutDetectionResult:
    header_row = header["row"]
    sample_rows = sheet.get("first_20_rows") or []
    date_indices = [int(item["column"]) for item in date_columns]
    gaps = [right - left for left, right in zip(date_indices, date_indices[1:])]
    continuous_score = gaps.count(1) / len(gaps) if gaps else 0
    every_second_score = gaps.count(2) / len(gaps) if gaps else 0
    staff_range = _likely_staff_range(sample_rows, header_row, header)
    direct_count, adjacent_hours_count, code_count = _sample_schedule_counts(sample_rows, header_row, date_indices)
    legend_hint = _legend_hint(sample_rows)

    direct_score = (
        len(date_columns) * 0.8
        + direct_count * 4
        + adjacent_hours_count * 2
        + every_second_score * 12
        + _sheet_base_score(sheet)
    )
    shift_score = (
        len(date_columns) * 0.8
        + code_count * 3
        + continuous_score * 12
        + legend_hint * 5
        + _sheet_base_score(sheet)
    )

    if direct_score < 8 and shift_score < 8:
        layout_type = UNKNOWN
        confidence = 0.2
    elif direct_score >= shift_score:
        layout_type = DIRECT_TIME_WITH_HOURS_COLUMNS
        confidence = _confidence(direct_score, shift_score)
    else:
        layout_type = SHIFT_CODE_MATRIX_WITH_LEGEND
        confidence = _confidence(shift_score, direct_score)

    warnings = []
    if len(date_columns) < 3:
        warnings.append("FEW_DATE_COLUMNS")
    if layout_type == UNKNOWN:
        warnings.append("UNCERTAIN_LAYOUT")

    overall = max(direct_score, shift_score) + header.get("score", 0)
    return LayoutDetectionResult(
        sheet_name=sheet.get("sheet_name"),
        header_row=header_row,
        layout_type=layout_type,
        likely_date_columns=date_columns,
        likely_staff_row_range=staff_range,
        confidence=confidence,
        warnings=warnings,
        diagnostics={
            "overall_score": round(overall, 3),
            "direct_score": round(direct_score, 3),
            "shift_score": round(shift_score, 3),
            "date_count": len(date_columns),
            "date_column_gaps": gaps,
            "sample_direct_time_cells": direct_count,
            "sample_adjacent_hours_cells": adjacent_hours_count,
            "sample_shift_code_cells": code_count,
            "legend_hint": legend_hint,
            "sheet_score": _sheet_base_score(sheet),
        },
    )


def _sheet_base_score(sheet: dict[str, Any]) -> float:
    score = 0.0
    if not sheet.get("appears_old_or_archive"):
        score += 8
    if sheet.get("candidate_header_rows"):
        score += 8
    date_count = len(sheet.get("candidate_date_columns") or [])
    score += min(date_count, 31) * 0.5
    score += min(float(sheet.get("non_empty_cell_density") or 0) * 20, 5)
    return score


def _candidate_score(candidate: LayoutDetectionResult) -> float:
    return float(candidate.diagnostics.get("overall_score") or 0)


def _is_usable_candidate(candidate: LayoutDetectionResult) -> bool:
    return (
        candidate.layout_type != UNKNOWN
        and candidate.header_row is not None
        and bool(candidate.likely_date_columns)
    )


def _likely_staff_range(sample_rows: list[list[Any]], header_row: int, header: dict[str, Any]) -> dict[str, int | None]:
    name_col = int((header.get("labels") or {}).get("name") or 1)
    start = None
    end = None
    blank_streak = 0
    for row_index in range(header_row + 1, len(sample_rows) + 1):
        row = sample_rows[row_index - 1]
        value = row[name_col - 1] if len(row) >= name_col else None
        text = str(value or "").strip()
        marker = text.lower()
        if marker in {"need", "total", "briefing", "still need"} or marker.startswith("briefing"):
            break
        if not text:
            blank_streak += 1
            if start is not None and blank_streak >= 3:
                break
            continue
        blank_streak = 0
        start = row_index if start is None else start
        end = row_index
    return {"start": start, "end": end}


def _sample_schedule_counts(sample_rows: list[list[Any]], header_row: int, date_indices: list[int]) -> tuple[int, int, int]:
    direct_count = 0
    adjacent_hours_count = 0
    code_count = 0
    for row_index in range(header_row + 1, len(sample_rows) + 1):
        row = sample_rows[row_index - 1]
        name = str((row[0] if row else "") or "").strip().lower()
        if name in {"need", "total", "briefing", "still need"} or name.startswith("briefing"):
            break
        for col in date_indices:
            if col > len(row):
                continue
            text = str(row[col - 1] or "").strip()
            if not text:
                continue
            if TIME_RANGE_RE.search(text):
                direct_count += 1
                if col < len(row):
                    try:
                        hours = float(row[col])
                    except (TypeError, ValueError):
                        hours = None
                    if hours is not None and 0 < hours <= 24:
                        adjacent_hours_count += 1
            elif SHIFT_CODE_RE.fullmatch(text):
                code_count += 1
    return direct_count, adjacent_hours_count, code_count


def _legend_hint(sample_rows: list[list[Any]]) -> int:
    hits = 0
    for row in sample_rows:
        text = " ".join(str(cell or "") for cell in row).lower()
        if any(token in text for token in ("tue", "sun", "mon", "public holiday", "christmas eve", "normal working")):
            hits += 1
    return hits


def _confidence(winner: float, loser: float) -> float:
    if winner <= 0:
        return 0.0
    margin = max(0.0, winner - loser)
    return round(min(0.99, 0.45 + margin / max(winner, 1) + winner / 100), 3)
