from schedule_parser.excel_inspector import inspect_workbook

from conftest import save_formula_header_workbook


def test_inspector_reports_formula_inferred_date_columns(tmp_path):
    path = save_formula_header_workbook(tmp_path / "formula.xlsx")

    inspected = inspect_workbook(path)
    sheet = inspected["sheets"][0]
    dates = [item for item in sheet["candidate_date_columns"] if item["row"] == 6]

    assert [item["date"] for item in dates[:3]] == ["2025-05-01", "2025-05-02", "2025-05-03"]
    assert dates[1]["formula"] == "=E6+1"
    assert dates[1]["source"] == "formula_inferred"
    assert sheet["formula_cells"][0] == {"cell": "F6", "formula": "=E6+1"}
