from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image

from schedule_parser.web import create_app

from conftest import save_jan_style_workbook


def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def png_bytes(size=(320, 520)) -> bytes:
    image = Image.new("RGB", size, "white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_health_returns_ok():
    response = client().get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_index_renders_upload_page():
    response = client().get("/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Oil Street 排班工作台" in body
    assert "1 上傳排班表" in body
    assert "2 檢查排班" in body
    assert "3 上傳打卡紙" in body
    assert "4 核對排班" in body
    assert "5 匯出 JSON" in body
    assert "讀取排班表" in body
    assert "確認排班表" in body
    assert "下載修正 JSON" in body
    assert "Excel 貼上表格" in body
    assert "exportTableDatasetSelect" in body
    assert "copyExportTableSelectionButton" in body
    assert "copyExportTableAllButton" in body
    assert "clearExportTableSelectionButton" in body
    assert "打卡紙 OCR" in body
    assert "OCR 全部檔案" in body
    assert "複製 OCR JSON" not in body
    assert "下載 OCR JSON" not in body
    assert "ocrEnhanceImageInput" in body
    assert "影像增強" in body
    assert "OCR 表格" in body
    assert "ocrProgress" in body
    assert "排班 vs 打卡紙核對" in body
    assert "lateGraceMinutesInput" in body
    assert "earlyLeaveGraceMinutesInput" in body
    assert "countEarlyInInput" in body
    assert "earlyInGraceMinutesInput" in body
    assert "countOvertimeInput" in body
    assert "overtimeGraceMinutesInput" in body
    assert "holidaySundayInput" in body
    assert "holidayOfficialInput" in body
    assert "holidayOfficialYearInput" in body
    assert "holidayUploadInput" in body
    assert "entriesTableHead" in body
    assert "GovHK 官方假期" in body
    assert '<option value="2025">2025</option>' in body
    assert '<option value="2026" selected>2026</option>' in body
    assert '<option value="2027">2027</option>' in body
    assert "上班寬限" in body
    assert "早退寬限" in body
    assert "rosterConfidenceInput" in body
    assert "信心提示" in body
    assert "<th>信心</th>" in body
    assert "顯示 0 小時員工" in body
    assert "員工詳細核對" in body
    assert "新增 Actual Row" in body
    assert "實際差異" in body
    assert "rosterDetailImageStage" in body
    assert "rosterDetailPrevImageButton" in body
    assert "rosterDetailNextImageButton" in body
    assert "rosterDetailImageCount" in body
    assert "logsheetAssignmentList" in body
    assert "logsheetAssignmentSummary" in body
    assert 'id="messagesSection" hidden' in body
    assert body.index("<h3>排班資料</h3>") < body.index("<summary>班次時間</summary>")


def test_step_two_summary_omits_low_value_cards():
    script = (Path(__file__).parents[1] / "schedule_parser" / "static" / "parser_app.js").read_text(encoding="utf-8")

    assert '["檔案名稱", summary.source_filename]' not in script
    assert '["版型", summary.layout_type]' not in script
    assert '["警告數", summary.warning_count]' not in script
    assert '["錯誤數", summary.error_count]' not in script
    assert '["使用 AI", summary.ai_used ? "是" : "否"]' not in script
    assert "countReviewedEntries" not in script
    assert '"沒有警告或錯誤。"' not in script


def test_schedule_summary_days_and_hours_can_be_manually_overridden():
    root = Path(__file__).parents[1]
    script = (root / "schedule_parser" / "static" / "parser_app.js").read_text(encoding="utf-8")
    styles = (root / "schedule_parser" / "static" / "parser_styles.css").read_text(encoding="utf-8")

    assert "staff_summary_overrides" in script
    assert "SCHEDULE_SUMMARY_OVERRIDE_FIELDS" in script
    assert "handleScheduleSummaryOverrideChange" in script
    assert "renderScheduleSummaryInput" in script
    assert "applyScheduleSummaryOverrides" in script
    assert 'data-summary-field="${escapeAttr(field)}"' in script
    assert 'renderScheduleSummaryInput(row, "normalDays", "Normal day Days")' in script
    assert 'renderScheduleSummaryInput(row, "publicHolidayHours", "PH day Hours")' in script
    assert "<small>Days</small>" in script
    assert "<small>Hours</small>" in script
    assert ".summary-override-input" in styles
    assert ".summary-override-input::-webkit-inner-spin-button" in styles
    assert "appearance: textfield" in styles


def test_roster_summary_splits_holiday_columns_and_uses_compact_chips():
    root = Path(__file__).parents[1]
    script = (root / "schedule_parser" / "static" / "parser_app.js").read_text(encoding="utf-8")
    styles = (root / "schedule_parser" / "static" / "parser_styles.css").read_text(encoding="utf-8")

    assert "function renderRosterHeader" in script
    assert "function renderRosterColumnStructure" in script
    assert "function rosterColumnCount" in script
    assert "function rosterShiftChipHtml" in script
    assert "roster-col-ph-hours" in script
    assert "Normal day" in script
    assert "非公眾假期" in script
    assert "PH day" in script
    assert "公眾假期" in script
    assert "row.publicHolidayHours" in script
    assert 'log.isPublicHoliday ? "is-public-holiday" : ""' in script
    assert "if (state.comparison) renderRosterSummary(state.comparison.rows || [])" in script
    assert ".roster-col-ph-hours" in styles
    assert ".roster-metric-cell.is-ph" in styles
    assert "min-height: 20px" in styles
    assert "font-size: 11px" in styles


def test_export_json_step_has_excel_copyable_table_selection():
    root = Path(__file__).parents[1]
    body = (root / "schedule_parser" / "templates" / "parser_index.html").read_text(encoding="utf-8")
    script = (root / "schedule_parser" / "static" / "parser_app.js").read_text(encoding="utf-8")
    styles = (root / "schedule_parser" / "static" / "parser_styles.css").read_text(encoding="utf-8")

    assert "Excel 貼上表格" in body
    assert "exportTableHead" in body
    assert "exportTableBody" in body
    assert "exportTableIncludeHeadersInput" in body
    assert "function renderExportTable" in script
    assert "function copyExportTableSelection" in script
    assert "function exportTableToTsv" in script
    assert "function exportScheduleEntryRows" in script
    assert "data-export-column" in script
    assert "data-export-row" in script
    assert "navigator.clipboard.writeText(tsv)" in script
    assert ".export-cell.is-selected-cell" in styles
    assert ".export-table tr.is-selected-row" in styles
    assert ".export-table th.is-selected-column" in styles


def test_actual_time_exceptions_use_warning_visuals():
    root = Path(__file__).parents[1]
    script = (root / "schedule_parser" / "static" / "parser_app.js").read_text(encoding="utf-8")
    styles = (root / "schedule_parser" / "static" / "parser_styles.css").read_text(encoding="utf-8")

    assert "function compareActualTimeReasons" in script
    assert 'String(row?.status || "") === "Early In"' in script
    assert 'status === "Early In") reasons.push' not in script
    assert "function isNonChargeableEarlyIn" in script
    assert "function isCompareRowOk" in script
    assert "early_in_minutes" in script
    assert 'status.includes("Late")' in script
    assert 'status.includes("Early Leave")' in script
    assert "overtime_minutes" in script
    assert "currentCountEarlyIn" in script
    assert "currentCountOvertime" in script
    assert "comparisonStatusLabelForRow(row)" in script
    assert ".roster-detail-main.is-warning" in styles
    assert ".roster-shift-chip.is-warning" in styles


def test_logsheet_source_files_can_open_preview_from_review_ui():
    script = (Path(__file__).parents[1] / "schedule_parser" / "static" / "parser_app.js").read_text(encoding="utf-8")
    styles = (Path(__file__).parents[1] / "schedule_parser" / "static" / "parser_styles.css").read_text(encoding="utf-8")

    assert "handleLogsheetPreviewClick" in script
    assert "function openLogsheetFilePreview" in script
    assert "function sourceLinksHtml" in script
    assert "data-logsheet-preview-key" in script
    assert "renderRosterDetailImageFiles" in script
    assert ".source-file-link" in styles
    assert ".logsheet-file-name:hover" in styles


def test_roster_actual_inputs_accept_compact_time_and_paste_grid():
    script = (Path(__file__).parents[1] / "schedule_parser" / "static" / "parser_app.js").read_text(encoding="utf-8")

    assert 'addEventListener("paste", handleRosterDetailPaste)' in script
    assert "function normalizeManualActualTime" in script
    assert "function parseManualActualTimeGrid" in script
    assert 'line.includes("\\t") ? line.split("\\t")' in script
    assert "function rosterActualPasteEdits" in script
    assert "function setOcrActualCells" in script
    assert 'padStart(4, "0")' in script
    assert "11:42 或 1142" in script


def test_public_holiday_years_are_selectable_and_data_backed():
    root = Path(__file__).parents[1]
    body = (root / "schedule_parser" / "templates" / "parser_index.html").read_text(encoding="utf-8")
    script = (root / "schedule_parser" / "static" / "parser_app.js").read_text(encoding="utf-8")

    assert "holidayOfficialYearInput" in body
    assert "GOVHK_GENERAL_HOLIDAYS_BY_YEAR" in script
    assert "GOVHK_2026_GENERAL_HOLIDAYS" not in script
    assert '"2025-01-29", "Lunar New Year\'s Day"' in script
    assert '"2026-02-17", "Lunar New Year\'s Day"' in script
    assert '"2027-02-06", "Lunar New Year\'s Day"' in script
    assert "function currentOfficialHolidayYear" in script
    assert "function inferScheduleHolidayYear" in script
    assert "function shouldInferSelectedHolidayLine" in script


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


def test_ocr_without_file_returns_400_json():
    response = client().post("/api/ocr-logsheet", data={})
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["ok"] is False
    assert "logsheet" in payload["error"]


def test_ocr_invalid_extension_returns_400_json():
    response = client().post(
        "/api/ocr-logsheet",
        data={"logsheet": (BytesIO(b"not image"), "logsheet.txt")},
        content_type="multipart/form-data",
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["ok"] is False
    assert ".png" in payload["error"]


def test_ocr_missing_api_key_returns_503_json(monkeypatch):
    from schedule_parser.openrouter_ocr import OpenRouterOCRConfigError

    def fake_ocr(_file_bytes, _filename, *, mime_type=None, prompt=None):
        raise OpenRouterOCRConfigError("OPENROUTER_API_KEY is not set.")

    monkeypatch.setattr("schedule_parser.web.ocr_logsheet_with_openrouter", fake_ocr)
    response = client().post(
        "/api/ocr-logsheet",
        data={"logsheet": (BytesIO(b"fake image"), "logsheet.png")},
        content_type="multipart/form-data",
    )
    payload = response.get_json()

    assert response.status_code == 503
    assert payload["ok"] is False
    assert "OPENROUTER_API_KEY" in payload["error"]


def test_ocr_logsheet_success_uses_openrouter_client(monkeypatch):
    calls = []

    def fake_ocr(file_bytes, filename, *, mime_type=None, prompt=None):
        calls.append((file_bytes, filename, mime_type, prompt))
        assert prompt == "保留簽名欄位"
        suffix = "21" if filename == "logsheet-1.png" else "26"
        return {
            "source_filename": filename,
            "configured_model": "qwen/qwen3.6-35b-a3b",
            "response_model": "qwen/qwen3.6-35b-a3b",
            "text": '{"document_type":"logsheet","entries":[]}',
            "structured": {"document_type": "logsheet", "entries": []},
            "daily_rows": [
                {
                    "name": "Chan Ching Yee Jenny",
                    "date": f"2025-08-{suffix}",
                    "in": "09:40",
                    "out": "18:46",
                    "source_filename": filename,
                    "source_filenames": [filename],
                    "all_times": ["09:40", "18:46"],
                    "warnings": [],
                }
            ],
            "usage": {},
            "annotations": [],
        }

    monkeypatch.setattr("schedule_parser.web.ocr_logsheet_with_openrouter", fake_ocr)
    response = client().post(
        "/api/ocr-logsheet",
        data={
            "logsheet": [
                (BytesIO(b"fake image 1"), "logsheet-1.png"),
                (BytesIO(b"fake image 2"), "logsheet-2.png"),
            ],
            "prompt": "保留簽名欄位",
        },
        content_type="multipart/form-data",
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert len(calls) == 2
    assert payload["ocr"]["configured_model"] == "qwen/qwen3.6-35b-a3b"
    assert payload["ocr"]["structured"]["document_type"] == "logsheet"
    assert payload["ocr"]["source_count"] == 2
    assert len(payload["ocr"]["daily_rows"]) == 2
    assert payload["ocr"]["daily_rows"][0]["name"] == "Chan Ching Yee Jenny"


def test_ocr_logsheet_enhances_image_by_default(monkeypatch):
    original = png_bytes()
    calls = []

    def fake_ocr(file_bytes, filename, *, mime_type=None, prompt=None):
        calls.append((file_bytes, filename, mime_type))
        return {
            "source_filename": filename,
            "configured_model": "qwen/qwen3.6-35b-a3b",
            "response_model": "qwen/qwen3.6-35b-a3b",
            "text": "{}",
            "structured": {},
            "daily_rows": [],
            "usage": {},
            "annotations": [],
        }

    monkeypatch.setattr("schedule_parser.web.ocr_logsheet_with_openrouter", fake_ocr)
    response = client().post(
        "/api/ocr-logsheet",
        data={"logsheet": (BytesIO(original), "logsheet.png")},
        content_type="multipart/form-data",
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert calls[0][0] != original
    assert calls[0][2] == "image/jpeg"
    preprocessing = payload["ocr"]["results"][0]["preprocessing"]
    assert preprocessing["enabled"] is True
    assert preprocessing["applied"] is True


def test_ocr_logsheet_can_disable_image_enhancement(monkeypatch):
    original = png_bytes()
    calls = []

    def fake_ocr(file_bytes, filename, *, mime_type=None, prompt=None):
        calls.append((file_bytes, filename, mime_type))
        return {
            "source_filename": filename,
            "configured_model": "qwen/qwen3.6-35b-a3b",
            "response_model": "qwen/qwen3.6-35b-a3b",
            "text": "{}",
            "structured": {},
            "daily_rows": [],
            "usage": {},
            "annotations": [],
        }

    monkeypatch.setattr("schedule_parser.web.ocr_logsheet_with_openrouter", fake_ocr)
    response = client().post(
        "/api/ocr-logsheet",
        data={"logsheet": (BytesIO(original), "logsheet.png"), "enhance_image": "0"},
        content_type="multipart/form-data",
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert calls[0] == (original, "logsheet.png", "image/png")
    preprocessing = payload["ocr"]["results"][0]["preprocessing"]
    assert preprocessing["enabled"] is False
    assert preprocessing["applied"] is False


def test_compare_roster_success_returns_summary():
    response = client().post(
        "/api/compare-roster",
        json={
            "schedule": {
                "staff": [{"name": "Cheng Nuo Isla", "staff_id": "S001"}],
                "entries": [
                    {
                        "staff_name": "Cheng Nuo Isla",
                        "staff_id": "S001",
                        "date": "2025-08-20",
                        "shift_code": "A",
                        "scheduled_in": "09:45",
                        "scheduled_out": "20:15",
                        "scheduled_hours": 10.5,
                    }
                ],
            },
            "late_grace_minutes": 7,
            "early_leave_grace_minutes": 6,
            "count_early_in": True,
            "early_in_grace_minutes": 5,
            "count_overtime": True,
            "overtime_grace_minutes": 4,
            "ocr_rows": [{"name": "ISLA", "date": "20", "in": "09:41", "out": "20:15"}],
        },
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["comparison"]["summary"]["matched_rows"] == 1
    assert payload["comparison"]["summary"]["late_grace_minutes"] == 7
    assert payload["comparison"]["summary"]["early_leave_grace_minutes"] == 6
    assert payload["comparison"]["summary"]["count_early_in"] is True
    assert payload["comparison"]["summary"]["early_in_grace_minutes"] == 5
    assert payload["comparison"]["summary"]["count_overtime"] is True
    assert payload["comparison"]["summary"]["overtime_grace_minutes"] == 4
    assert payload["comparison"]["rows"][0]["staff_name"] == "Cheng Nuo Isla"


def test_compare_roster_without_schedule_returns_400_json():
    response = client().post("/api/compare-roster", json={"ocr_rows": []})
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["ok"] is False
    assert "schedule" in payload["error"]


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
