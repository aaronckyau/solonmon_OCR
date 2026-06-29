const state = {
  response: null,
  schedule: null,
  originalSchedule: null,
  entries: [],
};

const els = {
  file: document.getElementById("scheduleFile"),
  parse: document.getElementById("parseButton"),
  clear: document.getElementById("clearButton"),
  status: document.getElementById("statusLine"),
  summary: document.getElementById("summarySection"),
  messages: document.getElementById("messagesList"),
  dateColumns: document.getElementById("dateColumnsBody"),
  staff: document.getElementById("staffBody"),
  shiftTimes: document.getElementById("shiftTimesBody"),
  entries: document.getElementById("entriesBody"),
  entryCount: document.getElementById("entryCount"),
  search: document.getElementById("entrySearch"),
  staffFilter: document.getElementById("staffFilter"),
  unresolvedOnly: document.getElementById("unresolvedOnly"),
  warningsOnly: document.getElementById("warningsOnly"),
  diagnostics: document.getElementById("diagnosticsJson"),
  rawJson: document.getElementById("rawJson"),
  resetReview: document.getElementById("resetReviewButton"),
  copyJson: document.getElementById("copyJsonButton"),
  downloadJson: document.getElementById("downloadJsonButton"),
};

els.parse.addEventListener("click", parseSelectedFile);
els.clear.addEventListener("click", clearPage);
els.search.addEventListener("input", renderEntries);
els.staffFilter.addEventListener("change", renderEntries);
els.unresolvedOnly.addEventListener("change", renderEntries);
els.warningsOnly.addEventListener("change", renderEntries);
els.entries.addEventListener("click", handleEntryReviewClick);
els.resetReview.addEventListener("click", resetReview);
els.copyJson.addEventListener("click", copyJson);
els.downloadJson.addEventListener("click", downloadJson);

function setStatus(message, isError = false) {
  els.status.textContent = message;
  els.status.classList.toggle("error", isError);
}

async function parseSelectedFile() {
  const file = els.file.files[0];
  if (!file) {
    setStatus("請先選擇排班 Excel 檔。", true);
    return;
  }
  const form = new FormData();
  form.append("schedule", file);
  setStatus("解析中...");
  els.parse.disabled = true;
  try {
    const response = await fetch("/api/parse", { method: "POST", body: form });
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "解析失敗。");
    }
    state.response = payload;
    state.schedule = payload.schedule;
    state.originalSchedule = deepClone(payload.schedule);
    state.entries = payload.schedule.entries || [];
    renderAll();
    setStatus("解析完成。");
  } catch (error) {
    setStatus(error.message || String(error), true);
  } finally {
    els.parse.disabled = false;
  }
}

function clearPage() {
  state.response = null;
  state.schedule = null;
  state.originalSchedule = null;
  state.entries = [];
  els.file.value = "";
  els.search.value = "";
  els.staffFilter.innerHTML = '<option value="">全部員工</option>';
  els.unresolvedOnly.checked = false;
  els.warningsOnly.checked = false;
  els.summary.innerHTML = "";
  els.messages.textContent = "尚未解析排班表。";
  els.messages.className = "message-list empty";
  clearTable(els.dateColumns);
  clearTable(els.staff);
  clearTable(els.shiftTimes);
  clearTable(els.entries);
  els.entryCount.textContent = "0 筆";
  els.diagnostics.textContent = "";
  els.rawJson.textContent = "";
  setStatus("就緒");
}

function renderAll() {
  const schedule = state.schedule;
  renderSummary(state.response.summary || {});
  renderMessages(schedule.warnings || [], schedule.errors || []);
  renderDateColumns(schedule.date_columns || []);
  renderStaff(schedule.staff || []);
  renderShiftTimes(schedule.shift_times || {});
  renderStaffFilter(schedule.staff || []);
  renderEntries();
  els.diagnostics.textContent = pretty(schedule.diagnostics || {});
  els.rawJson.textContent = pretty(schedule);
}

