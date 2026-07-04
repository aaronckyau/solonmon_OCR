from __future__ import annotations

from schedule_parser.roster_compare import compare_schedule_to_ocr


def sample_schedule():
    return {
        "sheet_name": "August 2025",
        "staff": [
            {"name": "Cheng Nuo Isla", "staff_id": "S001", "phone_last4": "1234", "row": 7},
            {"name": "Chan Hiu Ue", "staff_id": "S002", "phone_last4": "5678", "row": 8},
        ],
        "entries": [
            {
                "staff_name": "Cheng Nuo Isla",
                "staff_id": "S001",
                "phone_last4": "1234",
                "date": "2025-08-20",
                "shift_code": "A",
                "raw_shift_code": "A",
                "scheduled_in": "09:45",
                "scheduled_out": "20:15",
                "scheduled_hours": 10.5,
                "schedule_cell": "E7",
            },
            {
                "staff_name": "Cheng Nuo Isla",
                "staff_id": "S001",
                "phone_last4": "1234",
                "date": "2025-08-21",
                "shift_code": "A",
                "raw_shift_code": "A",
                "scheduled_in": "09:45",
                "scheduled_out": "20:15",
                "scheduled_hours": 10.5,
                "schedule_cell": "F7",
            },
            {
                "staff_name": "Chan Hiu Ue",
                "staff_id": "S002",
                "phone_last4": "5678",
                "date": "2025-08-20",
                "shift_code": "B",
                "raw_shift_code": "B",
                "scheduled_in": "09:45",
                "scheduled_out": "18:45",
                "scheduled_hours": 9,
                "schedule_cell": "E8",
            },
        ],
    }


def test_compares_partial_ocr_name_to_schedule_staff_and_infers_day_only_date():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [{"name": "ISLA", "date": "20", "in": "09:41", "out": "20:15", "source_filename": "Cheng Nuo Isla 2.jpg"}],
    )

    assert result["summary"]["matched_rows"] == 1
    assert result["summary"]["missing_logsheet_rows"] == 1
    assert result["summary"]["name_check_rows"] == 1

    matched = next(row for row in result["rows"] if row["date"] == "2025-08-20")
    assert matched["staff_name"] == "Cheng Nuo Isla"
    assert matched["ocr_name"] == "ISLA"
    assert matched["actual_in"] == "09:41"
    assert matched["actual_out"] == "20:15"
    assert matched["status"] == "Early In"
    assert matched["flags"] == ["Name Check"]

    missing = next(row for row in result["rows"] if row["date"] == "2025-08-21")
    assert missing["status"] == "Missing Logsheet"


def test_adds_unscheduled_punch_for_matched_staff_without_roster_shift():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [{"name": "Cheng Nuo Isla", "date": "2025-08-22", "in": "09:45", "out": "18:45"}],
    )

    statuses = [row["status"] for row in result["rows"]]
    assert "Unscheduled Punch" in statuses
    assert result["summary"]["unscheduled_punch_rows"] == 1
    unscheduled = next(row for row in result["rows"] if row["status"] == "Unscheduled Punch")
    assert unscheduled["date"] == "2025-08-22"
    assert unscheduled["actual_in"] == "09:45"


def test_aligns_wrong_ocr_iso_year_to_roster_date_instead_of_duplicating_day():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [{"name": "Cheng Nuo Isla", "date": "2024-08-20", "in": "09:45", "out": "20:15"}],
    )

    matched = next(row for row in result["rows"] if row["date"] == "2025-08-20")
    assert matched["status"] == "Matched"
    assert matched["actual_in"] == "09:45"
    assert matched["actual_out"] == "20:15"
    assert result["summary"]["unscheduled_punch_rows"] == 0
    assert not any(row["date"] == "2024-08-20" for row in result["rows"])


def test_unmatched_ocr_name_does_not_expand_entire_roster_as_missing():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [{"name": "Unknown Person", "date": "2025-08-20", "in": "09:45", "out": "18:45"}],
    )

    assert len(result["rows"]) == 1
    assert result["rows"][0]["status"] == "Name Not Matched"
    assert result["summary"]["missing_logsheet_rows"] == 0
    assert result["summary"]["unmatched_name_rows"] == 1


