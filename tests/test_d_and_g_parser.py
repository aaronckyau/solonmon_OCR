from __future__ import annotations

from schedule_parser.d_and_g import parse_d_and_g_schedule

from conftest import save_d_and_g_workbook


def test_parse_d_and_g_job_applications_direct_time_schedule(tmp_path):
    path = save_d_and_g_workbook(tmp_path / "D&G Apr 2026 Invoice.xlsx")

    parsed = parse_d_and_g_schedule(path)

    assert parsed.project_profile == "d_and_g"
    assert parsed.sheet_name == "Job Applications"
    assert parsed.layout_type == "d_and_g_job_applications"
    assert parsed.header_row == 2
    assert [column.date for column in parsed.date_columns] == [
        "2026-04-01",
        "2026-04-02",
        "2026-04-03",
        "2026-05-01",
        "2026-05-02",
    ]
    assert [staff.name for staff in parsed.staff] == [
        "Fung King Yan Kelvin",
        "Tam Kit Man Fion",
        "LEE Sarah",
    ]
    assert len(parsed.entries) == 6

    late_shift = next(entry for entry in parsed.entries if entry.raw_shift_code == "10:30-23:00")
    assert late_shift.date == "2026-05-01"
    assert late_shift.scheduled_in == "10:30"
    assert late_shift.scheduled_out == "23:00"
    assert late_shift.scheduled_hours == 12.5
    assert late_shift.resolution_source == "d_and_g_time_range"
    assert not parsed.errors
