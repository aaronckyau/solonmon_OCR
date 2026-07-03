# Logsheet OCR 說明

本文件說明本 repo 的 Logsheet OCR 如何運作、使用哪個 model / API，以及輸入輸出格式。

## 使用的 API 和 Model

OCR 功能使用 OpenRouter Chat Completions API：

```text
https://openrouter.ai/api/v1/chat/completions
```

預設 model：

```text
qwen/qwen3.6-35b-a3b
```

PDF 預設 parser engine：

```text
mistral-ocr
```

相關程式碼：

```text
schedule_parser/openrouter_ocr.py
schedule_parser/web.py
```

## 設定 API Key

程式會依序讀取以下環境變數或 `.env` key：

```text
OPENROUTER_API_KEY
OPENROUTER
openrouter
```

建議在本機 `.env` 放：

```text
openrouter="your_openrouter_key"
```

不要 commit `.env`，也不要把 key 寫入文件或測試輸出。

## 可調整的環境變數

```text
OPENROUTER_MODEL=qwen/qwen3.6-35b-a3b
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_PDF_ENGINE=mistral-ocr
OPENROUTER_REASONING_EFFORT=none
OPENROUTER_TIMEOUT_SECONDS=90
OPENROUTER_MAX_TOKENS=4096
OPENROUTER_SITE_URL=
OPENROUTER_APP_NAME=Solonmon OCR
```

`OPENROUTER_REASONING_EFFORT=none` 是刻意設定，目的是減少 reasoning token 佔用輸出空間，避免 OCR JSON 被截斷。

## 支援檔案

Web UI 支援上傳一個或多個 logsheet 檔案：

```text
.jpg
.jpeg
.png
.webp
.pdf
```

圖片會送成 OpenRouter multimodal message 的 `image_url`。

圖片預設會先做 OCR 前影像增強，然後以 JPEG 送出；PDF 不會做影像增強。
如果某張圖片無法處理，系統會 fallback 使用原圖 bytes。
Web UI 可以取消勾選「影像增強」來直接送原圖。

PDF 會送成 message content 的 `file`，並使用 OpenRouter plugin：

```json
{
  "plugins": [
    {
      "id": "file-parser",
      "pdf": {
        "engine": "mistral-ocr"
      }
    }
  ]
}
```

## OCR 流程

1. 使用者在 web UI 上傳 logsheet 圖片或 PDF。
2. 前端逐個檔案呼叫：

```text
POST /api/ocr-logsheet
```

3. 後端讀取檔案 bytes，判斷 MIME type。
4. 如果是圖片且「影像增強」開啟，後端會做保守 preprocessing：
   - EXIF 方向校正。
   - 透明背景轉白底 RGB。
   - 長邊調整到約 2200-2800px。
   - 輕微 autocontrast、contrast、sharpen。
   - 不自動裁切卡面，避免切走姓名、日期、欄名。
5. 後端建立 OpenRouter payload。
6. OpenRouter / Qwen 回傳文字內容。
7. 後端從文字內容抽出 JSON。
8. 後端把 JSON 正規化成 `daily_rows`。
9. 多個檔案的結果會合併，同一個 `name + date` 只保留一筆。
10. 每日 `in` 取最早 readable punch time，`out` 取最晚 readable punch time。
11. 前端顯示 OCR 表格和 raw OCR JSON。

## Prompt 規則

系統 prompt 要求 model 只回傳 compact valid JSON，不要 markdown、不要解釋文字。

核心規則：

- 每個有打卡的日期只輸出一筆 row。
- 同一天所有 MORNING / AFTERNOON / OVER TIME 欄位中的 readable punch time 都要收集。
- `in` 必須是該日最早時間。
- `out` 必須是該日最晚時間。
- 如果只有一個 readable punch time，該時間放在 `in`，`out` 用 `null`。
- Oil Street 打卡紙以檔名作為 staff name 的優先來源，例如 `Cheng Nuo Isla 2.jpg` 會輸出 `Cheng Nuo Isla`；卡上讀到的短名或暱稱不會覆蓋檔名。
- 如果卡上月份年份空白，只能從檔名、路徑或使用者補充 prompt 推斷；否則日期保留為日號。
- 不確定事項放入 Traditional Chinese `warnings`。

