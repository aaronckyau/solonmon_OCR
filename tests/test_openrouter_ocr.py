from __future__ import annotations

from io import BytesIO
import json

import pytest

from schedule_parser import openrouter_ocr


def test_dotenv_lowercase_openrouter_key_is_supported(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text('openrouter="sk-or-test-value"\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER", raising=False)
    monkeypatch.delenv("openrouter", raising=False)
    openrouter_ocr._read_dotenv_values.cache_clear()

    assert openrouter_ocr._config_value("OPENROUTER_API_KEY") == ""
    assert openrouter_ocr._config_value("openrouter") == "sk-or-test-value"


def test_image_payload_uses_qwen_model_and_data_url():
    payload = openrouter_ocr.build_logsheet_ocr_payload(
        b"fake image",
        "logsheet.png",
        model="qwen/qwen3.6-35b-a3b",
        mime_type="image/png",
    )

    content = payload["messages"][0]["content"]

    assert payload["model"] == "qwen/qwen3.6-35b-a3b"
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert payload["reasoning"] == {"effort": "none", "exclude": True}
    assert "daily_rows" in content[0]["text"]
    assert "first/earliest" in content[0]["text"]
    assert '"raw_text"' not in content[0]["text"]
    assert '"tables"' not in content[0]["text"]


def test_pdf_payload_uses_file_parser_plugin():
    payload = openrouter_ocr.build_logsheet_ocr_payload(
        b"fake pdf",
        "logsheet.pdf",
        model="qwen/qwen3.6-35b-a3b",
        mime_type="application/pdf",
    )

    content = payload["messages"][0]["content"]

    assert content[1]["type"] == "file"
    assert content[1]["file"]["file_data"].startswith("data:application/pdf;base64,")
    assert payload["plugins"][0]["id"] == "file-parser"


def test_pdf_ocr_splits_pages_and_merges_rows(monkeypatch):
    pypdf = pytest.importorskip("pypdf")
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_blank_page(width=72, height=72)
    buffer = BytesIO()
    writer.write(buffer)
    calls = []

    def fake_post(payload, *, api_key):
        calls.append(payload)
        page_filename = payload["messages"][0]["content"][1]["file"]["filename"]
        day = "1" if page_filename.endswith("_page_01.pdf") else "2"
        return {
            "model": "fake-model",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": json.dumps(
                            {
                                "document_type": "logsheet",
                                "month_year": "May 2026",
                                "daily_rows": [
                                    {"name": "Helper A", "date": day, "sign_in": "09:00", "sign_out": "18:00"}
                                ],
                            }
                        )
                    },
                }
            ],
            "usage": {"total_tokens": 10},
        }

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_PDF_PARALLELISM", "1")
    monkeypatch.setattr(openrouter_ocr, "_post_openrouter", fake_post)

    result = openrouter_ocr.ocr_logsheet_with_openrouter(
        buffer.getvalue(),
        "FM2026_gallery helper sign-in sheet_May.pdf",
        mime_type="application/pdf",
        prompt="May 2026",
    )

    assert len(calls) == 2
    assert result["text"] == "PDF split OCR: 2 pages, 2 rows."
    assert result["usage"]["total_tokens"] == 20
    assert [row["date"] for row in result["daily_rows"]] == ["2026-05-01", "2026-05-02"]
    assert {row["source_filename"] for row in result["daily_rows"]} == {"FM2026_gallery helper sign-in sheet_May.pdf"}
    assert [page["row_count"] for page in result["page_results"]] == [1, 1]


