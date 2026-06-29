from __future__ import annotations

from io import BytesIO

from schedule_parser.web import create_app

from conftest import save_jan_style_workbook


def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_health_returns_ok():
    response = client().get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_index_renders_upload_page():
    response = client().get("/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Oil Street 排班解析器" in body
    assert "上傳" in body
    assert "人工覆核" in body
    assert "下載修正 JSON" in body


def test_parse_without_file_returns_400_json():
    response = client().post("/api/parse", data={})
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["ok"] is False
    assert "上傳欄位" in payload["error"]


def test_parse_invalid_extension_returns_400_json():
    response = client().post(
        "/api/parse",
        data={"schedule": (BytesIO(b"not excel"), "schedule.txt")},
        content_type="multipart/form-data",
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["ok"] is False
    assert ".xlsx" in payload["error"]


def test_parse_generated_jan_workbook_returns_summary(tmp_path):
    workbook_path = save_jan_style_workbook(tmp_path / "Oil Street Jan 2025 Schedule.xlsx")
    response = client().post(
        "/api/parse",
        data={"schedule": (BytesIO(workbook_path.read_bytes()), workbook_path.name)},
        content_type="multipart/form-data",
    )
    payload = response.get_json()
    summary = payload["summary"]

    assert response.status_code == 200
    assert payload["ok"] is True
    assert summary["layout_type"] == "direct_time_with_hours_columns"
    assert summary["date_count"] > 0
    assert summary["staff_count"] > 0
    assert summary["entry_count"] > 0
    assert payload["schedule"]["entries"][0]["schedule_cell"] == "E7"
