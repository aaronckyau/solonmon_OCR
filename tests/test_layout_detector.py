from schedule_parser.excel_inspector import inspect_workbook
from schedule_parser.layout_detector import (
    DIRECT_TIME_WITH_HOURS_COLUMNS,
    SHIFT_CODE_MATRIX_WITH_LEGEND,
    detect_schedule_layout,
)

from conftest import save_apr_style_workbook, save_jan_style_workbook


def test_detects_direct_time_with_hours_columns(tmp_path):
    inspected = inspect_workbook(save_jan_style_workbook(tmp_path / "jan.xlsx"))

    result = detect_schedule_layout(inspected)

    assert result.sheet_name == "Jan"
    assert result.header_row == 6
    assert result.layout_type == DIRECT_TIME_WITH_HOURS_COLUMNS
    assert [col["letter"] for col in result.likely_date_columns] == ["E", "G", "I"]


def test_detects_shift_code_matrix_with_legend(tmp_path):
    inspected = inspect_workbook(save_apr_style_workbook(tmp_path / "apr.xlsx"))

    result = detect_schedule_layout(inspected)

    assert result.sheet_name == "Apr"
    assert result.header_row == 6
    assert result.layout_type == SHIFT_CODE_MATRIX_WITH_LEGEND
    assert result.diagnostics["date_count"] == 30