def test_confirmed_staff_assignment_overrides_fuzzy_ocr_name():
    schedule = {
        "sheet_name": "April 2026",
        "staff": [
            {"name": "Lun Ka Yan Ashley", "staff_id": "S001", "phone_last4": "1111", "row": 7},
            {"name": "Ho Ka Yan", "staff_id": "S002", "phone_last4": "2222", "row": 8},
        ],
        "entries": [
            {
                "staff_name": "Lun Ka Yan Ashley",
                "staff_id": "S001",
                "phone_last4": "1111",
                "date": "2026-04-01",
                "shift_code": "D&G",
                "raw_shift_code": "D&G",
                "scheduled_in": "10:00",
                "scheduled_out": "21:15",
                "scheduled_hours": 11.25,
                "schedule_cell": "E7",
            },
            {
                "staff_name": "Ho Ka Yan",
                "staff_id": "S002",
                "phone_last4": "2222",
                "date": "2026-04-01",
                "shift_code": "D&G",
                "raw_shift_code": "D&G",
                "scheduled_in": "09:30",
                "scheduled_out": "18:30",
                "scheduled_hours": 9,
                "schedule_cell": "E8",
            },
        ],
    }

    result = compare_schedule_to_ocr(
        schedule,
        [
            {
                "name": "Lun Ka Yan Ashley",
                "assigned_staff_name": "Lun Ka Yan Ashley",
                "ocr_name": "Luk Ka Yan",
                "original_name": "Luk Ka Yan",
                "date": "2026-04-01",
                "in": "08:30",
                "out": "22:40",
            }
        ],
    )

    assert result["summary"]["matched_rows"] == 1
    matched = next(row for row in result["rows"] if row["staff_name"] == "Lun Ka Yan Ashley")
    assert matched["ocr_name"] == "Luk Ka Yan"
    assert matched["actual_in"] == "08:30"
    assert matched["actual_out"] == "22:40"
    assert matched["name_match_type"] == "confirmed"
    assert not any(row["staff_name"] == "Ho Ka Yan" and row.get("has_actual") for row in result["rows"])


def test_merges_multiple_ocr_rows_to_first_in_last_out_for_same_staff_date():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [
            {"name": "Cheng Nuo Isla", "date": "2025-08-20", "in": "12:00", "out": "18:00"},
            {"name": "Cheng Nuo Isla", "date": "2025-08-20", "in": "09:40", "out": "20:16"},
        ],
    )

    matched = next(row for row in result["rows"] if row["date"] == "2025-08-20")
    assert matched["actual_in"] == "09:40"
    assert matched["actual_out"] == "20:16"
    assert matched["status"] == "Early In"


def test_oil_street_compare_uses_15_minute_charged_blocks():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [{"name": "Cheng Nuo Isla", "date": "2025-08-20", "in": "09:54", "out": "20:07"}],
    )

    matched = next(row for row in result["rows"] if row["date"] == "2025-08-20")
    assert result["summary"]["late_grace_minutes"] == 8
    assert matched["raw_late_minutes"] == 9
    assert matched["late_minutes"] == 15
    assert matched["rounded_late_minutes"] == 15
    assert matched["early_leave_minutes"] == 15
    assert matched["overtime_minutes"] == 0
    assert matched["status"] == "Late + Early Leave"


def test_oil_street_compare_default_grace_allows_eight_minutes():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [{"name": "Cheng Nuo Isla", "date": "2025-08-20", "in": "09:53", "out": "20:15"}],
    )

    matched = next(row for row in result["rows"] if row["date"] == "2025-08-20")
    assert matched["raw_late_minutes"] == 8
    assert matched["late_minutes"] == 0
    assert matched["rounded_late_minutes"] == 0
    assert matched["status"] == "Matched"


