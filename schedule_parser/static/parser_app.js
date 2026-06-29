const state = {
  response: null,
  schedule: null,
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
  copyJson: document.getElementById("copyJsonButton"),
  downloadJson: document.getElementById("downloadJsonButton"),
};

els.parse.addEventListener("click", parseSelectedFile);
els.clear.addEventListener("click", clearPage);
els.search.addEventListener("input", renderEntries);
els.staffFilter.addEventListener("change", renderEntries);
els.unresolvedOnly.addEventListener("change", renderEntries);
els.warningsOnly.addEventListener("change", renderEntries);
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
  const filtered = state.entries.filter((entry) => {
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
  renderTable(els.entries, filtered, (entry) => [
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
  ], (entry) => {
    if (String(entry.resolution_source || "").startsWith("unresolved")) return "error-row";
    if ((entry.warnings || []).length) return "warning-row";
    return "";
  });
}

function renderTable(tbody, rows, cellsForRow, classForRow = () => "") {
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="12" class="muted">沒有資料。</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map((row) => {
    const cells = cellsForRow(row).map((value) => `<td>${escapeHtml(display(value))}</td>`).join("");
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
  anchor.download = `${filename}.parsed.json`;
  anchor.click();
  URL.revokeObjectURL(url);
  setStatus("JSON 下載已開始。");
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