def test_normalizes_daily_rows_to_first_in_last_out():
    structured = {
        "document_type": "logsheet",
        "entries": [
            {
                "date": "21",
                "morning_in": "21 09:40",
                "morning_out": "21 12:01",
                "afternoon_in": "21 12:56",
                "afternoon_out": "21 18:46",
            },
            {
                "date": "26",
                "morning_in": "26 12:42",
                "afternoon_out": "26 16:45",
            },
        ],
    }

    rows = openrouter_ocr.normalize_logsheet_daily_rows(
        structured,
        r"doc\Testing\Testing\Oil Street\August 2025\Chan Ching Yee Jenny 2.jpg",
    )

    assert rows == [
        {
            "name": "Chan Ching Yee Jenny",
            "date": "2025-08-21",
            "in": "09:40",
            "out": "18:46",
            "source_filename": r"doc\Testing\Testing\Oil Street\August 2025\Chan Ching Yee Jenny 2.jpg",
            "source_filenames": [r"doc\Testing\Testing\Oil Street\August 2025\Chan Ching Yee Jenny 2.jpg"],
            "all_times": ["09:40", "12:01", "12:56", "18:46"],
            "warnings": [],
        },
        {
            "name": "Chan Ching Yee Jenny",
            "date": "2025-08-26",
            "in": "12:42",
            "out": "16:45",
            "source_filename": r"doc\Testing\Testing\Oil Street\August 2025\Chan Ching Yee Jenny 2.jpg",
            "source_filenames": [r"doc\Testing\Testing\Oil Street\August 2025\Chan Ching Yee Jenny 2.jpg"],
            "all_times": ["12:42", "16:45"],
            "warnings": [],
        },
    ]


def test_card_two_row_index_recovers_date_when_tens_digit_is_hidden():
    rows = openrouter_ocr.normalize_logsheet_daily_rows(
        {
            "month_year": "June 2026",
            "daily_rows": [
                {
                    "row_index": 2,
                    "date": "7",
                    "morning_in": "09:30",
                    "afternoon_out": "20:15",
                }
            ],
        },
        "Oi! timecard_June 2026 (All Staff).pdf",
        source_card_no=2,
    )

    assert rows[0]["date"] == "2026-06-17"
    assert rows[0]["source_row_index"] == 2
    assert rows[0]["date_identity_status"] == "card_row"
    assert not rows[0]["warnings"]


def test_card_one_row_index_maps_directly_to_first_half_date():
    rows = openrouter_ocr.normalize_logsheet_daily_rows(
        {
            "month_year": "June 2026",
            "daily_rows": [{"row_index": 15, "date": None, "in": "09:30", "out": "20:15"}],
        },
        "timecard June 2026.jpg",
        source_card_no=1,
    )

    assert rows[0]["date"] == "2026-06-15"
    assert rows[0]["date_identity_status"] == "card_row"


def test_card_row_outside_month_is_kept_for_date_review():
    rows = openrouter_ocr.normalize_logsheet_daily_rows(
        {
            "month_year": "June 2026",
            "daily_rows": [{"row_index": 16, "date": "31", "in": "09:30", "out": "20:15"}],
        },
        "timecard June 2026.jpg",
        source_card_no=2,
    )

    assert rows[0]["date"] is None
    assert rows[0]["date_identity_status"] == "invalid_card_row"
    assert any("June 2026" in warning and "31" in warning for warning in rows[0]["warnings"])


def test_obscured_second_half_date_without_row_index_is_not_guessed():
    rows = openrouter_ocr.normalize_logsheet_daily_rows(
        {
            "month_year": "June 2026",
            "daily_rows": [{"date": "7", "in": "09:30", "out": "20:15"}],
        },
        "timecard June 2026.jpg",
        source_card_no=2,
    )

    assert rows[0]["date"] is None
    assert rows[0]["date_identity_status"] == "card_date_review"
    assert any("Card 2" in warning and "列次" in warning for warning in rows[0]["warnings"])


def test_merges_multiple_images_by_name_and_date():
    rows = openrouter_ocr.merge_logsheet_daily_rows(
        [
            {"name": "A", "date": "2025-08-21", "in": "09:40", "out": "12:01", "source_filename": "a1.jpg"},
            {"name": "A", "date": "2025-08-21", "in": "12:56", "out": "18:46", "source_filename": "a2.jpg"},
        ]
    )

    assert rows[0]["in"] == "09:40"
    assert rows[0]["out"] == "18:46"
    assert rows[0]["source_filenames"] == ["a1.jpg", "a2.jpg"]


