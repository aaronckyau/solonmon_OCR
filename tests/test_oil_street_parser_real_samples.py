from pathlib import Path

import pytest

from schedule_parser.oil_street import parse_oil_street_schedule


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "schedules"


def test_real_jan_sample_if_present():
    path = FIXTURE_DIR / "Oil Street Jan 2025 Schedule.xlsx"
    if not path.exists():
        pytest.skip(f"Missing real sample fixture: {path}")

    parsed = parse_oil_street_schedule(path)

    assert parsed.sheet_name == "Jan" or not parsed.sheet_name.lower().endswith("old")
    assert parsed.layout_type == "direct_time_with_hours_columns"
    assert parsed.header_row is not None
    assert 28 <= len(parsed.date_columns) <= 31
    assert len(parsed.staff) > 0
    assert len(parsed.entries) > 0
    assert parsed.diagnostics["ai_used"] is False


def test_real_apr_sample_if_present():
    path = FIXTURE_DIR / "Oil Street Apr 2025 Schedule.xlsx"
    if not path.exists():
        pytest.skip(f"Missing real sample fixture: {path}")

    parsed = parse_oil_street_schedule(path)

    assert parsed.sheet_name == "Apr" or not parsed.sheet_name.lower().endswith("old")
    assert parsed.layout_type == "shift_code_matrix_with_legend"
    assert parsed.header_row is not None
    assert 28 <= len(parsed.date_columns) <= 31
    assert len(parsed.staff) > 0
    for code in ["A", "B", "C", "D", "E", "A1", "B1"]:
        assert code in parsed.shift_times
    assert len(parsed.entries) > 0
    assert parsed.diagnostics["ai_used"] is False
    assert "AMBIGUOUS_SHIFT_CODE" not in [warning.code for warning in parsed.warnings]
    slash_entries = [entry for entry in parsed.entries if "/" in entry.raw_shift_code]
    if slash_entries:
        assert all(entry.resolution_source in {"legend_combined_code", "or_equivalent", "or_options"} for entry in slash_entries)
        assert all(entry.shift_options for entry in slash_entries)
