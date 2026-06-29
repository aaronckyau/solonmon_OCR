# Solomon HR Schedule Parser Layer

This repository contains only the deterministic Excel schedule parser layer for Oil Street schedules. It does not rebuild the Flask app, OCR flow, payroll export, or frontend UI.

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

This tool is only for inspecting parser output. It does not run OCR, export payroll, call AI, connect to the old app, or use any external network service.