def test_merge_preserves_explicit_out_without_in():
    rows = openrouter_ocr.merge_logsheet_daily_rows(
        [{"name": "A", "date": "2025-08-21", "in": "", "out": "18:46", "all_times": []}]
    )

    assert rows[0]["in"] is None
    assert rows[0]["out"] == "18:46"


def test_merge_keeps_unmatched_roster_labels_on_separate_cards():
    rows = openrouter_ocr.merge_logsheet_daily_rows(
        [
            {
                "name": None,
                "date": "2026-06-08",
                "in": "09:00",
                "source_filename": "all-staff.pdf",
                "source_part_filename": "page-1-staff-1-card-1.jpg",
                "source_staff_label": "Unknown One",
            },
            {
                "name": None,
                "date": "2026-06-08",
                "in": "10:00",
                "source_filename": "all-staff.pdf",
                "source_part_filename": "page-1-staff-2-card-1.jpg",
                "source_staff_label": "Unknown Two",
            },
        ]
    )

    assert len(rows) == 2
    assert {row["source_staff_label"] for row in rows} == {"Unknown One", "Unknown Two"}


def test_merge_preserves_confirmed_staff_assignment_fields():
    rows = openrouter_ocr.merge_logsheet_daily_rows(
        [
            {
                "name": "Lun Ka Yan Ashley",
                "assigned_staff_name": "Lun Ka Yan Ashley",
                "ocr_name": "Luk Ka Yan",
                "original_name": "Luk Ka Yan",
                "date": "2026-04-01",
                "in": "08:30",
                "out": "22:40",
                "source_filename": "1 Apr.jpg",
            }
        ]
    )

    assert rows[0]["name"] == "Lun Ka Yan Ashley"
    assert rows[0]["assigned_staff_name"] == "Lun Ka Yan Ashley"
    assert rows[0]["ocr_name"] == "Luk Ka Yan"
    assert rows[0]["original_name"] == "Luk Ka Yan"


def test_ocr_client_attaches_source_metadata_to_rows(monkeypatch):
    def fake_post(payload, *, api_key):
        return {
            "model": "fake-model",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": json.dumps(
                            {
                                "document_type": "logsheet",
                                "month_year": "January 2025",
                                "daily_rows": [
                                    {
                                        "name": "Poon Wai Ching Crystal",
                                        "date": "17",
                                        "morning_in": "09:41",
                                        "afternoon_out": "20:15",
                                    }
                                ],
                            }
                        )
                    },
                }
            ],
            "usage": {"total_tokens": 10},
        }

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(openrouter_ocr, "_post_openrouter", fake_post)

    result = openrouter_ocr.ocr_logsheet_with_openrouter(
        b"fake image",
        "Poon Wai Ching Crystal__card_2.jpg",
        mime_type="image/jpeg",
        source_filename="Poon Wai Ching Crystal.jpg",
        source_metadata={
            "source_type": "dual_card_image",
            "source_card_no": 2,
            "source_part_filename": "Poon Wai Ching Crystal__card_2.jpg",
            "source_part_label": "card 2",
            "source_preview_path": "/api/ocr-preview/0123456789abcdef0123456789abcdef",
        },
    )

    row = result["daily_rows"][0]
    assert row["source_filename"] == "Poon Wai Ching Crystal.jpg"
    assert row["source_card_no"] == "2"
    assert row["source_part_filename"] == "Poon Wai Ching Crystal__card_2.jpg"
    assert row["source_parts"] == [
        {
            "source_card_no": "2",
            "source_part_filename": "Poon Wai Ching Crystal__card_2.jpg",
            "source_part_label": "card 2",
            "source_preview_path": "/api/ocr-preview/0123456789abcdef0123456789abcdef",
        }
    ]


