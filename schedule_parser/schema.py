from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


@dataclass(slots=True)
class ParsedDateColumn:
    column: int
    letter: str
    date: str
    raw_value: JsonValue
    formula: str | None
    source: str


@dataclass(slots=True)
class ParsedStaff:
    name: str
    staff_id: str
    phone_last4: str
    row: int
    source_cells: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedShiftTime:
    code: str
    start: str
    end: str
    hours: float | None
    source: str
    source_text: str
    source_cell: str | None
    applies_to: str | None
    specific_dates: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParsedShiftOption:
    code: str
    start: str
    end: str
    hours: float | None
    source: str
    source_cell: str | None
    source_text: str


@dataclass(slots=True)
class ParsedScheduleEntry:
    staff_name: str
    staff_id: str
    phone_last4: str
    staff_row: int
    date: str
    date_column: int
    date_cell: str
    schedule_cell: str
    raw_value: JsonValue
    raw_shift_code: str
    shift_code: str
    scheduled_in: str
    scheduled_out: str
    scheduled_hours: float | None
    resolution_source: str
    warnings: list[str] = field(default_factory=list)
    shift_options: list[ParsedShiftOption] = field(default_factory=list)


@dataclass(slots=True)
class ParserWarning:
    code: str
    message: str
    cell: str | None
    severity: str = "warning"


@dataclass(slots=True)
class ParserError:
    code: str
    message: str
    cell: str | None


@dataclass(slots=True)
class ParsedSchedule:
    project_profile: str
    source_filename: str
    sheet_name: str
    layout_type: str
    header_row: int | None
    date_columns: list[ParsedDateColumn] = field(default_factory=list)
    staff: list[ParsedStaff] = field(default_factory=list)
    shift_times: dict[str, ParsedShiftTime] = field(default_factory=dict)
    entries: list[ParsedScheduleEntry] = field(default_factory=list)
    warnings: list[ParserWarning] = field(default_factory=list)
    errors: list[ParserError] = field(default_factory=list)
    diagnostics: dict[str, JsonValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JsonValue]:
        return to_jsonable(asdict(self))  # type: ignore[return-value]


def to_jsonable(value: Any) -> JsonValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    return str(value)
