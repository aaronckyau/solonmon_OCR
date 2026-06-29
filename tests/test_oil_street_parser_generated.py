import json

from schedule_parser.oil_street import parse_oil_street_schedule

from conftest import save_apr_style_workbook, save_formula_header_workbook, save_jan_style_workbook, save_slash_code_workbook


def test_jan_style_generated_workbook_parses_direct_time_layout(tmp_path):
    path = save_jan_style_workbook(tmp_path / "Oil Street Jan 2025 Schedule.xlsx")

    parsed = parse_oil_street_schedule(path)
    data = parsed.to_dict()

    assert parsed.layout_type == "direct_time_with_hours_columns"
    assert parsed.sheet_name == "Jan"
    assert parsed.header_row == 6
    assert [col.letter for col in parsed.date_columns] == ["E", "G", "I"]
    assert len(parsed.staff) == 2
    assert len(parsed.entries) == 5
    first = parsed.entries[0]
    assert first.date == "2025-01-01"
    assert first.date_cell == "E6"
    assert first.schedule_cell == "E7"
    assert first.scheduled_in == "09:45"
    assert first.scheduled_out == "20:15"
    assert first.scheduled_hours == 10.5
    json.dumps(data)


def test_apr_style_generated_workbook_parses_shift_code_layout(tmp_path):
    path = save_apr_style_workbook(tmp_path / "Oil Street Apr 2025 Schedule.xlsx")

    parsed = parse_oil_street_schedule(path)

    assert parsed.layout_type == "shift_code_matrix_with_legend"
    assert parsed.sheet_name == "Apr"
    assert len(parsed.date_columns) == 30
    assert len(parsed.staff) == 2
    for code in ["A", "B", "C", "D", "E", "A1", "B1"]:
        assert code in parsed.shift_times
    first = parsed.entries[0]
    assert first.raw_shift_code == "A"
    assert first.scheduled_in == "09:45"
    assert first.scheduled_out == "18:45"
    assert first.scheduled_hours == 9.0
    override = next(entry for entry in parsed.entries if entry.raw_shift_code == "D (2pm - 8:15pm)")
    assert override.scheduled_in == "14:00"
    assert override.scheduled_out == "20:15"
    assert override.resolution_source == "inline_override"


def test_formula_date_headers_are_inferred(tmp_path):
    path = save_formula_header_workbook(tmp_path / "formula.xlsx")

    parsed = parse_oil_street_schedule(path)

    assert [col.date for col in parsed.date_columns] == ["2025-05-01", "2025-05-02", "2025-05-03"]
    assert parsed.date_columns[1].source == "formula_inferred"
    assert [entry.date for entry in parsed.entries] == ["2025-05-01", "2025-05-02", "2025-05-03"]


def test_summary_columns_stop_date_detection_and_unknown_code_is_preserved(tmp_path):
    path = save_apr_style_workbook(tmp_path / "unknown.xlsx", unknown_code=True)

    parsed = parse_oil_street_schedule(path)
    unknown = next(entry for entry in parsed.entries if entry.raw_shift_code == "Z9")

    assert len(parsed.date_columns) == 30
    assert unknown.schedule_cell == "I7"
    assert unknown.resolution_source == "unresolved"
    assert "UNKNOWN_SHIFT_CODE" in unknown.warnings
    assert "Z9" in parsed.diagnostics["unknown_shift_codes"]


def test_generated_workbook_slash_codes_do_not_flood_warnings(tmp_path):
    path = save_slash_code_workbook(tmp_path / "slash.xlsx")

    parsed = parse_oil_street_schedule(path)
    slash_entries = [entry for entry in parsed.entries if "/" in entry.raw_shift_code]
    warning_codes = [warning.code for warning in parsed.warnings]

    assert len(slash_entries) == 4
    assert "AMBIGUOUS_SHIFT_CODE" not in warning_codes
    assert parsed.diagnostics["warning_count"] == 0
    assert {entry.raw_shift_code for entry in slash_entries} == {"A/C", "B/D", "A1/C1", "B1/D1"}
    assert all(entry.shift_options for entry in slash_entries)
    assert next(entry for entry in slash_entries if entry.raw_shift_code == "A/C").resolution_source == "or_options"
    assert next(entry for entry in slash_entries if entry.raw_shift_code == "B/D").resolution_source == "or_equivalent"