def test_pdf_staff_label_uses_roster_name_and_discards_handwritten_name(monkeypatch):
    def fake_post(payload, *, api_key):
        return {
            "model": "fake-model",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": json.dumps(
                            {
                                "document_type": "logsheet",
                                "month_year": "June 2026",
                                "daily_rows": [
                                    {
                                        "name": "Johnny",
                                        "date": "8",
                                        "morning_in": "08:25",
                                        "afternoon_out": "18:30",
                                    }
                                ],
                            }
                        )
                    },
                }
            ],
            "usage": {"total_tokens": 10},
        }

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(openrouter_ocr, "_post_openrouter", fake_post)

    result = openrouter_ocr.ocr_logsheet_with_openrouter(
        b"fake image",
        "Oi_timecard_June_2026_All_Staff__page_01__staff_01.jpg",
        mime_type="image/jpeg",
        source_filename="Oi_timecard_June_2026_All_Staff.pdf",
        source_metadata={
            "source_type": "pdf_timecard_pair",
            "source_page": 1,
            "source_staff_index": 1,
            "source_staff_name_hint": "Au Kin Wai Johnny",
        },
    )

    row = result["daily_rows"][0]
    assert row["name"] == "Au Kin Wai Johnny"
    assert "ocr_name" not in row
    assert row["source_staff_name_hint"] == "Au Kin Wai Johnny"
    assert row["name_identity_status"] == "roster_label"
    assert row["date"] == "2026-06-08"


def test_pdf_staff_label_overrides_different_handwritten_card_name(monkeypatch):
    def fake_post(payload, *, api_key):
        return {
            "model": "fake-model",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": json.dumps(
                            {
                                "document_type": "logsheet",
                                "month_year": "June 2026",
                                "daily_rows": [
                                    {
                                        "name": "Lau Ka Yiu Yo Yo",
                                        "row_index": 1,
                                        "date": "6",
                                        "morning_in": "09:16",
                                        "afternoon_out": "20:15",
                                    }
                                ],
                            }
                        )
                    },
                }
            ],
            "usage": {"total_tokens": 10},
        }

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(openrouter_ocr, "_post_openrouter", fake_post)

    result = openrouter_ocr.ocr_logsheet_with_openrouter(
        b"fake image",
        "Oi_timecard_June_2026_All_Staff__page_02__staff_06__card_2.jpg",
        mime_type="image/jpeg",
        source_filename="Oi_timecard_June_2026_All_Staff.pdf",
        source_metadata={
            "source_type": "pdf_timecard_card",
            "source_page": 2,
            "source_staff_index": 6,
            "source_staff_name_hint": "Lam Wai Ching Jade",
            "source_card_no": 2,
        },
    )

    row = result["daily_rows"][0]
    assert row["name"] == "Lam Wai Ching Jade"
    assert "ocr_name" not in row
    assert row["source_staff_name_hint"] == "Lam Wai Ching Jade"
    assert row["name_identity_status"] == "roster_label"
    assert row["date"] == "2026-06-16"
    assert row["source_row_index"] == 1
    assert row["date_identity_status"] == "card_row"
    assert not any("Lau Ka Yiu Yo Yo" in warning for warning in row["warnings"])


def test_pdf_staff_label_does_not_require_handwritten_name(monkeypatch):
    def fake_post(payload, *, api_key):
        return {
            "model": "fake-model",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": json.dumps(
                            {
                                "document_type": "logsheet",
                                "month_year": "June 2026",
                                "daily_rows": [
                                    {
                                        "date": "8",
                                        "morning_in": "08:25",
                                        "afternoon_out": "18:30",
                                    }
                                ],
                            }
                        )
                    },
                }
            ],
            "usage": {"total_tokens": 10},
        }

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(openrouter_ocr, "_post_openrouter", fake_post)

    result = openrouter_ocr.ocr_logsheet_with_openrouter(
        b"fake image",
        "Oi_timecard_June_2026_All_Staff__page_01__staff_01__card_1.jpg",
        mime_type="image/jpeg",
        source_filename="Oi_timecard_June_2026_All_Staff.pdf",
        source_metadata={
            "source_type": "pdf_timecard_card",
            "source_page": 1,
            "source_staff_index": 1,
            "source_staff_name_hint": "Au Kin Wai Johnny",
            "source_card_no": 1,
        },
    )

    row = result["daily_rows"][0]
    assert row["name"] == "Au Kin Wai Johnny"
    assert "ocr_name" not in row
    assert row["name_identity_status"] == "roster_label"
    assert not row["warnings"]