function renderSummary(summary) {
  const reviewedCount = countReviewedEntries();
  const cards = [
    ["檔案名稱", summary.source_filename],
    ["工作表", summary.sheet_name],
    ["版型", summary.layout_type],
    ["表頭列", summary.header_row],
    ["日期數", summary.date_count],
    ["員工數", summary.staff_count],
    ["排班筆數", summary.entry_count],
    ["班次規則數", summary.shift_time_count],
    ["警告數", summary.warning_count],
    ["錯誤數", summary.error_count],
    ["已修正", reviewedCount],
    ["使用 AI", summary.ai_used ? "是" : "否"],
  ];
  els.summary.innerHTML = cards.map(([label, value]) => (
    `<div class="summary-card"><div class="label">${escapeHtml(label)}</div><div class="value">${escapeHtml(display(value))}</div></div>`
  )).join("");
}

function renderMessages(warnings, errors) {
  const items = [
    ...warnings.map((item) => ({ ...item, kind: "warning" })),
    ...errors.map((item) => ({ ...item, kind: "error", severity: "error" })),
  ];
  if (!items.length) {
    els.messages.textContent = "沒有警告或錯誤。";
    els.messages.className = "message-list empty";
    return;
  }
  els.messages.className = "message-list";
  els.messages.innerHTML = items.map((item) => (
    `<div class="message-item ${item.kind === "error" ? "error" : ""}">
      <div><strong>${escapeHtml(item.code || item.kind)}</strong> ${escapeHtml(item.message || "")}</div>
      <div class="message-meta">${escapeHtml(messageSeverityLabel(item.severity || item.kind))}${item.cell ? " · " + escapeHtml(item.cell) : ""}</div>
    </div>`
  )).join("");
}

function renderDateColumns(rows) {
  renderTable(els.dateColumns, rows, (row) => [
    row.date,
    row.letter,
    row.column,
    display(row.raw_value),
    row.formula || "",
    row.source,
  ]);
}

function renderStaff(rows) {
  renderTable(els.staff, rows, (row) => [
    row.row,
    row.name,
    row.staff_id,
    row.phone_last4,
    compactJson(row.source_cells || {}),
  ]);
}

function renderShiftTimes(shiftTimes) {
  const rows = Object.entries(shiftTimes).map(([key, value]) => ({ key, ...value }));
  renderTable(els.shiftTimes, rows, (row) => [
    row.code || row.key,
    row.start,
    row.end,
    display(row.hours),
    row.applies_to || "",
    row.source || "",
    row.source_cell || "",
    row.source_text || "",
  ]);
}

function renderStaffFilter(staffRows) {
  const current = els.staffFilter.value;
  const names = [...new Set(staffRows.map((row) => row.name).filter(Boolean))].sort();
  els.staffFilter.innerHTML = '<option value="">全部員工</option>' + names.map((name) => (
    `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`
  )).join("");
  if (names.includes(current)) {
    els.staffFilter.value = current;
  }
}

function renderEntries() {
  const query = els.search.value.trim().toLowerCase();
  const staffName = els.staffFilter.value;
  const unresolvedOnly = els.unresolvedOnly.checked;
  const warningsOnly = els.warningsOnly.checked;
  const indexedEntries = state.entries.map((entry, index) => ({ entry, index }));
  const filtered = indexedEntries.filter(({ entry }) => {
    if (staffName && entry.staff_name !== staffName) return false;
    if (unresolvedOnly && !String(entry.resolution_source || "").startsWith("unresolved")) return false;
    if (warningsOnly && !(entry.warnings || []).length) return false;
    if (!query) return true;
    return [
      entry.date,
      entry.staff_name,
      entry.schedule_cell,
      entry.raw_value,
      entry.raw_shift_code,
      entry.shift_code,
      formatShiftOptions(entry),
      entry.resolution_source,
      (entry.warnings || []).join(" "),
    ].some((value) => display(value).toLowerCase().includes(query));
  });
  els.entryCount.textContent = `${filtered.length} / ${state.entries.length} 筆`;
  renderTable(els.entries, filtered, ({ entry, index }) => [
    entry.date,
    entry.staff_name,
    entry.schedule_cell,
    display(entry.raw_value),
    entry.raw_shift_code,
    entry.shift_code,
    formatShiftOptions(entry),
    entry.scheduled_in,
    entry.scheduled_out,
    display(entry.scheduled_hours),
    entry.resolution_source,
    (entry.warnings || []).join(", "),
    htmlCell(renderReviewControls(entry, index)),
  ], ({ entry }) => {
    if (String(entry.resolution_source || "").startsWith("unresolved")) return "error-row";
    if ((entry.warnings || []).length) return "warning-row";
    if (entry.review) return "reviewed-row";
    return "";
  });
}