def test_oil_street_compare_accepts_custom_grace_minutes():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [{"name": "Cheng Nuo Isla", "date": "2025-08-20", "in": "09:53", "out": "20:15"}],
        late_grace_minutes=7,
    )

    matched = next(row for row in result["rows"] if row["date"] == "2025-08-20")
    assert result["summary"]["late_grace_minutes"] == 7
    assert matched["raw_late_minutes"] == 8
    assert matched["late_minutes"] == 15
    assert matched["rounded_late_minutes"] == 15
    assert matched["status"] == "Late"


def test_oil_street_compare_accepts_custom_early_leave_grace_minutes():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [{"name": "Cheng Nuo Isla", "date": "2025-08-20", "in": "09:45", "out": "20:07"}],
        early_leave_grace_minutes=8,
    )

    matched = next(row for row in result["rows"] if row["date"] == "2025-08-20")
    assert result["summary"]["early_leave_grace_minutes"] == 8
    assert matched["early_leave_minutes"] == 0
    assert matched["status"] == "Matched"


def test_oil_street_compare_charges_early_leave_after_custom_grace_minutes():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [{"name": "Cheng Nuo Isla", "date": "2025-08-20", "in": "09:45", "out": "20:06"}],
        early_leave_grace_minutes=8,
    )

    matched = next(row for row in result["rows"] if row["date"] == "2025-08-20")
    assert matched["early_leave_minutes"] == 15
    assert matched["status"] == "Early Leave"


def test_early_in_is_not_counted_unless_enabled():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [{"name": "Cheng Nuo Isla", "date": "2025-08-20", "in": "09:25", "out": "20:15"}],
    )

    matched = next(row for row in result["rows"] if row["date"] == "2025-08-20")
    assert result["summary"]["count_early_in"] is False
    assert result["summary"]["early_in_rows"] == 0
    assert matched["raw_early_in_minutes"] == 20
    assert matched["early_in_minutes"] == 0
    assert matched["status"] == "Early In"


def test_early_in_counts_after_grace_when_enabled():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [{"name": "Cheng Nuo Isla", "date": "2025-08-20", "in": "09:25", "out": "20:15"}],
        count_early_in=True,
        early_in_grace_minutes=8,
    )

    matched = next(row for row in result["rows"] if row["date"] == "2025-08-20")
    assert result["summary"]["count_early_in"] is True
    assert result["summary"]["early_in_grace_minutes"] == 8
    assert result["summary"]["early_in_rows"] == 1
    assert matched["raw_early_in_minutes"] == 20
    assert matched["early_in_minutes"] == 15
    assert matched["status"] == "Early In"


def test_overtime_is_not_counted_unless_enabled():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [{"name": "Cheng Nuo Isla", "date": "2025-08-20", "in": "09:45", "out": "20:35"}],
    )

    matched = next(row for row in result["rows"] if row["date"] == "2025-08-20")
    assert result["summary"]["count_overtime"] is False
    assert matched["raw_overtime_minutes"] == 20
    assert matched["overtime_minutes"] == 0
    assert matched["status"] == "Matched"


def test_overtime_counts_after_grace_when_enabled():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [{"name": "Cheng Nuo Isla", "date": "2025-08-20", "in": "09:45", "out": "20:35"}],
        count_overtime=True,
        overtime_grace_minutes=8,
    )

    matched = next(row for row in result["rows"] if row["date"] == "2025-08-20")
    assert result["summary"]["count_overtime"] is True
    assert result["summary"]["overtime_grace_minutes"] == 8
    assert matched["raw_overtime_minutes"] == 20
    assert matched["overtime_minutes"] == 15
    assert matched["status"] == "Matched"


def test_explicit_out_without_in_stays_missing_in():
    result = compare_schedule_to_ocr(
        sample_schedule(),
        [{"name": "Cheng Nuo Isla", "date": "2025-08-20", "in": "", "out": "20:15", "all_times": []}],
    )

    matched = next(row for row in result["rows"] if row["date"] == "2025-08-20")
    assert matched["actual_in"] == ""
    assert matched["actual_out"] == "20:15"
    assert matched["status"] == "Missing In"