def test_unmatched_pdf_label_rejects_handwritten_name_and_requires_roster_review(monkeypatch):
    def fake_post(payload, *, api_key):
        return {
            "model": "fake-model",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": json.dumps(
                            {
                                "document_type": "logsheet",
                                "month_year": "June 2026",
                                "daily_rows": [
                                    {
                                        "name": "Brand New OCR Name",
                                        "date": "8",
                                        "morning_in": "08:25",
                                        "afternoon_out": "18:30",
                                    }
                                ],
                            }
                        )
                    },
                }
            ],
            "usage": {"total_tokens": 10},
        }

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(openrouter_ocr, "_post_openrouter", fake_post)

    result = openrouter_ocr.ocr_logsheet_with_openrouter(
        b"fake image",
        "Oi_timecard_June_2026_All_Staff__page_01__staff_01__card_1.jpg",
        mime_type="image/jpeg",
        source_filename="Oi_timecard_June_2026_All_Staff.pdf",
        source_metadata={
            "source_type": "pdf_timecard_card",
            "source_page": 1,
            "source_staff_index": 1,
            "source_staff_label": "Unknown Printed Label",
            "source_card_no": 1,
        },
    )

    row = result["daily_rows"][0]
    assert row["name"] is None
    assert "ocr_name" not in row
    assert row["source_staff_label"] == "Unknown Printed Label"
    assert row["name_identity_status"] == "unresolved_roster_label"
    assert any("Excel roster" in warning for warning in row["warnings"])


def test_merge_preserves_source_parts_from_multiple_cards():
    rows = openrouter_ocr.merge_logsheet_daily_rows(
        [
            {
                "name": "A",
                "date": "2025-01-14",
                "in": "09:45",
                "out": "20:15",
                "source_filename": "A.jpg",
                "source_card_no": "1",
                "source_part_filename": "A__card_1.jpg",
            },
            {
                "name": "A",
                "date": "2025-01-14",
                "in": "09:40",
                "out": "20:16",
                "source_filename": "A.jpg",
                "source_card_no": "2",
                "source_part_filename": "A__card_2.jpg",
            },
        ]
    )

    assert rows[0]["in"] == "09:40"
    assert rows[0]["out"] == "20:16"
    assert rows[0]["source_card_nos"] == ["1", "2"]
    assert rows[0]["source_part_filenames"] == ["A__card_1.jpg", "A__card_2.jpg"]


def test_normalize_uses_context_hint_for_month_year():
    rows = openrouter_ocr.normalize_logsheet_daily_rows(
        {"entries": [{"date": "21", "morning_in": "09:40", "afternoon_out": "18:46"}]},
        "Chan Ching Yee Jenny 2.jpg",
        context_hint="August 2025",
    )

    assert rows[0]["date"] == "2025-08-21"


def test_normalize_reads_nested_pdf_pages_and_sign_in_columns():
    rows = openrouter_ocr.normalize_logsheet_daily_rows(
        {
            "document_type": "logsheet",
            "pages": [
                {
                    "page": 1,
                    "daily_rows": [
                        {
                            "Helper Name": "Lee Mei Mei",
                            "Date": "5",
                            "Sign In": "09:14",
                            "Sign Out": "18:03",
                        }
                    ],
                }
            ],
        },
        "FM2026_gallery helper sign-in sheet_May.pdf",
        context_hint="May 2026",
    )

    assert rows == [
        {
            "name": "Lee Mei Mei",
            "date": "2026-05-05",
            "in": "09:14",
            "out": "18:03",
            "source_filename": "FM2026_gallery helper sign-in sheet_May.pdf",
            "source_filenames": ["FM2026_gallery helper sign-in sheet_May.pdf"],
            "all_times": ["09:14", "18:03"],
            "warnings": [],
        }
    ]


