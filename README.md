# Solomon HR Schedule Parser Layer

This repository contains the deterministic Excel schedule parser layer for Oil Street schedules plus a local review web UI. It does not rebuild the old HR app or payroll export flow.

## Design

- Excel is the source of truth.
- Staff rows, date columns, raw schedule cells, and source coordinates are read deterministically with `openpyxl`.
- Workbooks are opened twice: `data_only=False` for formulas and `data_only=True` for cached/calculated values.
- AI must not read schedule grid data and is not required for tests.
- AI is represented only as an optional `ShiftRuleAIResolver` interface for future fallback of difficult legend text.
- Unknown shift codes are preserved as entries with warnings instead of being dropped.

## Install

```bash
python -m pip install -e ".[test]"
```

## Run Tests

```bash
python -m pytest
```

Real sample tests look for:

```text
tests/fixtures/schedules/Oil Street Jan 2025 Schedule.xlsx
tests/fixtures/schedules/Oil Street Apr 2025 Schedule.xlsx
```

If those files are absent, the real sample tests skip with a helpful message.

## CLI

Print full JSON:

```bash
python -m schedule_parser.oil_street path/to/schedule.xlsx --json
```

Print summary:

```bash
python -m schedule_parser.oil_street path/to/schedule.xlsx --summary
```

Summary includes selected sheet, layout type, header row, date count, staff count, entry count, shift code count, unknown shift codes, and warning count.

## Supported Layouts

### `direct_time_with_hours_columns`

Date columns may appear every second column, with an adjacent hours column. Schedule cells contain direct time ranges such as `9:45 - 20:15`. The adjacent numeric hours cell overrides calculated hours when valid.

### `shift_code_matrix_with_legend`

Date columns are usually continuous. Schedule cells contain shift codes such as `A`, `B`, `D`, `A1`, or inline overrides like `D (2pm - 8:15pm)`. Legend rows after the staff block define shift code times and may be grouped by sections such as `Tue - Sun`, `Mon`, `Public Holidays`, `Sunday`, or `Christmas Eve`.

## Diagnostics

`ParsedSchedule.diagnostics` reports:

- workbook sheet names
- selected sheet score
- layout confidence
- header row
- staff row range
- date count
- staff count
- entry count
- unknown shift codes
- whether AI was used
- warning count
- error count

When the parser is unsure, it keeps the raw cell value and coordinate, emits a warning, and preserves the schedule entry whenever possible.

## Local Web Interface

Install the local web dependency:

```bash
pip install -e ".[web]"
```

Run the web UI:

```bash
python -m schedule_parser.web
```

Open:

```text
http://127.0.0.1:5050
```

Upload an `.xlsx` or `.xlsm` Oil Street schedule to inspect the parsed output. The page shows summary counts, staff, date columns, shift rules, schedule entries, warnings, diagnostics, and raw `ParsedSchedule` JSON.

The entries table also supports a lightweight review flow:

- choose one option for slash/OR shift codes such as `A/C`
- manually fill start/end/hours for unresolved shift codes
- clear the matching warning once a manual correction is applied
- copy or download the corrected JSON

After both an Excel roster and OCR logsheet rows are available, the web UI automatically runs a Roster vs Logsheet comparison. It matches OCR rows back to parsed roster staff and dates, then shows:

- roster staff, OCR name, scheduled in/out, and actual in/out
- missing logsheet rows for roster shifts where the uploaded staff has no OCR row
- OCR punch rows that do not exist in the roster
- low-confidence or partial name matches for review
- late and early-leave minute checks using a 7-minute late grace window

The comparison endpoint is also available as JSON:

```text
POST /api/compare-roster
{
  "schedule": { "...": "ParsedSchedule JSON" },
  "ocr_rows": [{ "name": "ISLA", "date": "20", "in": "09:41", "out": "20:15" }]
}
```

### Logsheet OCR

The web UI can also OCR one or more logsheet images or PDFs through OpenRouter using Qwen3.6 35B A3B.

See [OCR_LOGSHEET.md](OCR_LOGSHEET.md) for the detailed OCR API, model, prompt, JSON, and comparison workflow.

Set the API key before starting the web UI:

```bash
$env:OPENROUTER_API_KEY="your_openrouter_key"
```

Or add a local `.env` file:

```text
openrouter="your_openrouter_key"
```

Optional environment variables:

```text
OPENROUTER_MODEL=qwen/qwen3.6-35b-a3b
OPENROUTER_PDF_ENGINE=mistral-ocr
OPENROUTER_REASONING_EFFORT=none
OPENROUTER_TIMEOUT_SECONDS=90
OPENROUTER_MAX_TOKENS=4096
```

Supported logsheet uploads are `.jpg`, `.jpeg`, `.png`, `.webp`, and `.pdf`. Image uploads are sent as multimodal image input. PDF uploads are sent through OpenRouter's file parser plugin before Qwen returns structured logsheet JSON.

For each worked date, OCR output is normalized into a table:

```text
name | date | in | out
```

`in` is the first readable punch time of the day, and `out` is the last readable punch time of the day. If multiple images are uploaded, rows with the same name and date are merged before calculating first in / last out. The browser processes selected logsheet files one by one and updates a progress bar after each file, so partial results remain visible during longer OCR runs.

This tool is still local-only for schedule parsing and review. It does not export payroll or connect to the old HR app.