function renderTable(tbody, rows, cellsForRow, classForRow = () => "") {
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="20" class="muted">沒有資料。</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map((row) => {
    const cells = cellsForRow(row).map((value) => {
      if (value && typeof value === "object" && Object.hasOwn(value, "__html")) {
        return `<td>${value.__html}</td>`;
      }
      return `<td>${escapeHtml(display(value))}</td>`;
    }).join("");
    const klass = classForRow(row);
    return `<tr${klass ? ` class="${klass}"` : ""}>${cells}</tr>`;
  }).join("");
}

function clearTable(tbody) {
  tbody.innerHTML = "";
}

async function copyJson() {
  if (!state.schedule) {
    setStatus("沒有可複製的 JSON。", true);
    return;
  }
  await navigator.clipboard.writeText(pretty(state.schedule));
  setStatus("JSON 已複製。");
}

function downloadJson() {
  if (!state.schedule) {
    setStatus("沒有可下載的 JSON。", true);
    return;
  }
  const blob = new Blob([pretty(state.schedule)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  const filename = (state.schedule.source_filename || "parsed_schedule").replace(/\.[^.]+$/, "");
  anchor.href = url;
  anchor.download = `${filename}.corrected.json`;
  anchor.click();
  URL.revokeObjectURL(url);
  setStatus("修正 JSON 下載已開始。");
}

function resetReview() {
  if (!state.originalSchedule) {
    setStatus("沒有可重設的修正。", true);
    return;
  }
  state.schedule = deepClone(state.originalSchedule);
  state.entries = state.schedule.entries || [];
  renderAll();
  setStatus("已重設所有修正。");
}

function handleEntryReviewClick(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const index = Number(button.dataset.entryIndex);
  const entry = state.entries[index];
  if (!entry) return;
  if (button.dataset.action === "apply-option") {
    applyOptionSelection(index, entry);
    return;
  }
  if (button.dataset.action === "apply-manual") {
    applyManualCorrection(index, entry);
  }
}

function applyOptionSelection(index, entry) {
  const select = els.entries.querySelector(`select[data-entry-index="${index}"]`);
  const selectedCode = select?.value || "";
  const option = (entry.shift_options || []).find((item) => item.code === selectedCode);
  if (!option) {
    setStatus("請先選擇班次選項。", true);
    return;
  }
  entry.shift_code = option.code;
  entry.scheduled_in = option.start || "";
  entry.scheduled_out = option.end || "";
  entry.scheduled_hours = option.hours ?? calculateHours(option.start, option.end);
  entry.resolution_source = "manual_or_selection";
  entry.warnings = [];
  clearScheduleWarningsForEntry(entry);
  entry.selected_shift_option = option;
  entry.review = {
    status: "selected_option",
    raw_shift_code: entry.raw_shift_code,
    selected_code: option.code,
  };
  refreshAfterReview(`已套用 ${entry.raw_shift_code} -> ${option.code}。`);
}

function applyManualCorrection(index, entry) {
  const start = valueForReviewInput(index, "start");
  const end = valueForReviewInput(index, "end");
  const hoursText = valueForReviewInput(index, "hours");
  const code = valueForReviewInput(index, "code") || entry.shift_code || entry.raw_shift_code;
  if (!isValidTime(start) || !isValidTime(end)) {
    setStatus("請輸入 HH:MM 格式的上班和下班時間。", true);
    return;
  }
  const manualHours = hoursText === "" ? calculateHours(start, end) : Number(hoursText);
  if (!Number.isFinite(manualHours) || manualHours < 0 || manualHours > 24) {
    setStatus("請輸入有效時數。", true);
    return;
  }
  entry.shift_code = code;
  entry.scheduled_in = start;
  entry.scheduled_out = end;
  entry.scheduled_hours = roundHours(manualHours);
  entry.resolution_source = "manual";
  entry.warnings = [];
  clearScheduleWarningsForEntry(entry);
  entry.review = {
    status: "manual_time",
    raw_shift_code: entry.raw_shift_code,
  };
  refreshAfterReview(`已套用 ${entry.schedule_cell} 的人工修正。`);
}

function refreshAfterReview(message) {
  refreshSummaryWarningCount();
  renderMessages(state.schedule.warnings || [], state.schedule.errors || []);
  renderSummary(state.response?.summary || {});
  renderEntries();
  els.rawJson.textContent = pretty(state.schedule);
  setStatus(message);
}

function clearScheduleWarningsForEntry(entry) {
  if (!state.schedule || !Array.isArray(state.schedule.warnings)) return;
  state.schedule.warnings = state.schedule.warnings.filter((warning) => warning.cell !== entry.schedule_cell);
}

function refreshSummaryWarningCount() {
  if (state.response?.summary) {
    state.response.summary.warning_count = (state.schedule?.warnings || []).length;
  }
  if (state.schedule?.diagnostics) {
    state.schedule.diagnostics.warning_count = (state.schedule.warnings || []).length;
  }
}

function formatShiftOptions(entry) {
  const options = entry.shift_options || [];
  if (entry.resolution_source === "or_equivalent" && entry.shift_code && entry.scheduled_in && entry.scheduled_out) {
    return `${entry.shift_code} ${entry.scheduled_in}-${entry.scheduled_out}`;
  }
  if (!options.length) return "";
  return options.map((option) => {
    const time = option.start && option.end ? `${option.start}-${option.end}` : "";
    const hours = option.hours !== null && option.hours !== undefined ? ` (${option.hours})` : "";
    return `${option.code}${time ? " " + time : ""}${hours}`;
  }).join(" / ");
}

function renderReviewControls(entry, index) {
  if (entry.review) {
    return `<div class="review-badge">已修正</div>`;
  }
  const options = entry.shift_options || [];
  if (options.length) {
    const optionTags = options.map((option) => (
      `<option value="${escapeAttr(option.code)}">${escapeHtml(formatOptionLabel(option))}</option>`
    )).join("");
    return `
      <div class="review-controls">
        <select data-entry-index="${index}" aria-label="班次選項">${optionTags}</select>
        <button type="button" class="mini-button" data-action="apply-option" data-entry-index="${index}">套用</button>
      </div>
    `;
  }
  if (String(entry.resolution_source || "").startsWith("unresolved") || (entry.warnings || []).length) {
    return `
      <div class="review-controls manual-review">
        <input class="review-input" data-review-field="code" data-entry-index="${index}" value="${escapeAttr(entry.shift_code || entry.raw_shift_code || "")}" placeholder="代碼">
        <input class="review-input time-input" data-review-field="start" data-entry-index="${index}" placeholder="上班 HH:MM">
        <input class="review-input time-input" data-review-field="end" data-entry-index="${index}" placeholder="下班 HH:MM">
        <input class="review-input hours-input" data-review-field="hours" data-entry-index="${index}" placeholder="時數">
        <button type="button" class="mini-button" data-action="apply-manual" data-entry-index="${index}">套用</button>
      </div>
    `;
  }
  return "";
}

function formatOptionLabel(option) {
  const time = option.start && option.end ? `${option.start}-${option.end}` : "";
  const hours = option.hours !== null && option.hours !== undefined ? ` ${option.hours}h` : "";
  return `${option.code}${time ? " " + time : ""}${hours}`;
}

function valueForReviewInput(index, field) {
  const input = els.entries.querySelector(`[data-review-field="${field}"][data-entry-index="${index}"]`);
  return input ? input.value.trim() : "";
}

function isValidTime(value) {
  return /^\d{2}:\d{2}$/.test(value);
}

function calculateHours(start, end) {
  if (!isValidTime(start) || !isValidTime(end)) return null;
  const [startHour, startMinute] = start.split(":").map(Number);
  const [endHour, endMinute] = end.split(":").map(Number);
  let startMinutes = startHour * 60 + startMinute;
  let endMinutes = endHour * 60 + endMinute;
  if (endMinutes <= startMinutes) endMinutes += 24 * 60;
  return roundHours((endMinutes - startMinutes) / 60);
}

function roundHours(value) {
  return Math.round(Number(value) * 100) / 100;
}

function countReviewedEntries() {
  return state.entries.filter((entry) => entry.review).length;
}

function htmlCell(value) {
  return { __html: value };
}

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

function messageSeverityLabel(value) {
  const labels = {
    info: "資訊",
    warning: "警告",
    error: "錯誤",
  };
  return labels[String(value || "").toLowerCase()] || value;
}

function display(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return compactJson(value);
  return String(value);
}

function compactJson(value) {
  return JSON.stringify(value);
}

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}