def test_normalize_does_not_use_generic_heritage_filename_as_staff_name():
    rows = openrouter_ocr.normalize_logsheet_daily_rows(
        {"entries": [{"name": "Helper A", "date": "5", "sign_in": "09:00", "sign_out": "18:00"}]},
        "heritage_may.pdf",
        context_hint="May 2026",
    )

    assert rows[0]["name"] == "Helper A"


def test_normalize_d_and_g_generic_date_filename_and_day_month_date():
    rows = openrouter_ocr.normalize_logsheet_daily_rows(
        {
            "daily_rows": [
                {"name": "LEE Sarah", "date": "1/5", "in": "10:00", "out": "21:15"},
                {"name": "Chan Suet Wah Sana", "date": "2 Apr", "in": "09:00", "out": "21:30"},
            ]
        },
        "1 and 2 Apr 1.jpg",
        context_hint="April 2026",
    )

    assert rows[0]["name"] == "LEE Sarah"
    assert rows[0]["date"] == "2026-05-01"
    assert rows[1]["name"] == "Chan Suet Wah Sana"
    assert rows[1]["date"] == "2026-04-02"


def test_normalize_d_and_g_keeps_visible_rows_without_times():
    rows = openrouter_ocr.normalize_logsheet_daily_rows(
        {
            "daily_rows": [
                {"name": "Chow Yee Ling Dilys", "date": "8"},
                {"name": "Ho Ka Yan", "date": "8", "in": "10:30", "out": "21:30"},
            ]
        },
        "8 Apr.jpg",
        context_hint="D&G project instruction:\nApril 2026",
    )

    assert len(rows) == 2
    assert rows[0]["name"] == "Chow Yee Ling Dilys"
    assert rows[0]["date"] == "2026-04-08"
    assert rows[0]["in"] is None
    assert rows[0]["out"] is None
    assert rows[0]["all_times"] == []
    assert rows[1]["in"] == "10:30"


def test_normalize_prefers_filename_staff_name_over_card_name():
    rows = openrouter_ocr.normalize_logsheet_daily_rows(
        {
            "staff_name": "ISLA",
            "entries": [{"name": "ISLA", "date": "21", "morning_in": "09:40", "afternoon_out": "18:46"}],
        },
        "Cheng Nuo Isla 2.jpg",
        context_hint="August 2025",
    )

    assert rows[0]["name"] == "Cheng Nuo Isla"


def test_prompt_warns_against_row_numbers_as_punch_times():
    prompt = openrouter_ocr._build_prompt(None, "Ku Yin Wah 1.jpg")

    assert "left-margin row number is the date/day only" in prompt
    assert "Never combine that row number with a nearby time" in prompt
    assert "SIGNATURE, CHECK, ADMIN" in prompt
    assert "same horizontal row" in prompt


def test_extracts_daily_rows_from_truncated_fenced_json():
    text = """```json
{
  "document_type": "logsheet",
  "staff_name": "ISLA",
  "month_year": "August 2025",
  "daily_rows": [
    {"name": "ISLA", "date": "18", "in": "13:40", "out": "20:15", "all_times": ["13:40", "20:15"], "warnings": []},
    {"name": "ISLA", "date": "20", "in": "09:41", "out": "20:15", "all_times": ["09:41", "14:05", "14:47", "20:15"], "warnings": []}
  ],
  "tables": [
"""

    parsed = openrouter_ocr._extract_json_object(text)
    rows = openrouter_ocr.normalize_logsheet_daily_rows(parsed, "Cheng Nuo Isla 2.jpg", context_hint="August 2025")

    assert parsed["staff_name"] == "ISLA"
    assert len(parsed["daily_rows"]) == 2
    assert rows[0]["name"] == "Cheng Nuo Isla"
    assert rows[0]["date"] == "2025-08-18"
    assert rows[0]["in"] == "13:40"
    assert rows[1]["out"] == "20:15"