## 建議使用 Prompt

如果 logsheet 卡片沒有月份年份，請在 UI 的補充欄輸入：

```text
August 2025
```

或其他實際月份年份。這樣日號 `20` 可以正規化成 `2025-08-20`。

## OCR JSON 格式

OpenRouter 回傳後，程式期望或正規化成以下格式：

```json
{
  "document_type": "logsheet",
  "staff_name": null,
  "month_year": null,
  "daily_rows": [
    {
      "name": "Cheng Nuo Isla",
      "date": "2025-08-20",
      "in": "09:41",
      "out": "20:15",
      "all_times": ["09:41", "14:47", "20:15"],
      "warnings": []
    }
  ],
  "warnings": []
}
```

Web API 回傳外層格式：

```json
{
  "ok": true,
  "ocr": {
    "source_count": 1,
    "source_filename": "Cheng Nuo Isla 2.jpg",
    "configured_model": "qwen/qwen3.6-35b-a3b",
    "response_model": "qwen/qwen3.6-35b-a3b-20260415",
    "finish_reason": "stop",
    "daily_rows": [],
    "structured": {},
    "results": [],
    "usage": {}
  }
}
```

## 多檔案處理

前端不是一次把所有檔案丟給 model，而是逐個檔案 OCR：

```text
file 1 -> /api/ocr-logsheet
file 2 -> /api/ocr-logsheet
file 3 -> /api/ocr-logsheet
```

好處：

- 可以顯示 progress bar。
- 某一張失敗不會令全部結果消失。
- 已完成的 OCR rows 會即時顯示。
- 同一員工同一日期的 rows 會合併。

## Roster vs Logsheet 核對

當 Excel roster 已解析，且 OCR 有 `daily_rows` 後，前端會自動呼叫：

```text
POST /api/compare-roster
```

payload：

```json
{
  "schedule": {},
  "ocr_rows": [
    {
      "name": "ISLA",
      "date": "20",
      "in": "09:41",
      "out": "20:15"
    }
  ]
}
```

核對邏輯在：

```text
schedule_parser/roster_compare.py
```

核對方式：

- 用 OCR name 對 parsed roster staff name。
- 支援 partial name，例如 `ISLA` 可配對 `Cheng Nuo Isla`，但會標示姓名需覆核。
- 用日期配對 roster entry 和 OCR daily row。
- 如果 OCR 只有日號，會用 roster 內唯一符合的日期推斷完整日期。
- 有 roster 但沒有 OCR row，標示 `Missing Logsheet`。
- 有 OCR row 但 roster 沒有該日排班，標示 `Unscheduled Punch`。
- 有 partial / fuzzy name match，標示 `Name Check`。
- 也會計算遲到和早退分鐘。

## 本機使用流程

啟動 web UI：

```bash
python -m schedule_parser.web
```

打開：

```text
http://127.0.0.1:5050
```

操作順序：

1. 上傳 Oil Street Excel roster。
2. 按 `解析`。
3. 上傳一張或多張 logsheet 圖片 / PDF。
4. 如卡片沒有月份年份，在補充欄填入月份年份，例如 `August 2025`。
5. 按 `OCR Logsheet`。
6. 查看 `OCR 表格`。
7. 查看 `Roster vs Logsheet 核對`。

## 測試和檢查

建議修改 OCR 或核對邏輯後跑：

```bash
python -m compileall schedule_parser
python -m pytest
node --check schedule_parser/static/parser_app.js
```

如果只改 Markdown 文件，不需要跑 OCR API。
