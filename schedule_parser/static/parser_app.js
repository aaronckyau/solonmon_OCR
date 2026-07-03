const DEFAULT_LATE_GRACE_MINUTES = 8;
const DEFAULT_EARLY_LEAVE_GRACE_MINUTES = 0;
const DEFAULT_EARLY_IN_GRACE_MINUTES = 0;
const DEFAULT_OVERTIME_GRACE_MINUTES = 0;
const DEFAULT_GOVHK_HOLIDAY_YEAR = "2026";
const GOVHK_GENERAL_HOLIDAYS_BY_YEAR = {
  2025: [
    ["2025-01-01", "The first day of January"],
    ["2025-01-29", "Lunar New Year's Day"],
    ["2025-01-30", "The second day of Lunar New Year"],
    ["2025-01-31", "The third day of Lunar New Year"],
    ["2025-04-04", "Ching Ming Festival"],
    ["2025-04-18", "Good Friday"],
    ["2025-04-19", "The day following Good Friday"],
    ["2025-04-21", "Easter Monday"],
    ["2025-05-01", "Labour Day"],
    ["2025-05-05", "The Birthday of the Buddha"],
    ["2025-05-31", "Tuen Ng Festival"],
    ["2025-07-01", "Hong Kong Special Administrative Region Establishment Day"],
    ["2025-10-01", "National Day"],
    ["2025-10-07", "The day following the Chinese Mid-Autumn Festival"],
    ["2025-10-29", "Chung Yeung Festival"],
    ["2025-12-25", "Christmas Day"],
    ["2025-12-26", "The first weekday after Christmas Day"],
  ],
  2026: [
    ["2026-01-01", "The first day of January"],
    ["2026-02-17", "Lunar New Year's Day"],
    ["2026-02-18", "The second day of Lunar New Year"],
    ["2026-02-19", "The third day of Lunar New Year"],
    ["2026-04-03", "Good Friday"],
    ["2026-04-04", "The day following Good Friday"],
    ["2026-04-06", "The day following Ching Ming Festival"],
    ["2026-04-07", "The day following Easter Monday"],
    ["2026-05-01", "Labour Day"],
    ["2026-05-25", "The day following the Birthday of the Buddha"],
    ["2026-06-19", "Tuen Ng Festival"],
    ["2026-07-01", "Hong Kong Special Administrative Region Establishment Day"],
    ["2026-09-26", "The day following the Chinese Mid-Autumn Festival"],
    ["2026-10-01", "National Day"],
    ["2026-10-19", "The day following Chung Yeung Festival"],
    ["2026-12-25", "Christmas Day"],
    ["2026-12-26", "The first weekday after Christmas Day"],
  ],
  2027: [
    ["2027-01-01", "The first day of January"],
    ["2027-02-06", "Lunar New Year's Day"],
    ["2027-02-08", "The third day of Lunar New Year"],
    ["2027-02-09", "The fourth day of Lunar New Year"],
    ["2027-03-26", "Good Friday"],
    ["2027-03-27", "The day following Good Friday"],
    ["2027-03-29", "Easter Monday"],
    ["2027-04-05", "Ching Ming Festival"],
    ["2027-05-01", "Labour Day"],
    ["2027-05-13", "The Birthday of the Buddha"],
    ["2027-06-09", "Tuen Ng Festival"],
    ["2027-07-01", "Hong Kong Special Administrative Region Establishment Day"],
    ["2027-09-16", "The day following the Chinese Mid-Autumn Festival"],
    ["2027-10-01", "National Day"],
    ["2027-10-08", "Chung Yeung Festival"],
    ["2027-12-25", "Christmas Day"],
    ["2027-12-27", "The first weekday after Christmas Day"],
  ],
};
const GOVHK_GENERAL_HOLIDAY_YEARS = Object.keys(GOVHK_GENERAL_HOLIDAYS_BY_YEAR);
const SCHEDULE_SUMMARY_OVERRIDE_FIELDS = new Set([
  "days",
  "hours",
  "normalDays",
  "normalHours",
  "publicHolidayDays",
  "publicHolidayHours",
]);
const ALL_SCHEDULE_VARIANT_KEY = "__all__";
const DEFAULT_PROJECT_PROFILE = "oil_street";
const DEFAULT_EXPORT_TABLE_DATASET = "compare_rows";
const WORKFLOW_STEP_ORDER = ["project-select", "schedule-upload", "check-schedule", "log-upload", "manage-schedule", "export"];
const API_BASE_PATH = (document.body?.dataset.apiBase || "").replace(/\/+$/, "");
const PROJECT_PROFILES = {
  oil_street: {
    id: "oil_street",
    name: "Oil Street",
    eyebrow: "Oil Street 排班優先 OCR",
    title: "Oil Street 排班工作台",
    logSheetShortName: "打卡紙",
    logStepLabel: "3 上傳打卡紙",
    scheduleStepNote: "Excel 是排班資料的主要來源。讀取後會進入檢查排班，先確認班次時間再 OCR 打卡紙。",
    ocrTitle: "打卡紙 OCR",
    ocrIntro: "使用 OpenRouter Qwen3.6 35B A3B 辨識打卡紙圖片或 PDF，輸出每日首次上班 / 最後下班表格。",
    logUploadLabel: "上傳 logsheet 圖片 / PDF",
    ocrPromptPlaceholder: "可選：補充月份年份，例如 August 2025；或補充欄位規則。",
    ocrButtonLabel: "OCR 全部檔案",
    compareTitle: "排班 vs 打卡紙核對",
    sourceSidebarAriaLabel: "打卡紙來源文件",
    assignmentEmptyText: "上傳打卡紙後，可在這裡把檔案指派到正確員工。",
    detailPreviewLabel: "打卡紙預覽",
    detailPrevAriaLabel: "上一張打卡紙",
    detailNextAriaLabel: "下一張打卡紙",
    detailImageAlt: "員工打卡紙",
    detailEmptyText: "這位員工沒有可預覽的打卡紙圖片。",
    noFileMessage: "請先選擇打卡紙圖片或 PDF。",
    compareDoneMessage: "排班與打卡紙已重新核對。",
    waitingActualMessage: "已解析排班表，等待 OCR 打卡資料。",
    missingLogsheetLabel: "缺打卡紙",
  },
  heritage: {
    id: "heritage",
    name: "Heritage",
    eyebrow: "Heritage 排班優先 OCR",
    title: "Heritage 排班工作台",
    logSheetShortName: "Heritage log sheet",
    logStepLabel: "3 上傳 log sheet",
    scheduleStepNote: "Excel 是排班資料的主要來源。讀取後會進入檢查排班，先確認班次時間再 OCR Heritage log sheet / 簽到表。",
    ocrTitle: "Heritage log sheet OCR",
    ocrIntro: "使用 OpenRouter Qwen3.6 35B A3B 辨識 Heritage REGISTER FOR EXHIBITION HELPERS 簽到 / 簽出 PDF，輸出每日首次上班 / 最後下班表格。",
    logUploadLabel: "上傳 Heritage log sheet / 簽到表 PDF",
    ocrPromptPlaceholder: "可選：補充月份年份，例如 May 2026；或補充 Heritage sign-in sheet 欄位規則。",
    ocrButtonLabel: "OCR log sheet",
    compareTitle: "排班 vs Heritage log sheet 核對",
    sourceSidebarAriaLabel: "Heritage log sheet 來源文件",
    assignmentEmptyText: "上傳 Heritage log sheet 後，可在這裡把檔案指派到正確員工。",
    detailPreviewLabel: "Log sheet 預覽",
    detailPrevAriaLabel: "上一張 log sheet",
    detailNextAriaLabel: "下一張 log sheet",
    detailImageAlt: "員工 log sheet",
    detailEmptyText: "這位員工沒有可預覽的 log sheet 圖片。",
    noFileMessage: "請先選擇 Heritage log sheet PDF 或圖片。",
    compareDoneMessage: "排班與 Heritage log sheet 已重新核對。",
    waitingActualMessage: "已解析排班表，等待 OCR log sheet 資料。",
    missingLogsheetLabel: "缺 log sheet",
  },
  d_and_g: {
    id: "d_and_g",
    name: "D&G",
    eyebrow: "D&G 排班優先 OCR",
    title: "D&G 排班工作台",
    logSheetShortName: "D&G 工作紀錄",
    logStepLabel: "3 上傳工作紀錄",
    scheduleStepNote: "Excel 是 D&G Job Applications 排班資料來源。讀取後會進入檢查排班，先確認跨月份日期與時間再 OCR 工作紀錄相片。",
    ocrTitle: "D&G 工作紀錄 OCR",
    ocrIntro: "使用 OpenRouter Qwen3.6 35B A3B 辨識 D&G 促銷員工作紀錄相片，支援一張相片內有多張表格。",
    logUploadLabel: "上傳 D&G 工作紀錄圖片 / PDF",
    ocrPromptPlaceholder: "可選：補充月份年份，例如 April 2026；或說明相片內日期範圍。",
    ocrButtonLabel: "OCR 目前工作紀錄",
    compareTitle: "排班 vs D&G 工作紀錄核對",
    sourceSidebarAriaLabel: "D&G 工作紀錄來源文件",
    assignmentEmptyText: "上傳 D&G 工作紀錄後，可在這裡把檔案指派到正確員工。",
    detailPreviewLabel: "工作紀錄預覽",
    detailPrevAriaLabel: "上一張工作紀錄",
    detailNextAriaLabel: "下一張工作紀錄",
    detailImageAlt: "員工工作紀錄",
    detailEmptyText: "這位員工沒有可預覽的工作紀錄圖片。",
    noFileMessage: "請先選擇 D&G 工作紀錄圖片或 PDF。",
    compareDoneMessage: "排班與 D&G 工作紀錄已重新核對。",
    waitingActualMessage: "已解析排班表，等待 OCR 工作紀錄資料。",
    missingLogsheetLabel: "缺工作紀錄",
  },
};

const state = {
  projectProfile: DEFAULT_PROJECT_PROFILE,
  response: null,
  schedule: null,
  originalSchedule: null,
  scheduleVariants: [],
  selectedScheduleVariantKey: "",
  entries: [],
  ocr: null,
  comparison: null,
  lateGraceMinutes: DEFAULT_LATE_GRACE_MINUTES,
  earlyLeaveGraceMinutes: DEFAULT_EARLY_LEAVE_GRACE_MINUTES,
  countEarlyIn: false,
  earlyInGraceMinutes: DEFAULT_EARLY_IN_GRACE_MINUTES,
  countOvertime: false,
  overtimeGraceMinutes: DEFAULT_OVERTIME_GRACE_MINUTES,
  holidayCountSunday: false,
  holidayUseOfficial: true,
  officialHolidayYear: DEFAULT_GOVHK_HOLIDAY_YEAR,
  customHolidays: [],
  customHolidaySource: "",
  currentStep: "project-select",
  scheduleConfirmed: false,
  selectedRosterStaff: "",
  logsheetFiles: [],
  activeLogsheetFileKey: "",
  dngSheetRows: [],
  dngDraftRowsByFileKey: {},
  dngSheetBusy: false,
  rosterImageView: { x: 0, y: 0, scale: 1 },
  rosterImageDrag: null,
  rosterImageFileName: "",
  rosterImageIndex: 0,
  rosterIssuesExpanded: false,
  exportTableDataset: DEFAULT_EXPORT_TABLE_DATASET,
  exportTableUserSelected: false,
  exportTableSelection: {
    rows: new Set(),
    columns: new Set(),
    cells: new Set(),
  },
};

let comparisonRequestId = 0;

const els = {
  projectCards: [...document.querySelectorAll("[data-project-profile]")],
  projectCopyTargets: [...document.querySelectorAll("[data-project-copy]")],
  projectPlaceholderTargets: [...document.querySelectorAll("[data-project-placeholder]")],
  projectAriaTargets: [...document.querySelectorAll("[data-project-aria-label]")],
  projectAltTargets: [...document.querySelectorAll("[data-project-alt]")],
  file: document.getElementById("scheduleFile"),
  logsheetFile: document.getElementById("logsheetFile"),
  parse: document.getElementById("parseButton"),
  ocr: document.getElementById("ocrButton"),
  clear: document.getElementById("clearButton"),
  status: document.getElementById("statusLine"),
  ocrPrompt: document.getElementById("ocrPrompt"),
  ocrEnhanceImage: document.getElementById("ocrEnhanceImageInput"),
  ocrMeta: document.getElementById("ocrMeta"),
  ocrOutput: document.getElementById("ocrOutput"),
  ocrProgress: document.getElementById("ocrProgress"),
  ocrProgressText: document.getElementById("ocrProgressText"),
  ocrProgressCount: document.getElementById("ocrProgressCount"),
  ocrProgressBar: document.getElementById("ocrProgressBar"),
  ocrProgressList: document.getElementById("ocrProgressList"),
  ocrTableSection: document.getElementById("ocrTableSection"),
  ocrRowCount: document.getElementById("ocrRowCount"),
  ocrTableBody: document.getElementById("ocrTableBody"),
  compareStatus: document.getElementById("compareStatus"),
  compareButton: document.getElementById("compareButton"),
  lateGraceMinutes: document.getElementById("lateGraceMinutesInput"),
  earlyLeaveGraceMinutes: document.getElementById("earlyLeaveGraceMinutesInput"),
  countEarlyIn: document.getElementById("countEarlyInInput"),
  earlyInGraceMinutes: document.getElementById("earlyInGraceMinutesInput"),
  countOvertime: document.getElementById("countOvertimeInput"),
  overtimeGraceMinutes: document.getElementById("overtimeGraceMinutesInput"),
  compareSummary: document.getElementById("compareSummary"),
  compareRowCount: document.getElementById("compareRowCount"),
  compareTableBody: document.getElementById("compareTableBody"),
  compareOutput: document.getElementById("compareOutput"),
  logsheetAssignmentSummary: document.getElementById("logsheetAssignmentSummary"),
  logsheetAssignmentList: document.getElementById("logsheetAssignmentList"),
  dngSheetReviewPanel: document.getElementById("dngSheetReviewPanel"),
  dngSheetFileCount: document.getElementById("dngSheetFileCount"),
  dngSheetFileList: document.getElementById("dngSheetFileList"),
  dngSheetStatus: document.getElementById("dngSheetStatus"),
  dngPrevSheet: document.getElementById("dngPrevSheetButton"),
  dngNextSheet: document.getElementById("dngNextSheetButton"),
  dngOcrCurrent: document.getElementById("dngOcrCurrentButton"),
  dngSaveSheet: document.getElementById("dngSaveSheetButton"),
  dngAddRow: document.getElementById("dngAddRowButton"),
  dngSheetRows: document.getElementById("dngSheetRows"),
  dngSheetRowsSummary: document.getElementById("dngSheetRowsSummary"),
  dngSheetPreviewTitle: document.getElementById("dngSheetPreviewTitle"),
  dngSheetPreviewMeta: document.getElementById("dngSheetPreviewMeta"),
  dngSheetPreviewStage: document.getElementById("dngSheetPreviewStage"),
  dngSheetPreviewImage: document.getElementById("dngSheetPreviewImage"),
  dngSheetPreviewEmpty: document.getElementById("dngSheetPreviewEmpty"),
  summary: document.getElementById("summarySection"),
  messagesSection: document.getElementById("messagesSection"),
  messages: document.getElementById("messagesList"),
  scheduleVariantSection: document.getElementById("scheduleVariantSection"),
  scheduleVariantSelect: document.getElementById("scheduleVariantSelect"),
  scheduleVariantStatus: document.getElementById("scheduleVariantStatus"),
  dateColumns: document.getElementById("dateColumnsBody"),
  staff: document.getElementById("staffBody"),
  shiftTimes: document.getElementById("shiftTimesBody"),
  entriesTableHead: document.getElementById("entriesTableHead"),
  entries: document.getElementById("entriesBody"),
  entryCount: document.getElementById("entryCount"),
  search: document.getElementById("entrySearch"),
  staffFilter: document.getElementById("staffFilter"),
  unresolvedOnly: document.getElementById("unresolvedOnly"),
  warningsOnly: document.getElementById("warningsOnly"),
  holidaySunday: document.getElementById("holidaySundayInput"),
  holidayOfficial: document.getElementById("holidayOfficialInput"),
  holidayOfficialYear: document.getElementById("holidayOfficialYearInput"),
  holidayUpload: document.getElementById("holidayUploadInput"),
  holidayStatus: document.getElementById("holidayStatus"),
  diagnostics: document.getElementById("diagnosticsJson"),
  rawJson: document.getElementById("rawJson"),
  resetReview: document.getElementById("resetReviewButton"),
  copyJson: document.getElementById("copyJsonButton"),
  downloadJson: document.getElementById("downloadJsonButton"),
  exportTableDataset: document.getElementById("exportTableDatasetSelect"),
  exportTableIncludeHeaders: document.getElementById("exportTableIncludeHeadersInput"),
  exportTableSelectionStatus: document.getElementById("exportTableSelectionStatus"),
  exportTableHead: document.getElementById("exportTableHead"),
  exportTableBody: document.getElementById("exportTableBody"),
  copyExportTableSelection: document.getElementById("copyExportTableSelectionButton"),
  copyExportTableAll: document.getElementById("copyExportTableAllButton"),
  clearExportTableSelection: document.getElementById("clearExportTableSelectionButton"),
  copyOcr: document.getElementById("copyOcrButton"),
  downloadOcr: document.getElementById("downloadOcrButton"),
  workflowSteps: [...document.querySelectorAll("[data-workflow-step]")],
  stepPanels: [...document.querySelectorAll("[data-step-panel]")],
  workflowHint: document.getElementById("workflowHint"),
  workflowProgressFill: document.getElementById("workflowProgressFill"),
  confirmSchedule: document.getElementById("confirmScheduleButton"),
  rosterBody: document.getElementById("rosterBody"),
  rosterSummaryText: document.getElementById("rosterSummaryText"),
  rosterConfidence: document.getElementById("rosterConfidenceInput"),
  rosterShowZero: document.getElementById("rosterShowZeroInput"),
  rosterDetailModal: document.getElementById("rosterDetailModal"),
  rosterDetailTitle: document.getElementById("rosterDetailTitle"),
  rosterDetailMeta: document.getElementById("rosterDetailMeta"),
  rosterDetailRows: document.getElementById("rosterDetailRows"),
  rosterDetailClose: document.getElementById("rosterDetailCloseButton"),
  rosterDetailDone: document.getElementById("rosterDetailDoneButton"),
  rosterDetailAddRow: document.getElementById("rosterDetailAddRowButton"),
  rosterDetailHoursSummary: document.getElementById("rosterDetailHoursSummary"),
  rosterDetailImageTitle: document.getElementById("rosterDetailImageTitle"),
  rosterDetailPrevImage: document.getElementById("rosterDetailPrevImageButton"),
  rosterDetailNextImage: document.getElementById("rosterDetailNextImageButton"),
  rosterDetailResetImage: document.getElementById("rosterDetailResetImageButton"),
  rosterDetailImageCount: document.getElementById("rosterDetailImageCount"),
  rosterDetailImageEmpty: document.getElementById("rosterDetailImageEmpty"),
  rosterDetailImageStage: document.getElementById("rosterDetailImageStage"),
  rosterDetailImage: document.getElementById("rosterDetailImage"),
};

els.parse.addEventListener("click", parseSelectedFile);
els.ocr.addEventListener("click", ocrSelectedLogsheet);
els.logsheetFile?.addEventListener("change", handleLogsheetFileSelectionChange);
els.clear.addEventListener("click", clearPage);
els.confirmSchedule.addEventListener("click", confirmSchedule);
els.projectCards.forEach((button) => {
  button.addEventListener("click", () => selectProjectProfile(button.dataset.projectProfile));
});
els.workflowSteps.forEach((button) => {
  button.addEventListener("click", () => setWorkflowStep(button.dataset.workflowStep));
});
els.search.addEventListener("input", renderEntries);
els.staffFilter.addEventListener("change", renderEntries);
els.unresolvedOnly.addEventListener("change", renderEntries);
els.warningsOnly.addEventListener("change", renderEntries);
els.holidaySunday?.addEventListener("change", handleHolidayOptionsChange);
els.holidayOfficial?.addEventListener("change", handleHolidayOptionsChange);
els.holidayOfficialYear?.addEventListener("change", handleHolidayOptionsChange);
els.holidayUpload?.addEventListener("change", handleHolidayUploadChange);
els.scheduleVariantSelect?.addEventListener("change", handleScheduleVariantChange);
els.entries.addEventListener("click", handleEntryReviewClick);
els.entries.addEventListener("change", handleScheduleSummaryOverrideChange);
els.resetReview.addEventListener("click", resetReview);
els.copyJson.addEventListener("click", copyJson);
els.downloadJson.addEventListener("click", downloadJson);
els.exportTableDataset?.addEventListener("change", handleExportTableDatasetChange);
els.exportTableBody?.addEventListener("click", handleExportTableClick);
els.exportTableHead?.addEventListener("click", handleExportTableClick);
els.exportTableIncludeHeaders?.addEventListener("change", updateExportTableSelectionStatus);
els.copyExportTableSelection?.addEventListener("click", () => copyExportTableSelection("selected"));
els.copyExportTableAll?.addEventListener("click", () => copyExportTableSelection("all"));
els.clearExportTableSelection?.addEventListener("click", clearExportTableSelection);
els.copyOcr?.addEventListener("click", copyOcrJson);
els.downloadOcr?.addEventListener("click", downloadOcrJson);
els.compareButton.addEventListener("click", () => refreshRosterComparison({ userAction: true }));
els.logsheetAssignmentList?.addEventListener("change", handleLogsheetAssignmentChange);
els.logsheetAssignmentList?.addEventListener("click", handleLogsheetPreviewClick);
els.dngSheetFileList?.addEventListener("click", handleDngSheetFileClick);
els.dngPrevSheet?.addEventListener("click", () => shiftDngSheet(-1));
els.dngNextSheet?.addEventListener("click", () => shiftDngSheet(1));
els.dngOcrCurrent?.addEventListener("click", ocrCurrentDngSheet);
els.dngSaveSheet?.addEventListener("click", saveDngCurrentSheet);
els.dngAddRow?.addEventListener("click", addDngSheetRow);
els.dngSheetRows?.addEventListener("input", handleDngSheetRowsInput);
els.dngSheetRows?.addEventListener("change", handleDngSheetRowsChange);
els.dngSheetRows?.addEventListener("click", handleDngSheetRowsClick);
els.lateGraceMinutes?.addEventListener("change", handleGraceMinutesChange);
els.earlyLeaveGraceMinutes?.addEventListener("change", handleGraceMinutesChange);
els.countEarlyIn?.addEventListener("change", handleGraceMinutesChange);
els.earlyInGraceMinutes?.addEventListener("change", handleGraceMinutesChange);
els.countOvertime?.addEventListener("change", handleGraceMinutesChange);
els.overtimeGraceMinutes?.addEventListener("change", handleGraceMinutesChange);
els.rosterConfidence?.addEventListener("change", () => renderRosterSummary(state.comparison?.rows || []));
els.rosterShowZero?.addEventListener("change", () => renderRosterSummary(state.comparison?.rows || []));
els.rosterBody?.addEventListener("click", handleRosterClick);
els.rosterBody?.addEventListener("keydown", handleRosterKeydown);
els.rosterSummaryText?.addEventListener("click", handleRosterSummaryClick);
els.compareTableBody?.addEventListener("click", handleLogsheetPreviewClick);
els.rosterDetailRows?.addEventListener("change", handleRosterDetailChange);
els.rosterDetailRows?.addEventListener("paste", handleRosterDetailPaste);
els.rosterDetailRows?.addEventListener("click", handleRosterDetailClick);
els.rosterDetailClose?.addEventListener("click", closeRosterDetail);
els.rosterDetailDone?.addEventListener("click", closeRosterDetail);
els.rosterDetailAddRow?.addEventListener("click", addFirstMissingRosterActualRow);
els.rosterDetailModal?.addEventListener("click", (event) => {
  if (event.target === els.rosterDetailModal) closeRosterDetail();
});
els.rosterDetailPrevImage?.addEventListener("click", () => shiftRosterDetailImage(-1));
els.rosterDetailNextImage?.addEventListener("click", () => shiftRosterDetailImage(1));
els.rosterDetailResetImage?.addEventListener("click", resetRosterImageView);
els.rosterDetailImageStage?.addEventListener("wheel", handleRosterImageWheel, { passive: false });
els.rosterDetailImageStage?.addEventListener("pointerdown", handleRosterImagePointerDown);
els.rosterDetailImageStage?.addEventListener("pointermove", handleRosterImagePointerMove);
els.rosterDetailImageStage?.addEventListener("pointerup", endRosterImageDrag);
els.rosterDetailImageStage?.addEventListener("pointercancel", endRosterImageDrag);
els.rosterDetailImageStage?.addEventListener("dblclick", resetRosterImageView);
applyProjectProfileCopy();
renderHolidayStatus();
renderLogsheetAssignments();
renderDngSheetReview();
updateWorkflowState();

function apiUrl(path) {
  const cleanPath = String(path || "").replace(/^\/+/, "");
  return API_BASE_PATH ? `${API_BASE_PATH}/${cleanPath}` : `/${cleanPath}`;
}

async function readApiJson(response, fallbackMessage) {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return {
      ok: false,
      error: fallbackMessage || `API returned a non-JSON response (${response.status}).`,
    };
  }
}

function apiErrorMessage(error, endpoint) {
  const message = error?.message || String(error);
  if (/failed to fetch|networkerror|load failed/i.test(message)) {
    if (window.location.protocol === "file:") {
      return "無法連線到後端 API：請用 Flask 網址開啟此頁，不要直接打開 HTML 檔。";
    }
    return `無法連線到後端 API（${apiUrl(endpoint)}）。請確認目前頁面由同一個 Flask server 開啟，並重新整理頁面。`;
  }
  return message;
}

function currentProjectProfile() {
  return PROJECT_PROFILES[state.projectProfile] || PROJECT_PROFILES[DEFAULT_PROJECT_PROFILE];
}

function isDAndGProfile() {
  return state.projectProfile === "d_and_g";
}

function selectProjectProfile(profileId) {
  const nextProfileId = PROJECT_PROFILES[profileId] ? profileId : DEFAULT_PROJECT_PROFILE;
  state.projectProfile = nextProfileId;
  applyProjectProfileCopy();
  renderLogsheetAssignments();
  renderDngSheetReview();
  updateWorkflowState();
  setWorkflowStep("schedule-upload");
  setStatus(`${currentProjectProfile().name} 已選擇。`);
}

function applyProjectProfileCopy() {
  const profile = currentProjectProfile();
  document.title = profile.title;
  els.projectCopyTargets.forEach((node) => {
    const key = node.dataset.projectCopy;
    if (key && Object.hasOwn(profile, key)) {
      node.textContent = profile[key];
    }
  });
  els.projectPlaceholderTargets.forEach((node) => {
    const key = node.dataset.projectPlaceholder;
    if (key && Object.hasOwn(profile, key)) {
      node.setAttribute("placeholder", profile[key]);
    }
  });
  els.projectAriaTargets.forEach((node) => {
    const key = node.dataset.projectAriaLabel;
    if (key && Object.hasOwn(profile, key)) {
      node.setAttribute("aria-label", profile[key]);
    }
  });
  els.projectAltTargets.forEach((node) => {
    const key = node.dataset.projectAlt;
    if (key && Object.hasOwn(profile, key)) {
      node.setAttribute("alt", profile[key]);
    }
  });
  updateProjectProfileCards();
}

function updateProjectProfileCards() {
  els.projectCards.forEach((button) => {
    const isSelected = button.dataset.projectProfile === state.projectProfile;
    button.classList.toggle("is-selected", isSelected);
    button.setAttribute("aria-pressed", isSelected ? "true" : "false");
  });
}

function setStatus(message, isError = false) {
  els.status.textContent = message;
  els.status.classList.toggle("error", isError);
}

function setWorkflowStep(step) {
  if (!canVisitStep(step)) {
    setStatus(workflowBlockedMessage(step), true);
    return;
  }
  state.currentStep = step;
  updateWorkflowState();
}

function canVisitStep(step) {
  if (step === "project-select") return true;
  if (step === "schedule-upload") return true;
  if (step === "check-schedule") return Boolean(state.schedule);
  if (step === "log-upload") return Boolean(state.schedule && state.scheduleConfirmed);
  if (step === "manage-schedule") return Boolean(state.schedule && ocrRows().length);
  if (step === "export") return Boolean(state.schedule);
  return false;
}

function workflowBlockedMessage(step) {
  if (step === "check-schedule") return "請先上傳並讀取排班 Excel。";
  if (step === "log-upload") return "請先在檢查排班確認排班表。";
  if (step === "manage-schedule") return `請先完成${currentProjectProfile().logSheetShortName} OCR。`;
  if (step === "export") return "請先讀取排班 Excel。";
  return "目前不能進入這一步。";
}

function updateWorkflowState() {
  const stepIndex = workflowStepIndex(state.currentStep);
  els.stepPanels.forEach((panel) => {
    panel.hidden = panel.dataset.stepPanel !== state.currentStep;
  });
  els.workflowSteps.forEach((button) => {
    const step = button.dataset.workflowStep;
    const index = workflowStepIndex(step);
    button.disabled = !canVisitStep(step);
    button.classList.toggle("is-active", step === state.currentStep);
    button.classList.toggle("is-done", index < stepIndex && canVisitStep(step));
    if (step === state.currentStep) {
      button.setAttribute("aria-current", "step");
    } else {
      button.removeAttribute("aria-current");
    }
  });
  if (els.workflowProgressFill) {
    const maxIndex = Math.max(WORKFLOW_STEP_ORDER.length - 1, 1);
    const percent = Math.max(0, Math.min(100, (stepIndex / maxIndex) * 100));
    els.workflowProgressFill.style.width = `${percent}%`;
  }
  if (els.workflowHint) {
    els.workflowHint.textContent = workflowHintText();
  }
  if (els.confirmSchedule) {
    els.confirmSchedule.disabled = !state.schedule;
    els.confirmSchedule.textContent = state.scheduleConfirmed ? "排班表已確認" : "確認排班表";
  }
  els.ocr.disabled = !state.scheduleConfirmed;
  els.compareButton.disabled = !state.schedule || !ocrRows().length;
}

function workflowStepIndex(step) {
  return Math.max(0, WORKFLOW_STEP_ORDER.indexOf(step));
}

function workflowHintText() {
  const profile = currentProjectProfile();
  if (state.currentStep === "project-select") return "選擇 Oil Street、Heritage 或 D&G，然後上傳排班表。";
  if (!state.schedule) return `先上傳 ${profile.name} Excel 排班表。`;
  if (!state.scheduleConfirmed) return "檢查班次時間和未解析項目，確認後再 OCR。";
  if (!ocrRows().length) return `排班表已確認，可以上傳${profile.logSheetShortName}並執行 OCR。`;
  if (!state.comparison) return "OCR 已有資料，可以重新核對排班。";
  return "已完成核對，可匯出或繼續修正。";
}

function confirmSchedule() {
  if (!state.schedule) {
    setStatus("請先讀取排班 Excel。", true);
    return;
  }
  state.scheduleConfirmed = true;
  updateWorkflowState();
  setWorkflowStep("log-upload");
  setStatus(`排班表已確認，請上傳${currentProjectProfile().logSheetShortName}。`);
}

async function parseSelectedFile() {
  const file = els.file.files[0];
  if (!file) {
    setStatus("請先選擇排班 Excel 檔。", true);
    return;
  }
  const form = new FormData();
  form.append("schedule", file);
  form.append("project_profile", state.projectProfile);
  setStatus("解析中...");
  els.parse.disabled = true;
  try {
    const response = await fetch(apiUrl("/api/parse"), { method: "POST", body: form });
    const payload = await readApiJson(response, "讀取排班表失敗：API 回傳格式不正確。");
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "解析失敗。");
    }
    state.response = payload;
    state.scheduleVariants = normalizeScheduleVariants(payload);
    const selectedVariant = selectedScheduleVariant(payload.selected_schedule_key) || state.scheduleVariants[0];
    applyScheduleVariant(selectedVariant, { resetReviewState: false });
    state.officialHolidayYear = inferScheduleHolidayYear() || state.officialHolidayYear;
    state.scheduleConfirmed = false;
    state.comparison = null;
    renderAll();
    await refreshRosterComparison();
    setWorkflowStep("check-schedule");
    setStatus("排班表已讀取，請檢查班次時間後確認。");
  } catch (error) {
    setStatus(apiErrorMessage(error, "/api/parse"), true);
  } finally {
    els.parse.disabled = false;
  }
}

async function ocrSelectedLogsheet() {
  if (!state.schedule || !state.scheduleConfirmed) {
    setStatus("請先讀取並確認排班表，再執行 OCR。", true);
    setWorkflowStep(state.schedule ? "check-schedule" : "schedule-upload");
    return;
  }
  const files = Array.from(els.logsheetFile.files || []);
  if (!files.length) {
    setStatus(currentProjectProfile().noFileMessage, true);
    return;
  }
  rememberLogsheetFiles(files);
  if (isDAndGProfile()) {
    await ocrCurrentDngSheet();
    return;
  }
  const extraPrompt = els.ocrPrompt.value.trim();
  state.ocr = createOcrAggregate(files);
  renderOcrResult();
  showOcrProgress(files.length);
  setStatus(`OCR 辨識中 (${files.length} 個檔案)...`);
  els.ocr.disabled = true;
  try {
    for (let index = 0; index < files.length; index += 1) {
      const file = files[index];
      setOcrProgress(index, files.length, `正在 OCR：${file.name}`);
      markOcrProgressItem(file.name, "running", "處理中");
      try {
        const result = await ocrSingleFile(file, extraPrompt);
        addOcrResult(result);
        renderOcrResult();
        const rowCount = rowsFromOcrResult(result).length;
        if (rowCount === 0) {
          addOcrNoData(file.name);
          markOcrProgressItem(file.name, "no-data", "沒有辨識到打卡時間");
        } else {
          markOcrProgressItem(file.name, "done", `${rowCount} 筆`);
        }
      } catch (error) {
        const message = error.message || String(error);
        addOcrError(file.name, message);
        renderOcrResult();
        markOcrProgressItem(file.name, "error", message);
      }
      setOcrProgress(index + 1, files.length, `已完成 ${index + 1} / ${files.length}`);
    }
    const rows = ocrRows();
    if ((state.ocr.errors || []).length) {
      setStatus(`OCR 部分完成：${rows.length} 筆，${state.ocr.errors.length} 個檔案失敗。`, true);
    } else if ((state.ocr.no_data_files || []).length) {
      setStatus(`OCR 完成：${rows.length} 筆，${state.ocr.no_data_files.length} 個檔案沒有資料。`, true);
    } else {
      setStatus(`OCR 完成：${rows.length} 筆。`);
    }
    await refreshRosterComparison();
    if (ocrRows().length) setWorkflowStep("manage-schedule");
  } catch (error) {
    setStatus(error.message || String(error), true);
  } finally {
    els.ocr.disabled = false;
  }
}

function normalizeScheduleVariants(payload) {
  const variants = Array.isArray(payload.schedule_variants) ? payload.schedule_variants : [];
  const allVariant = payload.schedule ? {
    key: ALL_SCHEDULE_VARIANT_KEY,
    label: "全部月份",
    month: "",
    isAllMonths: true,
    summary: payload.summary || scheduleSummaryFromSchedule(payload.schedule),
    schedule: payload.schedule,
  } : null;
  if (variants.length) {
    const monthVariants = variants
      .filter((variant) => variant && variant.schedule)
      .map((variant, index) => ({
        key: String(variant.key || variant.month || `variant-${index + 1}`),
        label: String(variant.label || variant.month || `月份 ${index + 1}`),
        month: String(variant.month || ""),
        summary: variant.summary || scheduleSummaryFromSchedule(variant.schedule),
        schedule: variant.schedule,
      }));
    return allVariant ? [allVariant, ...monthVariants] : monthVariants;
  }
  return [{
    key: String(payload.schedule?.schedule_month || payload.schedule?.sheet_name || "schedule"),
    label: String(payload.schedule?.schedule_month_label || payload.schedule?.sheet_name || "排班表"),
    month: String(payload.schedule?.schedule_month || ""),
    summary: payload.summary || scheduleSummaryFromSchedule(payload.schedule),
    schedule: payload.schedule,
  }];
}

function selectedScheduleVariant(key) {
  if (!state.scheduleVariants.length) return null;
  return state.scheduleVariants.find((variant) => variant.key === key) || null;
}

function scheduleMonthKeyFromDate(date) {
  const text = String(date || "");
  return /^\d{4}-\d{2}-\d{2}$/.test(text) ? text.slice(0, 7) : "";
}

function scheduleMonthLabel(month) {
  const match = /^(\d{4})-(\d{2})$/.exec(String(month || ""));
  if (!match) return String(month || "");
  const date = new Date(Number(match[1]), Number(match[2]) - 1, 1);
  return date.toLocaleString("en", { month: "long", year: "numeric" });
}

function scheduleMonthField(month, metric) {
  return `month:${month}:${metric}`;
}

function isScheduleSummaryMonthField(field) {
  return /^month:\d{4}-\d{2}:(days|hours)$/.test(String(field || ""));
}

function scheduleSummaryMonthMetric(field) {
  const match = /^month:\d{4}-\d{2}:(days|hours)$/.exec(String(field || ""));
  return match ? match[1] : "";
}

function scheduleMonthColumnsFromRows(rows) {
  const months = new Map();
  rows.forEach((row) => {
    (row.scheduleMonths || []).forEach((month) => {
      if (month?.month && !months.has(month.month)) {
        months.set(month.month, {
          month: month.month,
          label: month.label || scheduleMonthLabel(month.month),
          daysField: month.daysField,
          hoursField: month.hoursField,
        });
      }
    });
  });
  return [...months.values()].sort((left, right) => left.month.localeCompare(right.month));
}

function applyScheduleVariant(variant, options = {}) {
  if (!variant?.schedule) return;
  state.selectedScheduleVariantKey = variant.key;
  state.schedule = deepClone(variant.schedule);
  state.originalSchedule = deepClone(variant.schedule);
  state.entries = state.schedule.entries || [];
  state.response = {
    ...(state.response || {}),
    schedule: state.schedule,
    summary: variant.summary || scheduleSummaryFromSchedule(state.schedule),
    selected_schedule_key: variant.key,
  };
  if (options.resetReviewState !== false) {
    state.scheduleConfirmed = false;
    state.comparison = null;
    clearComparison(currentProjectProfile().waitingActualMessage);
    setWorkflowStep("check-schedule");
    setStatus(`已切換至 ${variant.label}，請重新確認排班表。`);
  }
}

function scheduleSummaryFromSchedule(schedule) {
  const diagnostics = schedule?.diagnostics && typeof schedule.diagnostics === "object" ? schedule.diagnostics : {};
  return {
    source_filename: schedule?.source_filename || "",
    sheet_name: schedule?.sheet_name || "",
    schedule_month: schedule?.schedule_month || "",
    schedule_month_label: schedule?.schedule_month_label || "",
    layout_type: schedule?.layout_type || "",
    header_row: schedule?.header_row,
    date_count: (schedule?.date_columns || []).length,
    staff_count: (schedule?.staff || []).length,
    entry_count: (schedule?.entries || []).length,
    shift_time_count: Object.keys(schedule?.shift_times || {}).length,
    warning_count: diagnostics.warning_count ?? (schedule?.warnings || []).length,
    error_count: diagnostics.error_count ?? (schedule?.errors || []).length,
  };
}

function handleScheduleVariantChange() {
  const variant = selectedScheduleVariant(els.scheduleVariantSelect?.value || "");
  if (!variant) return;
  applyScheduleVariant(variant);
  renderAll();
}

function handleLogsheetFileSelectionChange() {
  const files = Array.from(els.logsheetFile?.files || []);
  rememberLogsheetFiles(files);
  renderLogsheetAssignments();
  renderDngSheetReview();
}

async function ocrSingleFile(file, extraPrompt) {
  const form = new FormData();
  form.append("logsheet", file);
  form.append("project_profile", state.projectProfile);
  if (extraPrompt) {
    form.append("prompt", extraPrompt);
  }
  form.append("enhance_image", els.ocrEnhanceImage?.checked === false ? "0" : "1");
  try {
    const response = await fetch(apiUrl("/api/ocr-logsheet"), { method: "POST", body: form });
    const payload = await readApiJson(response, "OCR 失敗：API 回傳格式不正確。");
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "OCR 失敗。");
    }
    return payload.ocr;
  } catch (error) {
    throw new Error(apiErrorMessage(error, "/api/ocr-logsheet"));
  }
}

function rememberLogsheetFiles(files) {
  const previousFiles = new Map((state.logsheetFiles || [])
    .map((file) => [logsheetFileKey(file.name), file]));
  revokeLogsheetFileUrls();
  state.logsheetFiles = files.map((file) => ({
    name: file.name,
    type: file.type || "",
    assignedStaff: previousFiles.get(logsheetFileKey(file.name))?.assignedStaff || "",
    ocrStatus: previousFiles.get(logsheetFileKey(file.name))?.ocrStatus || "Uploaded",
    ocrRows: previousFiles.get(logsheetFileKey(file.name))?.ocrRows || 0,
    reviewSaved: Boolean(previousFiles.get(logsheetFileKey(file.name))?.reviewSaved),
    ocrError: previousFiles.get(logsheetFileKey(file.name))?.ocrError || "",
    ocrResult: previousFiles.get(logsheetFileKey(file.name))?.ocrResult || null,
    previewUrl: isPreviewableLogsheetImage(file) ? URL.createObjectURL(file) : "",
  }));
  if (isDAndGProfile()) {
    syncDngOcrAggregateForFiles(files);
    if (!logsheetFileByKey(state.activeLogsheetFileKey)) {
      state.activeLogsheetFileKey = state.logsheetFiles[0] ? logsheetFileKey(state.logsheetFiles[0].name) : "";
    }
    state.dngSheetRows = loadDngDraftRows(state.activeLogsheetFileKey);
  }
  renderLogsheetAssignments();
  renderDngSheetReview();
}

function isPreviewableLogsheetImage(file) {
  const mimeType = String(file?.type || "").toLowerCase();
  if (mimeType.startsWith("image/")) return true;
  return /\.(jpe?g|png|webp)$/i.test(String(file?.name || ""));
}

function renderLogsheetAssignments() {
  if (!els.logsheetAssignmentList) return;
  const profile = currentProjectProfile();
  const files = state.logsheetFiles || [];
  const assignedCount = files.filter((file) => file.assignedStaff).length;
  if (els.logsheetAssignmentSummary) {
    els.logsheetAssignmentSummary.textContent = `${files.length} sheets${assignedCount ? ` / ${assignedCount} assigned` : ""}`;
  }
  if (!files.length) {
    els.logsheetAssignmentList.innerHTML = `<div class="logsheet-empty">${escapeHtml(profile.assignmentEmptyText)}</div>`;
    return;
  }
  const staffOptions = staffAssignmentOptions();
  els.logsheetAssignmentList.innerHTML = files.map((file, index) => {
    const key = logsheetFileKey(file.name);
    const inferred = staffNameFromFilename(file.name) || "-";
    const rowCount = ocrRowsForFileKey(key).length;
    const status = logsheetFileStatus(file.name, rowCount);
    const options = ['<option value="">Auto match</option>']
      .concat(staffOptions.map((name) => (
        `<option value="${escapeAttr(name)}"${file.assignedStaff === name ? " selected" : ""}>${escapeHtml(name)}</option>`
      )))
      .join("");
    return `
      <article class="logsheet-file-card${file.assignedStaff ? " is-assigned" : ""}">
        <div class="logsheet-file-index">${index + 1}</div>
        <div class="logsheet-file-body">
          <button type="button" class="logsheet-file-name" title="${escapeAttr(file.name)}" data-logsheet-preview-key="${escapeAttr(key)}">${escapeHtml(file.name)}</button>
          <div class="logsheet-file-meta">
            <span>${escapeHtml(status)}</span>
            <span>${rowCount} rows</span>
            <span>${file.previewUrl ? "Image" : "No preview"}</span>
          </div>
          <label class="logsheet-assign-control">
            <span>Point to staff</span>
            <select data-logsheet-file-key="${escapeAttr(key)}">${options}</select>
          </label>
          <div class="logsheet-file-hint">Filename: ${escapeHtml(inferred)}</div>
        </div>
      </article>
    `;
  }).join("");
}

function renderDngSheetReview() {
  if (!els.dngSheetReviewPanel) return;
  const enabled = isDAndGProfile();
  els.dngSheetReviewPanel.hidden = !enabled;
  if (!enabled) return;

  const files = state.logsheetFiles || [];
  if (els.dngSheetFileCount) {
    const savedCount = files.filter((file) => file.reviewSaved).length;
    els.dngSheetFileCount.textContent = `${files.length} sheets${files.length ? ` / ${savedCount} saved` : ""}`;
  }
  if (!files.length) {
    state.activeLogsheetFileKey = "";
    state.dngSheetRows = [];
  } else if (!logsheetFileByKey(state.activeLogsheetFileKey)) {
    state.activeLogsheetFileKey = logsheetFileKey(files[0].name);
    state.dngSheetRows = loadDngDraftRows(state.activeLogsheetFileKey);
  }

  const activeFile = activeDngLogsheetFile();
  const activeIndex = activeFile ? files.findIndex((file) => logsheetFileKey(file.name) === state.activeLogsheetFileKey) : -1;
  const currentLabel = activeIndex >= 0 ? `${activeIndex + 1} / ${files.length}` : "0 / 0";
  if (els.dngSheetStatus) els.dngSheetStatus.textContent = currentLabel;
  if (els.dngPrevSheet) els.dngPrevSheet.disabled = state.dngSheetBusy || activeIndex <= 0;
  if (els.dngNextSheet) els.dngNextSheet.disabled = state.dngSheetBusy || activeIndex < 0 || activeIndex >= files.length - 1;
  if (els.dngOcrCurrent) els.dngOcrCurrent.disabled = state.dngSheetBusy || !activeFile;
  if (els.dngSaveSheet) els.dngSaveSheet.disabled = state.dngSheetBusy || !activeFile;
  if (els.dngAddRow) els.dngAddRow.disabled = state.dngSheetBusy || !activeFile;

  renderDngSheetFileList(files);
  renderDngSheetPreview(activeFile);
  renderDngSheetRows();
}

function renderDngSheetFileList(files) {
  if (!els.dngSheetFileList) return;
  if (!files.length) {
    els.dngSheetFileList.innerHTML = '<div class="logsheet-empty">上傳 D&G 工作紀錄後會逐張列在這裡。</div>';
    return;
  }
  els.dngSheetFileList.innerHTML = files.map((file, index) => {
    const key = logsheetFileKey(file.name);
    const active = key === state.activeLogsheetFileKey;
    const rowCount = Number(file.ocrRows || ocrRowsForFileKey(key).length || 0);
    const status = dngSheetStatusLabel(file, rowCount);
    return `
      <button type="button" class="dng-sheet-file${active ? " is-active" : ""}${file.reviewSaved ? " is-saved" : ""}" data-dng-sheet-key="${escapeAttr(key)}">
        <span class="dng-sheet-file-index">${index + 1}</span>
        <span class="dng-sheet-file-main">
          <strong>${escapeHtml(file.name)}</strong>
          <small>${escapeHtml(status)} · ${rowCount} rows</small>
        </span>
      </button>
    `;
  }).join("");
}

function renderDngSheetPreview(file) {
  if (els.dngSheetPreviewTitle) els.dngSheetPreviewTitle.textContent = file?.name || "未選擇";
  if (els.dngSheetPreviewMeta) {
    const meta = file ? `${dngSheetStatusLabel(file, Number(file.ocrRows || 0))} · ${file.previewUrl ? "圖片預覽" : "沒有圖片預覽"}` : "上傳後選擇一張";
    els.dngSheetPreviewMeta.textContent = meta;
  }
  if (!els.dngSheetPreviewImage || !els.dngSheetPreviewEmpty) return;
  if (file?.previewUrl) {
    els.dngSheetPreviewImage.src = file.previewUrl;
    els.dngSheetPreviewImage.hidden = false;
    els.dngSheetPreviewEmpty.hidden = true;
  } else {
    els.dngSheetPreviewImage.removeAttribute("src");
    els.dngSheetPreviewImage.hidden = true;
    els.dngSheetPreviewEmpty.hidden = false;
    els.dngSheetPreviewEmpty.textContent = file ? "這個檔案沒有可直接預覽的圖片，仍可 OCR 或 Save rows。" : "選擇一張圖片後會在這裡預覽。";
  }
}

function renderDngSheetRows() {
  if (!els.dngSheetRows) return;
  const rows = state.dngSheetRows || [];
  if (els.dngSheetRowsSummary) {
    const activeFile = activeDngLogsheetFile();
    const savedText = activeFile?.reviewSaved ? " · saved" : "";
    els.dngSheetRowsSummary.textContent = `${rows.length} rows${savedText}`;
  }
  if (!activeDngLogsheetFile()) {
    els.dngSheetRows.innerHTML = '<tr><td colspan="5" class="muted">請先上傳並選擇一張 D&G 工作紀錄。</td></tr>';
    return;
  }
  if (!rows.length) {
    els.dngSheetRows.innerHTML = '<tr><td colspan="5" class="muted">先按 OCR 目前這張，或按新增列手動輸入。</td></tr>';
    return;
  }
  els.dngSheetRows.innerHTML = rows.map((row, index) => `
    <tr data-dng-row="${index}">
      <td><input value="${escapeAttr(row.date || "")}" data-dng-row="${index}" data-dng-field="date" placeholder="2026-04-01"></td>
      <td><input value="${escapeAttr(row.name || "")}" data-dng-row="${index}" data-dng-field="name" placeholder="Staff name"></td>
      <td><input value="${escapeAttr(row.in || "")}" data-dng-row="${index}" data-dng-field="in" placeholder="09:00"></td>
      <td><input value="${escapeAttr(row.out || "")}" data-dng-row="${index}" data-dng-field="out" placeholder="21:30"></td>
      <td><button type="button" class="ghost danger" data-dng-delete-row="${index}" aria-label="刪除第 ${index + 1} 列">刪除</button></td>
    </tr>
  `).join("");
}

function dngSheetStatusLabel(file, rowCount = 0) {
  if (!file) return "未選擇";
  if (file.reviewSaved) return "Saved";
  if (file.ocrError) return "Failed";
  if (file.ocrStatus === "OCR") return "OCR";
  if (file.ocrStatus === "Ready") return "Ready";
  if (file.ocrStatus === "No data") return "No data";
  if (rowCount) return "Ready";
  return file.ocrStatus || "Uploaded";
}

function handleDngSheetFileClick(event) {
  const button = event.target.closest("[data-dng-sheet-key]");
  if (!button) return;
  selectDngLogsheetFile(button.dataset.dngSheetKey || "");
}

function shiftDngSheet(direction) {
  const files = state.logsheetFiles || [];
  const currentIndex = files.findIndex((file) => logsheetFileKey(file.name) === state.activeLogsheetFileKey);
  const next = files[currentIndex + direction];
  if (next) selectDngLogsheetFile(logsheetFileKey(next.name));
}

function selectDngLogsheetFile(fileKey) {
  if (!logsheetFileByKey(fileKey)) return;
  storeActiveDngDraftRows();
  state.activeLogsheetFileKey = fileKey;
  state.dngSheetRows = loadDngDraftRows(fileKey);
  renderDngSheetReview();
}

function activeDngLogsheetFile() {
  return logsheetFileByKey(state.activeLogsheetFileKey);
}

function loadDngDraftRows(fileKey) {
  if (!fileKey) return [];
  const draftRows = state.dngDraftRowsByFileKey[fileKey];
  if (Array.isArray(draftRows)) return draftRows.map((row) => ({ ...row }));
  return ocrRowsForFileKey(fileKey).map((row) => dngEditableRowFromOcrRow(row));
}

function storeActiveDngDraftRows() {
  if (!isDAndGProfile() || !state.activeLogsheetFileKey) return;
  state.dngDraftRowsByFileKey[state.activeLogsheetFileKey] = dngSheetRowsFromDom();
}

function dngSheetRowsFromDom() {
  if (!els.dngSheetRows) return state.dngSheetRows || [];
  const tableRows = [...els.dngSheetRows.querySelectorAll("tr[data-dng-row]")];
  if (!tableRows.length) return state.dngSheetRows || [];
  return tableRows.map((tableRow) => {
    const row = {};
    ["date", "name", "in", "out"].forEach((field) => {
      row[field] = tableRow.querySelector(`[data-dng-field="${field}"]`)?.value.trim() || "";
    });
    return dngEditableRowFromOcrRow(row);
  });
}

function handleDngSheetRowsInput(event) {
  const input = event.target.closest("[data-dng-field]");
  if (!input) return;
  const rowIndex = Number(input.dataset.dngRow);
  const field = input.dataset.dngField;
  if (!state.dngSheetRows[rowIndex] || !field) return;
  state.dngSheetRows[rowIndex][field] = input.value;
  state.dngDraftRowsByFileKey[state.activeLogsheetFileKey] = state.dngSheetRows.map((row) => ({ ...row }));
}

function handleDngSheetRowsChange(event) {
  const input = event.target.closest("[data-dng-field]");
  if (!input) return;
  if (input.dataset.dngField === "in" || input.dataset.dngField === "out") {
    const normalized = normalizeManualActualTime(input.value);
    if (normalized !== null) input.value = normalized;
  }
  state.dngSheetRows = dngSheetRowsFromDom();
  state.dngDraftRowsByFileKey[state.activeLogsheetFileKey] = state.dngSheetRows.map((row) => ({ ...row }));
}

function handleDngSheetRowsClick(event) {
  const button = event.target.closest("[data-dng-delete-row]");
  if (!button) return;
  const index = Number(button.dataset.dngDeleteRow);
  if (!Number.isInteger(index)) return;
  state.dngSheetRows = dngSheetRowsFromDom().filter((_, rowIndex) => rowIndex !== index);
  state.dngDraftRowsByFileKey[state.activeLogsheetFileKey] = state.dngSheetRows.map((row) => ({ ...row }));
  renderDngSheetRows();
}

function addDngSheetRow() {
  const file = activeDngLogsheetFile();
  if (!file) {
    setStatus("請先選擇一張 D&G 工作紀錄。", true);
    return;
  }
  state.dngSheetRows = dngSheetRowsFromDom();
  state.dngSheetRows.push(createDngBlankSheetRow(file.name));
  state.dngDraftRowsByFileKey[state.activeLogsheetFileKey] = state.dngSheetRows.map((row) => ({ ...row }));
  renderDngSheetRows();
}

async function ocrCurrentDngSheet() {
  if (!state.schedule || !state.scheduleConfirmed) {
    setStatus("請先讀取並確認排班表，再 OCR 工作紀錄。", true);
    setWorkflowStep(state.schedule ? "check-schedule" : "schedule-upload");
    return;
  }
  const fileRecord = activeDngLogsheetFile();
  if (!fileRecord) {
    setStatus(currentProjectProfile().noFileMessage, true);
    return;
  }
  const file = logsheetInputFileByKey(state.activeLogsheetFileKey);
  if (!file) {
    setStatus("找不到目前這張工作紀錄的原始檔，請重新選擇檔案。", true);
    return;
  }

  ensureDngOcrAggregate();
  const extraPrompt = els.ocrPrompt.value.trim();
  state.dngSheetBusy = true;
  setDngFileState(state.activeLogsheetFileKey, { ocrStatus: "OCR", ocrError: "", reviewSaved: false });
  showOcrProgress(1);
  setOcrProgress(0, 1, `OCR ${file.name}`);
  markOcrProgressItem(file.name, "running", "目前這張");
  renderDngSheetReview();
  setStatus(`OCR 目前這張：${file.name}`);
  try {
    const result = await ocrSingleFile(file, extraPrompt);
    const rows = rowsFromOcrResult(result).map((row) => dngEditableRowFromOcrRow({
      ...row,
      source_filename: row.source_filename || file.name,
      source_filenames: row.source_filenames || [file.name],
    }));
    const status = rows.length ? "Ready" : "No data";
    setDngFileState(state.activeLogsheetFileKey, {
      ocrStatus: status,
      ocrRows: rows.length,
      ocrResult: result,
      ocrError: "",
      reviewSaved: false,
    });
    state.dngSheetRows = rows;
    state.dngDraftRowsByFileKey[state.activeLogsheetFileKey] = rows.map((row) => ({ ...row }));
    setOcrProgress(1, 1, `完成 ${file.name}`);
    markOcrProgressItem(file.name, rows.length ? "done" : "no-data", rows.length ? `${rows.length} rows，請檢查後 Save` : "沒有 rows，可手動新增後 Save");
    renderDngSheetReview();
    setStatus(`${file.name} 已 OCR：${rows.length} rows。請檢查後按 Save。`, rows.length === 0);
  } catch (error) {
    const message = error.message || String(error);
    setDngFileState(state.activeLogsheetFileKey, { ocrStatus: "Failed", ocrError: message, reviewSaved: false });
    addOcrError(file.name, message);
    markOcrProgressItem(file.name, "error", message);
    setOcrProgress(1, 1, `失敗 ${file.name}`);
    setStatus(`${file.name} OCR 失敗：${message}`, true);
  } finally {
    state.dngSheetBusy = false;
    renderDngSheetReview();
    renderLogsheetAssignments();
  }
}

async function saveDngCurrentSheet() {
  const file = activeDngLogsheetFile();
  if (!file) {
    setStatus("請先選擇一張 D&G 工作紀錄。", true);
    return;
  }
  ensureDngOcrAggregate();
  const fileKey = state.activeLogsheetFileKey;
  const rows = dngSheetRowsFromDom();
  let normalizedRows = [];
  try {
    normalizedRows = normalizeDngSheetRowsForSave(rows, file.name);
  } catch (error) {
    setStatus(error.message || String(error), true);
    return;
  }

  replaceDngOcrRowsForFile(fileKey, normalizedRows, file.ocrResult || null);
  setDngFileState(fileKey, {
    ocrStatus: "Saved",
    ocrRows: normalizedRows.length,
    reviewSaved: true,
    ocrError: "",
  });
  state.dngDraftRowsByFileKey[fileKey] = normalizedRows.map((row) => dngEditableRowFromOcrRow(row));
  syncDngAggregateCounts();
  renderOcrResult();
  if (ocrRows().length) {
    await refreshRosterComparison({ userAction: true });
  } else {
    clearComparison(currentProjectProfile().waitingActualMessage);
  }

  const nextFile = nextDngFileToReview(fileKey);
  if (nextFile) {
    selectDngLogsheetFile(logsheetFileKey(nextFile.name));
    setStatus(`已 Save ${file.name}，請處理下一張：${nextFile.name}`);
  } else {
    renderDngSheetReview();
    if (ocrRows().length) setWorkflowStep("manage-schedule");
    setStatus(`已 Save ${file.name}。D&G 工作紀錄已逐張處理完成。`);
  }
}

function createDngBlankSheetRow(filename) {
  return dngEditableRowFromOcrRow({
    name: "",
    date: "",
    in: "",
    out: "",
    source_filename: filename,
    source_filenames: [filename],
  });
}

function dngEditableRowFromOcrRow(row) {
  return {
    date: display(row?.date).trim(),
    name: display(row?.name).trim(),
    in: display(row?.in).trim(),
    out: display(row?.out).trim(),
  };
}

function normalizeDngSheetRowsForSave(rows, filename) {
  return (rows || [])
    .map((row, index) => {
      const name = display(row.name).trim();
      const date = alignOcrDateToSchedule(display(row.date).trim());
      const inputIn = display(row.in).trim();
      const inputOut = display(row.out).trim();
      const inTime = inputIn ? normalizeManualActualTime(inputIn) : "";
      const outTime = inputOut ? normalizeManualActualTime(inputOut) : "";
      if (inTime === null) throw new Error(`第 ${index + 1} 列 In 時間格式不正確，可輸入 09:30 或 0930。`);
      if (outTime === null) throw new Error(`第 ${index + 1} 列 Out 時間格式不正確，可輸入 21:30 或 2130。`);
      if (!name && !date && !inTime && !outTime) return null;
      return {
        name: name || null,
        date: date || null,
        in: inTime || null,
        out: outTime || null,
        source_filename: filename,
        source_filenames: [filename],
        all_times: [inTime, outTime].filter(Boolean).sort(compareTimes),
        warnings: ["D&G 逐張覆核"],
      };
    })
    .filter(Boolean);
}

function replaceDngOcrRowsForFile(fileKey, rows, result) {
  if (!state.ocr) return;
  ensureOcrAggregateShape();
  const remainingRows = ocrRows().filter((row) => !ocrRowFileKeys(row).has(fileKey));
  state.ocr.daily_rows = mergeOcrDailyRows([...remainingRows, ...rows]);
  state.ocr.results = (state.ocr.results || []).filter((item) => !ocrResultMatchesFileKey(item, fileKey));
  if (result) {
    const manualResult = {
      ...result,
      daily_rows: rows,
      structured: {
        ...(result.structured || {}),
        daily_rows: rows,
      },
    };
    state.ocr.results.push(manualResult);
    state.ocr.configured_model = state.ocr.configured_model || result.configured_model || "";
    state.ocr.response_model = state.ocr.response_model || result.response_model || "";
    state.ocr.finish_reason = state.ocr.finish_reason || result.finish_reason || "";
  }
  state.ocr.structured.results = state.ocr.results.map((item) => item.structured || null);
  state.ocr.structured.daily_rows = state.ocr.daily_rows;
  state.ocr.errors = (state.ocr.errors || []).filter((item) => logsheetFileKey(item.source_filename) !== fileKey);
  state.ocr.no_data_files = (state.ocr.no_data_files || []).filter((filename) => logsheetFileKey(filename) !== fileKey);
  if (!rows.length) {
    const filename = logsheetFileByKey(fileKey)?.name || fileKey;
    state.ocr.no_data_files.push(filename);
  }
  applyLogsheetStaffAssignmentsToRows();
  state.ocr.usage = combineUsage(state.ocr.results);
}

function ocrResultMatchesFileKey(result, fileKey) {
  return [result?.source_filename, ...sourceFilenameArray(result?.source_filenames)]
    .some((filename) => logsheetFileKey(filename) === fileKey);
}

function nextDngFileToReview(currentFileKey) {
  const files = state.logsheetFiles || [];
  const currentIndex = files.findIndex((file) => logsheetFileKey(file.name) === currentFileKey);
  const after = files.slice(Math.max(currentIndex + 1, 0)).find((file) => !file.reviewSaved);
  if (after) return after;
  return files.find((file) => !file.reviewSaved) || null;
}

function ensureDngOcrAggregate() {
  const files = Array.from(els.logsheetFile?.files || []);
  if (!state.ocr) {
    state.ocr = createOcrAggregate(files.length ? files : state.logsheetFiles);
  }
  syncDngOcrAggregateForFiles(files.length ? files : state.logsheetFiles);
}

function syncDngOcrAggregateForFiles(files) {
  if (!isDAndGProfile()) return;
  const sourceFiles = Array.from(files || []);
  const sourceFilenames = sourceFiles.map((file) => file.name).filter(Boolean);
  const sourceKeys = new Set(sourceFilenames.map(logsheetFileKey));
  Object.keys(state.dngDraftRowsByFileKey || {}).forEach((key) => {
    if (!sourceKeys.has(key)) delete state.dngDraftRowsByFileKey[key];
  });
  if (!state.ocr) {
    state.ocr = createOcrAggregate(sourceFiles);
  }
  ensureOcrAggregateShape();
  state.ocr.source_count = sourceFilenames.length;
  state.ocr.source_filename = sourceFilenames.join(", ");
  state.ocr.source_filenames = sourceFilenames;
  state.ocr.daily_rows = ocrRows().filter((row) => [...ocrRowFileKeys(row)].some((key) => sourceKeys.has(key)));
  state.ocr.results = (state.ocr.results || []).filter((result) => ocrResultMatchesAnyFileKey(result, sourceKeys));
  state.ocr.errors = (state.ocr.errors || []).filter((item) => sourceKeys.has(logsheetFileKey(item.source_filename)));
  state.ocr.no_data_files = (state.ocr.no_data_files || []).filter((filename) => sourceKeys.has(logsheetFileKey(filename)));
  state.ocr.structured.results = state.ocr.results.map((result) => result.structured || null);
  state.ocr.structured.daily_rows = state.ocr.daily_rows;
  syncDngAggregateCounts();
}

function ocrResultMatchesAnyFileKey(result, fileKeys) {
  return [result?.source_filename, ...sourceFilenameArray(result?.source_filenames)]
    .some((filename) => fileKeys.has(logsheetFileKey(filename)));
}

function sourceFilenameArray(value) {
  if (Array.isArray(value)) return value;
  return value ? [value] : [];
}

function syncDngAggregateCounts() {
  if (!state.ocr) return;
  ensureOcrAggregateShape();
  state.ocr.processed_count = (state.logsheetFiles || []).filter((file) => file.reviewSaved || file.ocrError).length;
  state.ocr.usage = combineUsage(state.ocr.results || []);
}

function ensureOcrAggregateShape() {
  if (!state.ocr) return;
  if (!Array.isArray(state.ocr.daily_rows)) state.ocr.daily_rows = [];
  if (!Array.isArray(state.ocr.results)) state.ocr.results = [];
  if (!Array.isArray(state.ocr.errors)) state.ocr.errors = [];
  if (!Array.isArray(state.ocr.no_data_files)) state.ocr.no_data_files = [];
  if (!state.ocr.structured || typeof state.ocr.structured !== "object") {
    state.ocr.structured = { document_type: "logsheet", daily_rows: [], results: [] };
  }
  if (!Array.isArray(state.ocr.structured.daily_rows)) state.ocr.structured.daily_rows = state.ocr.daily_rows;
  if (!Array.isArray(state.ocr.structured.results)) state.ocr.structured.results = [];
}

function setDngFileState(fileKey, patch) {
  const file = logsheetFileByKey(fileKey);
  if (!file) return;
  Object.assign(file, patch);
}

function logsheetInputFileByKey(fileKey) {
  return Array.from(els.logsheetFile?.files || [])
    .find((file) => logsheetFileKey(file.name) === fileKey) || null;
}

function staffAssignmentOptions() {
  return [...new Set((state.schedule?.staff || [])
    .map((staff) => String(staff.name || "").trim())
    .filter(Boolean))]
    .sort((left, right) => left.localeCompare(right));
}

function ocrRowsForFileKey(fileKey) {
  if (!fileKey) return [];
  return ocrRows().filter((row) => ocrRowFileKeys(row).has(fileKey));
}

function ocrRowFileKeys(row) {
  const keys = new Set();
  [row?.source_filename, ...(row?.source_filenames || [])].forEach((filename) => {
    const key = logsheetFileKey(filename);
    if (key) keys.add(key);
  });
  return keys;
}

function sourceFilenamesForRow(row) {
  if (!row) return [];
  return [...new Set([row.source_filename, ...(row.source_filenames || [])]
    .map((filename) => String(filename || "").trim())
    .filter(Boolean))];
}

function sourceLinksHtml(filenames, staffName = "") {
  const unique = [...new Set((filenames || []).map((filename) => String(filename || "").trim()).filter(Boolean))];
  if (!unique.length) return "";
  return `<span class="source-file-links">${unique.map((filename) => {
    const key = logsheetFileKey(filename);
    const file = logsheetFileByKey(key);
    if (file?.previewUrl) {
      return `<button type="button" class="source-file-link" data-logsheet-preview-key="${escapeAttr(key)}" data-staff="${escapeAttr(staffName)}" title="預覽 ${escapeAttr(filename)}">${escapeHtml(filename)}</button>`;
    }
    return `<span class="source-file-text" title="沒有可直接預覽的圖片">${escapeHtml(filename)}</span>`;
  }).join("")}</span>`;
}

function logsheetFileStatus(filename, rowCount) {
  const file = logsheetFileByKey(logsheetFileKey(filename));
  if (isDAndGProfile() && file) {
    return dngSheetStatusLabel(file, rowCount);
  }
  const errors = state.ocr?.errors || [];
  const noDataFiles = state.ocr?.no_data_files || [];
  if (errors.some((item) => logsheetFileKey(item.source_filename) === logsheetFileKey(filename))) return "Failed";
  if (noDataFiles.some((item) => logsheetFileKey(item) === logsheetFileKey(filename))) return "No data";
  if (rowCount) return "OCR rows";
  if (state.ocr) return "Waiting";
  return "Uploaded";
}

async function handleLogsheetAssignmentChange(event) {
  const select = event.target.closest("select[data-logsheet-file-key]");
  if (!select) return;
  const fileKey = select.dataset.logsheetFileKey || "";
  const file = (state.logsheetFiles || []).find((item) => logsheetFileKey(item.name) === fileKey);
  if (!file) return;
  file.assignedStaff = select.value || "";
  applyLogsheetStaffAssignmentsToRows();
  renderOcrResult();
  renderLogsheetAssignments();
  if (state.schedule && ocrRows().length) {
    await refreshRosterComparison({ userAction: true });
  }
  setStatus(file.assignedStaff ? `${file.name} 已指派到 ${file.assignedStaff}。` : `${file.name} 已改回自動配對。`);
}

function handleLogsheetPreviewClick(event) {
  const button = event.target.closest("[data-logsheet-preview-key]");
  if (!button) return;
  event.preventDefault();
  event.stopPropagation();
  openLogsheetFilePreview(button.dataset.logsheetPreviewKey || "", button.dataset.staff || "");
}

function applyLogsheetStaffAssignmentsToRows() {
  if (!state.ocr) return;
  const rows = ocrRows();
  if (!rows.length) return;
  const assignments = new Map((state.logsheetFiles || [])
    .filter((file) => file.assignedStaff)
    .map((file) => [logsheetFileKey(file.name), file.assignedStaff]));
  rows.forEach((row) => {
    if (!Object.hasOwn(row, "original_name")) row.original_name = row.name || "";
    const assignedStaff = assignedStaffForOcrRow(row, assignments);
    if (assignedStaff) {
      row.name = assignedStaff;
      row.assigned_staff_name = assignedStaff;
    } else if (row.assigned_staff_name) {
      row.name = row.original_name || row.name;
      delete row.assigned_staff_name;
    }
  });
  replaceOcrRows(rows);
}

function assignedStaffForOcrRow(row, assignments) {
  for (const key of ocrRowFileKeys(row)) {
    if (assignments.has(key)) return assignments.get(key);
  }
  return "";
}

function revokeLogsheetFileUrls() {
  (state.logsheetFiles || []).forEach((file) => {
    if (file.previewUrl) URL.revokeObjectURL(file.previewUrl);
  });
}

function clearPage() {
  revokeLogsheetFileUrls();
  state.response = null;
  state.schedule = null;
  state.originalSchedule = null;
  state.scheduleVariants = [];
  state.selectedScheduleVariantKey = "";
  state.entries = [];
  state.ocr = null;
  state.comparison = null;
  state.lateGraceMinutes = DEFAULT_LATE_GRACE_MINUTES;
  state.earlyLeaveGraceMinutes = DEFAULT_EARLY_LEAVE_GRACE_MINUTES;
  state.countEarlyIn = false;
  state.earlyInGraceMinutes = DEFAULT_EARLY_IN_GRACE_MINUTES;
  state.countOvertime = false;
  state.overtimeGraceMinutes = DEFAULT_OVERTIME_GRACE_MINUTES;
  state.currentStep = "project-select";
  state.scheduleConfirmed = false;
  state.selectedRosterStaff = "";
  state.logsheetFiles = [];
  state.activeLogsheetFileKey = "";
  state.dngSheetRows = [];
  state.dngDraftRowsByFileKey = {};
  state.dngSheetBusy = false;
  state.rosterIssuesExpanded = false;
  state.exportTableDataset = DEFAULT_EXPORT_TABLE_DATASET;
  state.exportTableUserSelected = false;
  resetExportTableSelection();
  els.file.value = "";
  els.logsheetFile.value = "";
  els.ocrPrompt.value = "";
  if (els.ocrEnhanceImage) els.ocrEnhanceImage.checked = true;
  if (els.rosterConfidence) els.rosterConfidence.checked = true;
  if (els.rosterShowZero) els.rosterShowZero.checked = true;
  syncGraceInputs();
  clearOcrResult();
  clearComparison("尚未解析排班表和 OCR。");
  els.search.value = "";
  els.staffFilter.innerHTML = '<option value="">全部員工</option>';
  els.unresolvedOnly.checked = false;
  els.warningsOnly.checked = false;
  state.holidayCountSunday = false;
  state.holidayUseOfficial = true;
  state.officialHolidayYear = DEFAULT_GOVHK_HOLIDAY_YEAR;
  state.customHolidays = [];
  state.customHolidaySource = "";
  if (els.holidaySunday) els.holidaySunday.checked = false;
  if (els.holidayOfficial) els.holidayOfficial.checked = true;
  if (els.holidayOfficialYear) els.holidayOfficialYear.value = state.officialHolidayYear;
  if (els.holidayUpload) els.holidayUpload.value = "";
  renderHolidayStatus();
  els.summary.innerHTML = "";
  els.messages.textContent = "尚未解析排班表。";
  els.messages.className = "message-list empty";
  renderScheduleVariantSelector();
  clearTable(els.dateColumns);
  clearTable(els.staff);
  clearTable(els.shiftTimes);
  clearTable(els.entries);
  els.entryCount.textContent = "0 筆";
  els.diagnostics.textContent = "";
  els.rawJson.textContent = "";
  clearExportTable();
  clearRosterSummary();
  updateWorkflowState();
  setStatus("就緒");
}

function handleHolidayOptionsChange() {
  state.holidayCountSunday = Boolean(els.holidaySunday?.checked);
  state.holidayUseOfficial = Boolean(els.holidayOfficial?.checked);
  state.officialHolidayYear = selectedOfficialHolidayYearFromInput();
  renderHolidayStatus();
  renderEntries();
  if (state.comparison) renderRosterSummary(state.comparison.rows || []);
  renderExportTable();
}

async function handleHolidayUploadChange(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    const text = await file.text();
    const holidays = parseHolidayUpload(text, file.name);
    if (!holidays.length) {
      throw new Error("找不到可用假期日期，請上傳 iCal、JSON、CSV 或文字日期清單。");
    }
    state.customHolidays = holidays;
    state.customHolidaySource = file.name;
    renderHolidayStatus(`已載入 ${holidays.length} 個自訂假期`);
    renderEntries();
    if (state.comparison) renderRosterSummary(state.comparison.rows || []);
    renderExportTable();
    setStatus(`已載入 ${holidays.length} 個自訂假期。`);
  } catch (error) {
    renderHolidayStatus(error.message || String(error), true);
    setStatus(error.message || String(error), true);
  }
}

function renderHolidayStatus(message = "", isError = false) {
  if (!els.holidayStatus) return;
  if (els.holidaySunday) els.holidaySunday.checked = state.holidayCountSunday;
  if (els.holidayOfficial) els.holidayOfficial.checked = state.holidayUseOfficial;
  if (els.holidayOfficialYear) {
    els.holidayOfficialYear.value = currentOfficialHolidayYear();
    els.holidayOfficialYear.disabled = !state.holidayUseOfficial;
  }
  const officialYear = currentOfficialHolidayYear();
  const officialHolidays = officialHolidayRowsForYear(officialYear);
  const parts = [
    state.holidayUseOfficial
      ? `GovHK ${officialYear}：${officialHolidays.length} 日`
      : `GovHK ${officialYear}：未使用`,
    state.holidayCountSunday ? "Sunday：計入" : "Sunday：不計入",
    state.customHolidays.length
      ? `上傳：${state.customHolidaySource || "自訂檔"}，${state.customHolidays.length} 日`
      : "未上傳自訂假期",
  ];
  els.holidayStatus.textContent = [message, parts.join("；")].filter(Boolean).join("；");
  els.holidayStatus.classList.toggle("is-error", Boolean(isError));
}

function currentOfficialHolidayYear() {
  const value = String(state.officialHolidayYear || DEFAULT_GOVHK_HOLIDAY_YEAR);
  return GOVHK_GENERAL_HOLIDAY_YEARS.includes(value) ? value : DEFAULT_GOVHK_HOLIDAY_YEAR;
}

function selectedOfficialHolidayYearFromInput() {
  const value = String(els.holidayOfficialYear?.value || state.officialHolidayYear || DEFAULT_GOVHK_HOLIDAY_YEAR);
  return GOVHK_GENERAL_HOLIDAY_YEARS.includes(value) ? value : DEFAULT_GOVHK_HOLIDAY_YEAR;
}

function officialHolidayRowsForYear(year = currentOfficialHolidayYear()) {
  return GOVHK_GENERAL_HOLIDAYS_BY_YEAR[String(year)] || GOVHK_GENERAL_HOLIDAYS_BY_YEAR[DEFAULT_GOVHK_HOLIDAY_YEAR] || [];
}

function inferScheduleHolidayYear() {
  const counts = new Map();
  (state.entries || []).forEach((entry) => {
    const year = String(entry?.date || "").slice(0, 4);
    if (GOVHK_GENERAL_HOLIDAY_YEARS.includes(year)) {
      counts.set(year, (counts.get(year) || 0) + 1);
    }
  });
  return [...counts.entries()].sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))[0]?.[0] || "";
}

function parseHolidayUpload(text, filename = "") {
  const trimmed = String(text || "").trim();
  if (!trimmed) return [];
  const source = filename || "uploaded holiday file";
  const rows = [];
  if (source.toLowerCase().endsWith(".json") || /^[\[{]/.test(trimmed)) {
    try {
      collectHolidayDatesFromJson(JSON.parse(trimmed), rows, source);
      return dedupeHolidayRows(rows, source);
    } catch {
      // Fall back to text scanning because some government exports wrap JSON-like text.
    }
  }
  rows.push(...extractHolidayRowsFromIcs(trimmed, source));
  rows.push(...extractHolidayRowsFromText(trimmed, source));
  return dedupeHolidayRows(rows, source);
}

function collectHolidayDatesFromJson(value, rows, source, fallbackName = "") {
  if (Array.isArray(value)) {
    value.forEach((item) => collectHolidayDatesFromJson(item, rows, source, fallbackName));
    return;
  }
  if (value && typeof value === "object") {
    const dateValue = value.date || value.holiday_date || value.start || value.dtstart || value.DTSTART;
    const nameValue = value.name || value.title || value.summary || value.SUMMARY || value.description || fallbackName;
    const date = normalizeHolidayDate(dateValue);
    if (date) rows.push({ date, name: String(nameValue || "").trim(), source });
    Object.entries(value).forEach(([key, item]) => {
      if (["date", "holiday_date", "start", "dtstart", "DTSTART"].includes(key)) return;
      collectHolidayDatesFromJson(item, rows, source, String(nameValue || fallbackName || "").trim());
    });
    return;
  }
  if (typeof value === "string") {
    datesFromText(value, shouldInferSelectedHolidayLine(value) ? currentOfficialHolidayYear() : "").forEach((date) => {
      rows.push({ date, name: fallbackName || holidayNameFromLine(value, date), source });
    });
  }
}

function extractHolidayRowsFromIcs(text, source) {
  const rows = [];
  const blocks = String(text || "").split(/BEGIN:VEVENT/i).slice(1);
  blocks.forEach((block) => {
    const dateLine = block.match(/^DTSTART[^:\n]*:(.+)$/im);
    if (!dateLine) return;
    const summaryLine = block.match(/^SUMMARY[^:\n]*:(.+)$/im);
    const date = normalizeHolidayDate(dateLine[1]);
    if (date) {
      rows.push({
        date,
        name: decodeIcsText(summaryLine?.[1] || ""),
        source,
      });
    }
  });
  return rows;
}

function extractHolidayRowsFromText(text, source) {
  const rows = [];
  String(text || "").split(/\r?\n/).forEach((line) => {
    datesFromText(line, shouldInferSelectedHolidayLine(line) ? currentOfficialHolidayYear() : "").forEach((date) => {
      rows.push({ date, name: holidayNameFromLine(line, date), source });
    });
  });
  return rows;
}

function shouldInferSelectedHolidayLine(line) {
  const text = String(line || "").toLowerCase();
  if (!text.trim()) return false;
  if (/\b(gazetted|issued|revision|today|spokesman|feedback|copyright|public information)\b/.test(text)) {
    return false;
  }
  return /\b(holiday|holidays|day|festival|christmas|lunar|ching ming|buddha|tuen ng|national|establishment)\b/.test(text);
}

function dedupeHolidayRows(rows, source) {
  const map = new Map();
  rows.forEach((row) => {
    const date = normalizeHolidayDate(row.date);
    if (!date || map.has(date)) return;
    map.set(date, {
      date,
      name: String(row.name || "").trim() || "Uploaded holiday",
      source: row.source || source,
    });
  });
  return [...map.values()].sort((left, right) => left.date.localeCompare(right.date));
}

function datesFromText(text, defaultYear = "") {
  const input = String(text || "").replace(/\u00a0/g, " ");
  const dates = [];
  const patterns = [
    /\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b/g,
    /\b(20\d{2})(\d{2})(\d{2})\b/g,
    /\b(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+(20\d{2})\b/gi,
    /\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(20\d{2})\b/gi,
  ];
  let match;
  while ((match = patterns[0].exec(input))) dates.push(formatHolidayDate(match[1], match[2], match[3]));
  while ((match = patterns[1].exec(input))) dates.push(formatHolidayDate(match[1], match[2], match[3]));
  while ((match = patterns[2].exec(input))) dates.push(formatHolidayDate(match[3], monthNumber(match[2]), match[1]));
  while ((match = patterns[3].exec(input))) dates.push(formatHolidayDate(match[3], monthNumber(match[1]), match[2]));
  if (defaultYear) {
    const dayMonth = /\b(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\b/gi;
    const monthDay = /\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?\b/gi;
    while ((match = dayMonth.exec(input))) dates.push(formatHolidayDate(defaultYear, monthNumber(match[2]), match[1]));
    while ((match = monthDay.exec(input))) dates.push(formatHolidayDate(defaultYear, monthNumber(match[1]), match[2]));
  }
  return [...new Set(dates.filter(isValidHolidayDate))];
}

function normalizeHolidayDate(value) {
  if (value === null || value === undefined) return "";
  return datesFromText(String(value), "")[0] || "";
}

function formatHolidayDate(year, month, day) {
  const yyyy = String(year || "").padStart(4, "0");
  const mm = String(month || "").padStart(2, "0");
  const dd = String(day || "").padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function monthNumber(value) {
  const month = String(value || "").slice(0, 3).toLowerCase();
  return {
    jan: 1,
    feb: 2,
    mar: 3,
    apr: 4,
    may: 5,
    jun: 6,
    jul: 7,
    aug: 8,
    sep: 9,
    oct: 10,
    nov: 11,
    dec: 12,
  }[month] || "";
}

function isValidHolidayDate(date) {
  const match = String(date || "").match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return false;
  const parsed = new Date(`${date}T00:00:00`);
  return !Number.isNaN(parsed.getTime())
    && parsed.getFullYear() === Number(match[1])
    && parsed.getMonth() + 1 === Number(match[2])
    && parsed.getDate() === Number(match[3]);
}

function isSundayDate(date) {
  if (!isValidHolidayDate(date)) return false;
  return new Date(`${date}T00:00:00`).getDay() === 0;
}

function decodeIcsText(value) {
  return String(value || "")
    .replace(/\\n/g, " ")
    .replace(/\\,/g, ",")
    .replace(/\\;/g, ";")
    .trim();
}

function holidayNameFromLine(line, date) {
  return String(line || "")
    .replace(date, "")
    .replace(date.replaceAll("-", ""), "")
    .replace(/\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b/g, "")
    .replace(/\b(20\d{2})(\d{2})(\d{2})\b/g, "")
    .replace(/\b(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)(?:\s+20\d{2})?\b/gi, "")
    .replace(/\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+20\d{2})?\b/gi, "")
    .replace(/[,|:-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim() || "Uploaded holiday";
}

function activeHolidayMap() {
  const holidays = new Map();
  if (state.holidayUseOfficial) {
    officialHolidayRowsForYear().forEach(([date, name]) => holidays.set(date, name));
  }
  state.customHolidays.forEach((holiday) => {
    if (!holiday?.date) return;
    holidays.set(holiday.date, holiday.name || "Uploaded holiday");
  });
  return holidays;
}

function holidayInfoForDate(date) {
  const key = normalizeHolidayDate(date);
  if (!key) return { isHoliday: false, label: "" };
  const labels = [];
  if (state.holidayCountSunday && isSundayDate(key)) labels.push("Sunday");
  const datedHoliday = activeHolidayMap().get(key);
  if (datedHoliday) labels.push(datedHoliday);
  return {
    isHoliday: Boolean(labels.length),
    label: labels.join(" / "),
  };
}

function renderOcrResult() {
  if (!state.ocr) {
    clearOcrResult();
    return;
  }
  const source = state.ocr.source_filename || "logsheet";
  const model = state.ocr.response_model || state.ocr.configured_model || "";
  const hasStructuredJson = Boolean(state.ocr.structured);
  const rows = ocrRows();
  els.ocrMeta.textContent = `${source}${model ? " · " + model : ""}${hasStructuredJson ? " · 已解析 JSON" : " · 原文輸出"} · ${rows.length} 筆`;
  renderOcrTable(rows);
  renderLogsheetAssignments();
  renderDngSheetReview();
  els.ocrOutput.hidden = false;
  els.ocrOutput.textContent = pretty(state.ocr);
  updateWorkflowState();
}

function clearOcrResult() {
  els.ocrMeta.textContent = "尚未 OCR";
  els.ocrOutput.textContent = "";
  els.ocrOutput.hidden = true;
  els.ocrTableSection.hidden = true;
  els.ocrRowCount.textContent = "0 筆";
  clearTable(els.ocrTableBody);
  hideOcrProgress();
  renderLogsheetAssignments();
  renderDngSheetReview();
  updateWorkflowState();
}

async function refreshRosterComparison(options = {}) {
  if (!state.schedule) {
    clearComparison("尚未解析 Excel 排班表。");
    return;
  }
  const rows = ocrRows();
  if (!rows.length) {
    clearComparison(currentProjectProfile().waitingActualMessage);
    return;
  }

  const requestId = comparisonRequestId + 1;
  comparisonRequestId = requestId;
  els.compareButton.disabled = true;
  els.compareStatus.classList.remove("error-text");
  els.compareStatus.textContent = "核對中...";
  try {
    const response = await fetch(apiUrl("/api/compare-roster"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        schedule: state.schedule,
        ocr_rows: rows,
        late_grace_minutes: currentLateGraceMinutes(),
        early_leave_grace_minutes: currentEarlyLeaveGraceMinutes(),
        count_early_in: currentCountEarlyIn(),
        early_in_grace_minutes: currentEarlyInGraceMinutes(),
        count_overtime: currentCountOvertime(),
        overtime_grace_minutes: currentOvertimeGraceMinutes(),
      }),
    });
    const payload = await readApiJson(response, "核對排班失敗：API 回傳格式不正確。");
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "核對失敗。");
    }
    if (requestId !== comparisonRequestId) return;
    state.comparison = payload.comparison;
    state.lateGraceMinutes = payload.comparison?.summary?.late_grace_minutes ?? currentLateGraceMinutes();
    state.earlyLeaveGraceMinutes = payload.comparison?.summary?.early_leave_grace_minutes ?? currentEarlyLeaveGraceMinutes();
    state.countEarlyIn = Boolean(payload.comparison?.summary?.count_early_in ?? currentCountEarlyIn());
    state.earlyInGraceMinutes = payload.comparison?.summary?.early_in_grace_minutes ?? currentEarlyInGraceMinutes();
    state.countOvertime = Boolean(payload.comparison?.summary?.count_overtime ?? currentCountOvertime());
    state.overtimeGraceMinutes = payload.comparison?.summary?.overtime_grace_minutes ?? currentOvertimeGraceMinutes();
    syncGraceInputs();
    renderComparison(payload.comparison);
    updateWorkflowState();
    if (options.userAction) setStatus(currentProjectProfile().compareDoneMessage);
  } catch (error) {
    if (requestId !== comparisonRequestId) return;
    state.comparison = null;
    const message = apiErrorMessage(error, "/api/compare-roster");
    els.compareStatus.textContent = message;
    els.compareStatus.classList.add("error-text");
    if (options.userAction) setStatus(message, true);
  } finally {
    if (requestId === comparisonRequestId) {
      els.compareButton.disabled = false;
    }
  }
}

function clearComparison(message) {
  state.comparison = null;
  comparisonRequestId += 1;
  closeRosterDetail();
  els.compareStatus.textContent = message || "尚未核對。";
  els.compareStatus.classList.remove("error-text");
  els.compareButton.disabled = !state.schedule || !ocrRows().length;
  els.compareSummary.innerHTML = "";
  els.compareRowCount.textContent = "0 筆";
  clearTable(els.compareTableBody);
  els.compareOutput.textContent = "";
  clearRosterSummary();
  renderExportTable();
  updateWorkflowState();
}

function renderComparison(comparison) {
  const summary = comparison?.summary || {};
  const rows = comparison?.rows || [];
  els.compareStatus.classList.remove("error-text");
  els.compareStatus.textContent = comparisonStatusText(summary);
  els.compareRowCount.textContent = `${rows.length} 筆`;
  renderComparisonSummary(summary);
  renderTable(els.compareTableBody, rows, (row) => [
    row.date,
    row.staff_name,
    row.ocr_name,
    formatConfidenceScore(row),
    row.shift_code || row.raw_shift_code,
    row.scheduled_in,
    row.scheduled_out,
    row.actual_in,
    row.actual_out,
    displayMinutes(row.raw_late_minutes),
    displayMinutes(row.late_minutes),
    displayMinutes(row.early_leave_minutes),
    comparisonStatusLabelForRow(row),
    formatComparisonFlags(row.flags || []),
    row.notes,
    htmlCell(sourceLinksHtml(sourceFilenamesForRow(row), row.staff_name || row.ocr_name || "")),
  ], comparisonRowClass);
  renderRosterSummary(rows);
  renderLogsheetAssignments();
  els.compareOutput.textContent = pretty(comparison);
  renderExportTable();
  updateWorkflowState();
}

function renderComparisonSummary(summary) {
  const cards = [
    ["核對筆數", summary.compared_rows],
    ["上班寬限", `${summary.late_grace_minutes ?? currentLateGraceMinutes()} 分鐘`],
    ["早退寬限", `${summary.early_leave_grace_minutes ?? currentEarlyLeaveGraceMinutes()} 分鐘`],
    ["早到計算", summary.count_early_in ? `${summary.early_in_grace_minutes ?? currentEarlyInGraceMinutes()} 分鐘` : "不計"],
    ["OT 計算", summary.count_overtime ? `${summary.overtime_grace_minutes ?? currentOvertimeGraceMinutes()} 分鐘` : "不計"],
    ["已配對", summary.matched_rows],
    [currentProjectProfile().missingLogsheetLabel, summary.missing_logsheet_rows],
    ["未排班打卡", summary.unscheduled_punch_rows],
    ["姓名未配對", summary.unmatched_name_rows],
    ["姓名需覆核", summary.name_check_rows],
    ["遲到", summary.late_rows],
    ["早退", summary.early_leave_rows],
    ["早到", summary.early_in_rows],
    ["OT", summary.overtime_rows],
  ];
  els.compareSummary.innerHTML = cards.map(([label, value]) => (
    `<div class="summary-card compact"><div class="label">${escapeHtml(label)}</div><div class="value">${escapeHtml(display(value ?? 0))}</div></div>`
  )).join("");
}

function handleGraceMinutesChange() {
  state.lateGraceMinutes = currentLateGraceMinutes();
  state.earlyLeaveGraceMinutes = currentEarlyLeaveGraceMinutes();
  state.countEarlyIn = currentCountEarlyIn();
  state.earlyInGraceMinutes = currentEarlyInGraceMinutes();
  state.countOvertime = currentCountOvertime();
  state.overtimeGraceMinutes = currentOvertimeGraceMinutes();
  syncGraceInputs();
  if (state.schedule && ocrRows().length) {
    refreshRosterComparison({ userAction: true });
  }
}

function currentLateGraceMinutes() {
  const value = Number.parseInt(els.lateGraceMinutes?.value || "", 10);
  if (!Number.isFinite(value)) return DEFAULT_LATE_GRACE_MINUTES;
  return clamp(value, 0, 14);
}

function currentEarlyLeaveGraceMinutes() {
  const value = Number.parseInt(els.earlyLeaveGraceMinutes?.value || "", 10);
  if (!Number.isFinite(value)) return DEFAULT_EARLY_LEAVE_GRACE_MINUTES;
  return clamp(value, 0, 14);
}

function currentCountEarlyIn() {
  return Boolean(els.countEarlyIn?.checked);
}

function currentEarlyInGraceMinutes() {
  const value = Number.parseInt(els.earlyInGraceMinutes?.value || "", 10);
  if (!Number.isFinite(value)) return DEFAULT_EARLY_IN_GRACE_MINUTES;
  return clamp(value, 0, 14);
}

function currentCountOvertime() {
  return Boolean(els.countOvertime?.checked);
}

function currentOvertimeGraceMinutes() {
  const value = Number.parseInt(els.overtimeGraceMinutes?.value || "", 10);
  if (!Number.isFinite(value)) return DEFAULT_OVERTIME_GRACE_MINUTES;
  return clamp(value, 0, 14);
}

function syncGraceInputs() {
  if (els.lateGraceMinutes) {
    const value = Number(state.lateGraceMinutes);
    els.lateGraceMinutes.value = String(clamp(Number.isFinite(value) ? value : DEFAULT_LATE_GRACE_MINUTES, 0, 14));
  }
  if (els.earlyLeaveGraceMinutes) {
    const value = Number(state.earlyLeaveGraceMinutes);
    els.earlyLeaveGraceMinutes.value = String(clamp(Number.isFinite(value) ? value : DEFAULT_EARLY_LEAVE_GRACE_MINUTES, 0, 14));
  }
  if (els.countEarlyIn) {
    els.countEarlyIn.checked = Boolean(state.countEarlyIn);
  }
  if (els.earlyInGraceMinutes) {
    const value = Number(state.earlyInGraceMinutes);
    els.earlyInGraceMinutes.value = String(clamp(Number.isFinite(value) ? value : DEFAULT_EARLY_IN_GRACE_MINUTES, 0, 14));
    els.earlyInGraceMinutes.disabled = !Boolean(state.countEarlyIn);
  }
  if (els.countOvertime) {
    els.countOvertime.checked = Boolean(state.countOvertime);
  }
  if (els.overtimeGraceMinutes) {
    const value = Number(state.overtimeGraceMinutes);
    els.overtimeGraceMinutes.value = String(clamp(Number.isFinite(value) ? value : DEFAULT_OVERTIME_GRACE_MINUTES, 0, 14));
    els.overtimeGraceMinutes.disabled = !Boolean(state.countOvertime);
  }
}

function renderRosterSummary(rows) {
  if (!els.rosterBody) return;
  const splitHolidayColumns = shouldSplitHolidayColumns();
  renderRosterHeader(splitHolidayColumns);
  const rosterRows = buildRosterRows(rows);
  const visibleRows = rosterRows;
  const hiddenRows = [];
  if (els.rosterSummaryText) {
    const totalDays = visibleRows.reduce((sum, row) => sum + row.days, 0);
    const totalHours = visibleRows.reduce((sum, row) => sum + row.hours, 0);
    const totalActualHours = visibleRows.reduce((sum, row) => sum + row.actualHours, 0);
    const totalIssues = visibleRows.reduce((sum, row) => sum + row.issues, 0);
    els.rosterSummaryText.innerHTML = rosterSummaryHtml({
      visibleRows,
      rosterRows,
      hiddenRows,
      totalDays,
      totalHours,
      totalActualHours,
      totalIssues,
    });
  }
  if (!visibleRows.length) {
    els.rosterBody.innerHTML = `<tr><td class="muted" colspan="${rosterColumnCount(splitHolidayColumns)}">沒有可顯示的員工排班。</td></tr>`;
    return;
  }
  els.rosterBody.innerHTML = visibleRows.map((row) => rosterRowHtml(row, splitHolidayColumns)).join("");
  if (state.selectedRosterStaff && !visibleRows.some((row) => row.staff === state.selectedRosterStaff)) {
    state.selectedRosterStaff = visibleRows[0]?.staff || "";
  }
  if (els.rosterDetailModal && !els.rosterDetailModal.hidden && state.selectedRosterStaff) {
    renderRosterDetail(state.selectedRosterStaff);
  }
}

function handleRosterSummaryClick(event) {
  const button = event.target.closest("[data-roster-summary-action]");
  if (!button) return;
  state.rosterIssuesExpanded = button.dataset.rosterSummaryAction === "expand";
  renderRosterSummary(state.comparison?.rows || []);
}

function rosterSummaryHtml({ visibleRows, rosterRows, hiddenRows, totalDays, totalHours, totalActualHours, totalIssues }) {
  const lines = [
    `<span class="roster-summary-line">${escapeHtml(`${visibleRows.length}/${rosterRows.length} 位員工，${totalDays} 天，預定 ${formatRosterHours(totalHours)} 小時，實際 ${formatRosterHours(totalActualHours)} 小時，${totalIssues} 個需要覆核項目。`)}</span>`,
  ];
  const hiddenText = hiddenRosterRowsText(hiddenRows);
  if (hiddenText) {
    lines.push(`<span class="roster-summary-missing">${escapeHtml(hiddenText)}</span>`);
  }
  const issueHtml = rosterIssueRowsHtml(visibleRows);
  if (issueHtml) {
    lines.push(issueHtml);
  }
  return lines.join("");
}

function hiddenRosterRowsText(hiddenRows) {
  if (!hiddenRows.length) return "";
  const staffDetails = hiddenRows.map((row) => `${row.staff}：${hiddenRosterReason(row)}`);
  return `未顯示 ${hiddenRows.length} 位員工：${staffDetails.join("；")}。`;
}

function hiddenRosterReason(row) {
  if (!row.days && !row.logs.length) return "名冊有此員工，但目前沒有排班或打卡資料";
  if (!row.hours && !row.actualHours) return "排班與打卡合計都是 0 小時，已被 0 小時篩選隱藏";
  return "不符合目前顯示條件";
}

function rosterIssueRowsHtml(rows) {
  const issueRows = rows.filter((row) => row.issues > 0);
  if (!issueRows.length) return "";
  const visibleIssueRows = state.rosterIssuesExpanded ? issueRows : issueRows.slice(0, 3);
  const items = visibleIssueRows.map((row) => (
    `<li class="roster-summary-issue-item">` +
    `<strong>${escapeHtml(row.staff)}</strong>` +
    `<span>${escapeHtml(rosterIssueReasonText(row))}</span>` +
    `</li>`
  )).join("");
  const hiddenCount = issueRows.length - visibleIssueRows.length;
  const action = issueRows.length > 3
    ? `<button type="button" class="roster-summary-more" data-roster-summary-action="${state.rosterIssuesExpanded ? "collapse" : "expand"}">${state.rosterIssuesExpanded ? "less" : `more (${hiddenCount})`}</button>`
    : "";
  return (
    `<div class="roster-summary-issues">` +
    `<div class="roster-summary-issues-title">需覆核員工</div>` +
    `<ul class="roster-summary-issue-list">${items}</ul>` +
    action +
    `</div>`
  );
}

function rosterIssueReasonText(row) {
  const buckets = new Map();
  row.logs.forEach((log) => {
    rosterLogIssueReasons(log).forEach((reason) => {
      if (!buckets.has(reason)) buckets.set(reason, []);
      buckets.get(reason).push(log.day || "-");
    });
  });
  return [...buckets.entries()].map(([reason, days]) => {
    const uniqueDays = [...new Set(days)];
    return `${reason} ${uniqueDays.length} 天（${uniqueDays.join("、")}）`;
  }).join("、") || "需要覆核";
}

function rosterLogIssueReasons(log) {
  const reasons = [...(log.issueReasons || [])];
  if (log.status === "missing") reasons.push("缺打卡資料");
  if (log.status === "late") reasons.push("遲到");
  if (log.status === "early") reasons.push("早退");
  if (log.status === "unscheduled") reasons.push("未排班打卡");
  if (log.confidenceLow) reasons.push("姓名信心需覆核");
  return [...new Set(reasons)];
}

function ensureScheduleSummaryOverrides() {
  if (!state.schedule) return {};
  if (!state.schedule.staff_summary_overrides || typeof state.schedule.staff_summary_overrides !== "object") {
    state.schedule.staff_summary_overrides = {};
  }
  return state.schedule.staff_summary_overrides;
}

function scheduleSummaryOverrideForStaff(staffName) {
  const overrides = state.schedule?.staff_summary_overrides;
  const rowOverride = overrides?.[staffName];
  return rowOverride && typeof rowOverride === "object" ? rowOverride : {};
}

function scheduleSummaryFieldValue(row, field) {
  const override = scheduleSummaryOverrideForStaff(row.staff);
  if (Object.hasOwn(override, field)) return override[field];
  return row[field];
}

function applyScheduleSummaryOverrides(row) {
  const normalDays = scheduleSummaryFieldValue(row, "normalDays");
  const normalHours = scheduleSummaryFieldValue(row, "normalHours");
  const publicHolidayDays = scheduleSummaryFieldValue(row, "publicHolidayDays");
  const publicHolidayHours = scheduleSummaryFieldValue(row, "publicHolidayHours");
  const override = scheduleSummaryOverrideForStaff(row.staff);
  const monthFields = Object.keys(row).filter(isScheduleSummaryMonthField);
  const monthValues = {};
  monthFields.forEach((field) => {
    monthValues[field] = scheduleSummaryFieldValue(row, field);
  });
  const hasSplitDays = Object.hasOwn(override, "normalDays") || Object.hasOwn(override, "publicHolidayDays");
  const hasSplitHours = Object.hasOwn(override, "normalHours") || Object.hasOwn(override, "publicHolidayHours");
  const monthDayFields = monthFields.filter((field) => scheduleSummaryMonthMetric(field) === "days");
  const monthHourFields = monthFields.filter((field) => scheduleSummaryMonthMetric(field) === "hours");
  const hasMonthDays = monthDayFields.some((field) => Object.hasOwn(override, field));
  const hasMonthHours = monthHourFields.some((field) => Object.hasOwn(override, field));
  const days = hasSplitDays
    ? Number(normalDays || 0) + Number(publicHolidayDays || 0)
    : hasMonthDays
      ? monthDayFields.reduce((total, field) => total + Number(monthValues[field] || 0), 0)
      : scheduleSummaryFieldValue(row, "days");
  const hours = hasSplitHours
    ? roundHours(Number(normalHours || 0) + Number(publicHolidayHours || 0))
    : hasMonthHours
      ? roundHours(monthHourFields.reduce((total, field) => total + Number(monthValues[field] || 0), 0))
      : scheduleSummaryFieldValue(row, "hours");

  return {
    ...row,
    ...monthValues,
    days,
    hours,
    normalDays,
    normalHours,
    publicHolidayDays,
    publicHolidayHours,
  };
}

function buildRosterRows(compareRows = []) {
  const schedule = state.schedule || {};
  const groups = new Map();
  const compareByScheduleKey = new Map();
  const unscheduledRows = [];

  compareRows.forEach((row) => {
    if (row.has_schedule) {
      compareByScheduleKey.set(rosterKey(row.staff_name, row.date), row);
    } else if (row.has_actual) {
      unscheduledRows.push(row);
    }
  });

  const makeGroup = (staff, order) => ({
    staff,
    order,
    dates: new Set(),
    normalDates: new Set(),
    publicHolidayDates: new Set(),
    hours: 0,
    normalHours: 0,
    publicHolidayHours: 0,
    actualHours: 0,
    issues: 0,
    logs: [],
  });

  (schedule.staff || []).forEach((staff, index) => {
    const name = String(staff.name || "").trim();
    if (name && !groups.has(name)) groups.set(name, makeGroup(name, index));
  });

  (schedule.entries || []).forEach((entry) => {
    const staff = String(entry.staff_name || "").trim();
    if (!staff) return;
    if (!groups.has(staff)) groups.set(staff, makeGroup(staff, groups.size));
    const group = groups.get(staff);
    const date = String(entry.date || "");
    const compareRow = compareByScheduleKey.get(rosterKey(staff, date));
    const scheduledHours = scheduleEntryHours(entry);
    const actualHours = actualHoursForCompareRow(entry, compareRow);
    const logStatus = rosterLogStatus(entry, compareRow);
    const holiday = holidayInfoForDate(date);
    if (date) group.dates.add(date);
    group.hours += scheduledHours;
    if (holiday.isHoliday) {
      if (date) group.publicHolidayDates.add(date);
      group.publicHolidayHours += scheduledHours;
    } else {
      if (date) group.normalDates.add(date);
      group.normalHours += scheduledHours;
    }
    group.actualHours += actualHours;
    if (logStatus.issue) group.issues += 1;
    group.logs.push({
      date,
      day: formatScheduleDayOnly(date),
      code: entry.shift_code || entry.raw_shift_code || "-",
      status: logStatus.status,
      label: logStatus.label,
      issueReasons: logStatus.issueReasons,
      confidenceLow: logStatus.confidenceLow,
      confidenceText: logStatus.confidenceText,
      isPublicHoliday: holiday.isHoliday,
      holidayLabel: holiday.label,
    });
  });

  unscheduledRows.forEach((row) => {
    const staff = row.staff_name || row.ocr_name || "未配對";
    if (!groups.has(staff)) groups.set(staff, makeGroup(staff, groups.size));
    const group = groups.get(staff);
    group.actualHours += actualDurationHours(row.actual_in, row.actual_out);
    group.issues += 1;
    group.logs.push({
      date: row.date || "",
      day: formatScheduleDayOnly(row.date),
      code: "未排班",
      status: "unscheduled",
      label: comparisonStatusLabel(row.status),
    });
  });

  return [...groups.values()]
    .map((group) => {
      const summary = applyScheduleSummaryOverrides({
        ...group,
        days: group.dates.size,
        normalDays: group.normalDates.size,
        publicHolidayDays: group.publicHolidayDates.size,
        logs: group.logs.sort((left, right) => String(left.date).localeCompare(String(right.date))),
      });
      return {
        ...summary,
        actualDiff: group.actualHours - Number(summary.hours || 0),
      };
    })
    .sort((left, right) => left.order - right.order);
}

function rosterRowHtml(row, splitHolidayColumns = shouldSplitHolidayColumns()) {
  const selected = row.staff === state.selectedRosterStaff ? " is-selected" : "";
  const diffClass = Math.abs(row.actualDiff) < 0.005 ? "is-even" : row.actualDiff > 0 ? "is-over" : "is-under";
  const chips = row.logs.map((log) => rosterShiftChipHtml(log)).join("");
  const summaryCells = splitHolidayColumns
    ? `
      <td class="roster-metric-cell" data-label="Normal day 天數">${row.normalDays}</td>
      <td class="roster-metric-cell" data-label="Normal day 預定時數">${formatRosterHours(row.normalHours)}</td>
      <td class="roster-metric-cell is-ph" data-label="PH day 天數">${row.publicHolidayDays}</td>
      <td class="roster-metric-cell is-ph" data-label="PH day 預定時數">${formatRosterHours(row.publicHolidayHours)}</td>
    `
    : `
      <td class="roster-metric-cell" data-label="天數">${row.days}</td>
      <td class="roster-metric-cell" data-label="預定時數">${formatRosterHours(row.hours)}</td>
    `;
  return `
    <tr class="roster-click-row${selected}" tabindex="0" data-staff="${escapeAttr(row.staff)}">
      <td data-label="員工">${escapeHtml(row.staff)}</td>
      ${summaryCells}
      <td data-label="實際差異" class="roster-actual-diff ${diffClass}" title="實際 ${formatRosterHours(row.actualHours)} 小時，差異 ${formatSignedRosterHours(row.actualDiff)} 小時">${formatRosterHours(row.actualHours)} (${formatSignedRosterHours(row.actualDiff)})</td>
      <td data-label="排班日"><div class="roster-schedule-list">${chips || '<span class="muted">沒有排班</span>'}</div></td>
    </tr>
  `;
}

function rosterShiftChipHtml(log) {
  const classes = [
    "roster-shift-chip",
    `is-${log.status}`,
    log.isPublicHoliday ? "is-public-holiday" : "",
    log.confidenceLow ? "is-confidence" : "",
  ].filter(Boolean).join(" ");
  const title = log.isPublicHoliday && log.holidayLabel
    ? `${log.label}；PH ${log.holidayLabel}`
    : log.label;
  return (
    `<span class="${escapeAttr(classes)}" title="${escapeAttr(title)}">` +
    `<span>${escapeHtml(log.day || "-")}</span><strong>${escapeHtml(log.code || "-")}</strong>` +
    `${log.isPublicHoliday ? "<small>PH</small>" : ""}` +
    `${log.confidenceLow && log.confidenceText ? `<small>${escapeHtml(log.confidenceText)}</small>` : ""}</span>`
  );
}

function rosterLogStatus(entry, compareRow) {
  if (!ocrRows().length) return { status: "pending", label: "等待 OCR", issue: false, confidenceLow: false };
  if (!compareRow || !compareRow.has_actual) return { status: "missing", label: "沒有同員工/日期的打卡資料", issue: true, confidenceLow: false };
  const confidenceLow = shouldHighlightLowConfidence(compareRow);
  const withConfidence = (status) => {
    if (!confidenceLow) return { ...status, confidenceLow: false };
    return {
      ...status,
      issue: true,
      confidenceLow: true,
      confidenceText: confidenceScoreText(compareRow),
      label: `${status.label}；${confidenceLabel(compareRow)}`,
    };
  };
  const actualTimeReasons = compareActualTimeReasons(compareRow);
  if (actualTimeReasons.length) {
    const status = String(compareRow.status || "");
    const visualStatus = status.includes("Late") ? "late" : status.includes("Early Leave") ? "early" : "warning";
    return withConfidence({
      status: visualStatus,
      label: detailDifferenceText(entry, compareRow),
      issue: true,
      issueReasons: actualTimeReasons,
    });
  }
  if (isCompareRowOk(compareRow)) {
    return withConfidence({ status: "ok", label: `已配對：${compareRow.actual_in || "-"}-${compareRow.actual_out || "-"}`, issue: false });
  }
  return withConfidence({ status: "missing", label: comparisonStatusLabel(compareRow.status), issue: true });
}

function compareActualTimeReasons(row) {
  const status = String(row?.status || "");
  const reasons = [];
  if (Number(row?.early_in_minutes || 0) > 0) reasons.push("提早上班");
  if (status.includes("Late")) reasons.push("遲到");
  if (status.includes("Early Leave")) reasons.push("早退");
  if (Number(row?.overtime_minutes || 0) > 0) reasons.push("OT");
  return reasons;
}

function hasActualTimeWarning(row) {
  return compareActualTimeReasons(row).length > 0;
}

function isNonChargeableEarlyIn(row) {
  return String(row?.status || "") === "Early In" && Number(row?.early_in_minutes || 0) <= 0;
}

function isCompareRowOk(row) {
  if ((row?.flags || []).length || hasActualTimeWarning(row)) return false;
  const status = String(row?.status || "");
  return status === "Matched" || isNonChargeableEarlyIn(row);
}

function shouldHighlightLowConfidence(row) {
  if (!els.rosterConfidence?.checked) return false;
  if ((row.flags || []).includes("Name Check")) return true;
  const score = Number(row.name_match_score);
  return Number.isFinite(score) && score > 0 && score < 0.95;
}

function confidenceLabel(row) {
  return `姓名信心 ${confidenceScoreText(row) || "未知"}`;
}

function confidenceScoreText(row) {
  const score = Number(row.name_match_score);
  return Number.isFinite(score) ? `${Math.round(score * 100)}%` : "";
}

function formatConfidenceScore(row) {
  const score = confidenceScoreText(row);
  if (!score) return "-";
  const type = String(row.name_match_type || "").trim();
  return type ? `${score} ${type}` : score;
}

function scheduleEntryHours(entry) {
  const value = Number(entry?.scheduled_hours);
  if (Number.isFinite(value)) return value;
  return calculateHours(entry?.scheduled_in || "", entry?.scheduled_out || "") || 0;
}

function actualHoursForCompareRow(entry, row) {
  if (!row?.has_actual || !row.actual_in || !row.actual_out) return 0;
  const scheduledHours = scheduleEntryHours(entry);
  if (scheduledHours) {
    const late = Number(row.late_minutes || 0) / 60;
    const earlyIn = Number(row.early_in_minutes || 0) / 60;
    const early = Number(row.early_leave_minutes || 0) / 60;
    const overtime = Number(row.overtime_minutes || 0) / 60;
    return Math.max(0, scheduledHours + earlyIn - late - early + overtime);
  }
  return actualDurationHours(row.actual_in, row.actual_out);
}

function actualDurationHours(start, end) {
  const startMinutes = rosterTimeMinutes(start);
  let endMinutes = rosterTimeMinutes(end);
  if (startMinutes === null || endMinutes === null) return 0;
  if (endMinutes < startMinutes) endMinutes += 24 * 60;
  return roundHours((endMinutes - startMinutes) / 60);
}

function formatRosterHours(value) {
  return Number(value || 0).toFixed(2);
}

function formatSignedRosterHours(value) {
  const number = Number(value || 0);
  const formatted = Math.abs(number).toFixed(2);
  return number > 0 ? `+${formatted}` : number < 0 ? `-${formatted}` : "0.00";
}

function formatScheduleDayOnly(date) {
  const match = String(date || "").match(/(\d{4})-(\d{2})-(\d{2})/);
  return match ? String(Number(match[3])) : String(date || "");
}

function rosterTimeMinutes(value) {
  if (!isValidTime(String(value || ""))) return null;
  const [hour, minute] = String(value).split(":").map(Number);
  return hour * 60 + minute;
}

function rosterKey(staff, date) {
  return `${staff || ""}\u0000${date || ""}`;
}

function clearRosterSummary() {
  const splitHolidayColumns = shouldSplitHolidayColumns();
  renderRosterHeader(splitHolidayColumns);
  if (els.rosterSummaryText) {
    els.rosterSummaryText.textContent = "核對後會按員工彙總天數、缺卡和問題。";
  }
  if (els.rosterBody) {
    els.rosterBody.innerHTML = `<tr><td class="muted" colspan="${rosterColumnCount(splitHolidayColumns)}">尚未核對。</td></tr>`;
  }
}

function handleRosterClick(event) {
  const row = event.target.closest("tr[data-staff]");
  if (!row) return;
  openRosterDetail(row.dataset.staff || "");
}

function handleRosterKeydown(event) {
  if (event.key !== "Enter" && event.key !== " ") return;
  const row = event.target.closest("tr[data-staff]");
  if (!row) return;
  event.preventDefault();
  openRosterDetail(row.dataset.staff || "");
}

function openRosterDetail(staffName, options = {}) {
  if (!staffName) return;
  if (state.selectedRosterStaff !== staffName) {
    state.rosterImageIndex = 0;
    state.rosterImageFileName = "";
    resetRosterImageView();
  }
  state.selectedRosterStaff = staffName;
  if (options.sourceFileKey) {
    setRosterImageIndexForFile(staffName, options.sourceFileKey);
  }
  if (els.rosterDetailModal) els.rosterDetailModal.hidden = false;
  renderRosterSummary(state.comparison?.rows || []);
  renderRosterDetail(staffName);
  els.rosterDetailClose?.focus();
}

function closeRosterDetail() {
  if (els.rosterDetailModal) els.rosterDetailModal.hidden = true;
  if (els.rosterDetailRows) {
    els.rosterDetailRows.innerHTML = '<tr><td class="muted" colspan="6">請先在員工排班彙總選擇員工。</td></tr>';
  }
}

function renderRosterDetail(staffName) {
  if (!staffName || !els.rosterDetailRows) return;
  const rosterRows = buildRosterRows(state.comparison?.rows || []);
  const selected = rosterRows.find((row) => row.staff === staffName);
  const detailRows = rosterStaffDetailRows(staffName);
  const issueCount = detailRows.filter((row) => !["ok", "pending"].includes(row.status)).length;
  if (els.rosterDetailTitle) els.rosterDetailTitle.textContent = staffName;
  if (els.rosterDetailMeta) {
    els.rosterDetailMeta.textContent = selected
      ? `${selected.days} 天，預定 ${formatRosterHours(selected.hours)} 小時，實際 ${formatRosterHours(selected.actualHours)} 小時，差異 ${formatSignedRosterHours(selected.actualDiff)} 小時，${issueCount} 個問題。`
      : "Schedule vs actual";
  }
  if (els.rosterDetailHoursSummary) {
    els.rosterDetailHoursSummary.hidden = !selected;
    els.rosterDetailHoursSummary.textContent = selected
      ? `預定 ${formatRosterHours(selected.hours)} | 實際 ${formatRosterHours(selected.actualHours)} | 差異 ${formatSignedRosterHours(selected.actualDiff)}`
      : "";
  }
  if (els.rosterDetailAddRow) els.rosterDetailAddRow.disabled = !staffName;
  renderRosterDetailImage(staffName);
  if (!detailRows.length) {
    els.rosterDetailRows.innerHTML = '<tr><td class="muted" colspan="6">這位員工沒有排班或打卡資料。</td></tr>';
    return;
  }
  els.rosterDetailRows.innerHTML = detailRows.map(rosterDetailRowHtml).join("");
}

function rosterStaffDetailRows(staffName) {
  const rows = [];
  const scheduledDates = new Set();
  const compareByScheduleKey = new Map((state.comparison?.rows || [])
    .filter((row) => row.has_schedule)
    .map((row) => [rosterKey(row.staff_name, row.date), row]));
  (state.schedule?.entries || [])
    .filter((entry) => String(entry.staff_name || "").trim() === staffName)
    .sort((left, right) => String(left.date || "").localeCompare(String(right.date || "")))
    .forEach((entry) => {
      const date = String(entry.date || "");
      scheduledDates.add(date);
      const compareRow = compareByScheduleKey.get(rosterKey(staffName, date));
      const statusInfo = rosterLogStatus(entry, compareRow);
      rows.push({
        staff: staffName,
        date,
        code: entry.shift_code || entry.raw_shift_code || "-",
        schedule: scheduleWindowLabel(entry),
        actualIn: compareRow?.actual_in || "",
        actualOut: compareRow?.actual_out || "",
        status: statusInfo.status,
        statusLabel: statusLabelForDetail(statusInfo.status, compareRow),
        difference: detailDifferenceText(entry, compareRow),
        source: compareRow?.source_filename || (compareRow?.source_filenames || []).join(", ") || "",
        sourceFilenames: sourceFilenamesForRow(compareRow),
        canAdd: !compareRow?.has_actual,
        canDelete: Boolean(compareRow?.has_actual),
      });
    });

  (state.comparison?.rows || [])
    .filter((row) => row.has_actual && !row.has_schedule && (row.staff_name || row.ocr_name) === staffName)
    .sort((left, right) => String(left.date || "").localeCompare(String(right.date || "")))
    .forEach((row) => {
      rows.push({
        staff: staffName,
        date: row.date || "",
        code: "未排班",
        schedule: "-",
        actualIn: row.actual_in || "",
        actualOut: row.actual_out || "",
        status: "unscheduled",
        statusLabel: "未排班",
        difference: row.notes || "有打卡資料但 roster 沒有排班。",
        source: row.source_filename || (row.source_filenames || []).join(", ") || "",
        sourceFilenames: sourceFilenamesForRow(row),
        canAdd: false,
        canDelete: true,
      });
    });
  return rows.sort((left, right) => String(left.date || "").localeCompare(String(right.date || "")));
}

function rosterDetailRowHtml(item) {
  const statusClass = `is-${escapeAttr(item.status || "pending")}`;
  const actualInputs = `
    <div class="roster-actual-fields">
      <input type="text" inputmode="numeric" value="${escapeAttr(item.actualIn)}" placeholder="In" data-roster-field="in" data-staff="${escapeAttr(item.staff)}" data-date="${escapeAttr(item.date)}">
      <input type="text" inputmode="numeric" value="${escapeAttr(item.actualOut)}" placeholder="Out" data-roster-field="out" data-staff="${escapeAttr(item.staff)}" data-date="${escapeAttr(item.date)}">
    </div>
  `;
  const actions = item.canAdd
    ? `<button type="button" class="mini-button" data-roster-action="add" data-staff="${escapeAttr(item.staff)}" data-date="${escapeAttr(item.date)}">新增</button>`
    : `<button type="button" class="mini-button" data-roster-action="focus" data-staff="${escapeAttr(item.staff)}" data-date="${escapeAttr(item.date)}">修改</button>
       <button type="button" class="mini-button danger" data-roster-action="delete" data-staff="${escapeAttr(item.staff)}" data-date="${escapeAttr(item.date)}">刪除</button>`;
  return `
    <tr class="roster-detail-main ${statusClass}">
      <td>${escapeHtml(formatScheduleDayOnly(item.date))}</td>
      <td>${escapeHtml(item.code)}</td>
      <td>${escapeHtml(item.schedule)}</td>
      <td>${actualInputs}</td>
      <td><span class="roster-status-pill">${escapeHtml(item.statusLabel)}</span></td>
      <td><div class="roster-action-buttons">${actions}</div></td>
    </tr>
    <tr class="roster-detail-note ${statusClass}">
      <td colspan="6">${escapeHtml(item.difference || "-")}${item.sourceFilenames?.length ? ` · ${sourceLinksHtml(item.sourceFilenames, item.staff)}` : ""}</td>
    </tr>
  `;
}

function scheduleWindowLabel(entry) {
  const start = entry?.scheduled_in || "-";
  const end = entry?.scheduled_out || "-";
  return `${start}-${end}`;
}

function statusLabelForDetail(status, compareRowOrStatus) {
  const compareRow = compareRowOrStatus && typeof compareRowOrStatus === "object" ? compareRowOrStatus : null;
  const compareStatus = compareRow ? compareRow.status : compareRowOrStatus;
  const actualReasons = compareRow ? compareActualTimeReasons(compareRow) : [];
  if (["late", "early", "warning"].includes(status) && actualReasons.length) return actualReasons.join(" + ");
  if (status === "ok") return "已工作";
  if (status === "late") return "遲到";
  if (status === "early") return "早退";
  if (status === "missing") return "缺資料";
  if (status === "unscheduled") return "未排班";
  if (status === "pending") return "待 OCR";
  return comparisonStatusLabel(compareStatus || status);
}

function detailDifferenceText(entry, row) {
  if (!ocrRows().length) return "等待 OCR。";
  if (!row?.has_actual) return "沒有同員工/日期的打卡資料。";
  const parts = [];
  if (row.early_in_minutes) {
    parts.push(`提早上班 ${row.early_in_minutes} 分鐘`);
  }
  if (row.late_minutes) parts.push(`遲到 ${row.late_minutes} 分鐘`);
  if (row.early_leave_minutes) parts.push(`早退 ${row.early_leave_minutes} 分鐘`);
  if (row.overtime_minutes) parts.push(`OT ${row.overtime_minutes} 分鐘`);
  if ((row.flags || []).length) parts.push(formatComparisonFlags(row.flags));
  if (row.notes) parts.push(row.notes);
  return parts.join("；") || `實際 ${row.actual_in || "-"}-${row.actual_out || "-"}，排班 ${scheduleWindowLabel(entry)}。`;
}

async function handleRosterDetailChange(event) {
  const input = event.target.closest("[data-roster-field]");
  if (!input) return;
  const field = input.dataset.rosterField;
  const value = normalizeManualActualTime(input.value);
  if (value === null) {
    setStatus("請輸入 HH:MM 或 3-4 位數時間，例如 11:42 或 1142。", true);
    input.focus();
    return;
  }
  input.value = value;
  await setOcrActualForStaffDate(input.dataset.staff || state.selectedRosterStaff, input.dataset.date || "", field, value);
}

async function handleRosterDetailPaste(event) {
  const input = event.target.closest("input[data-roster-field]");
  if (!input) return;
  const text = event.clipboardData?.getData("text/plain") || "";
  if (!text.trim()) return;
  const grid = parseManualActualTimeGrid(text);
  if (!grid) {
    setStatus("貼上內容包含無效時間；請使用 HH:MM 或 3-4 位數時間，例如 11:42 或 1142。", true);
    event.preventDefault();
    return;
  }
  event.preventDefault();
  const edits = rosterActualPasteEdits(input, grid);
  if (!edits.length) return;
  edits.forEach((edit) => {
    edit.input.value = edit.value;
  });
  await setOcrActualCells(edits.map(({ staff, date, field, value }) => ({ staff, date, field, value })));
}

function parseManualActualTimeGrid(text) {
  const rows = String(text || "")
    .replace(/\r/g, "")
    .split("\n")
    .filter((line) => line.trim() || line.includes("\t"));
  if (!rows.length) return null;
  const grid = rows.map((line) => {
    const cells = line.includes("\t") ? line.split("\t") : line.trim().split(/\s+/);
    return cells.map((cell) => normalizeManualActualTime(cell));
  });
  return grid.some((row) => row.some((value) => value === null)) ? null : grid;
}

function rosterActualPasteEdits(startInput, grid) {
  const startRow = startInput.closest("tr.roster-detail-main");
  if (!startRow) return [];
  const rows = [...els.rosterDetailRows.querySelectorAll("tr.roster-detail-main")];
  const startRowIndex = rows.indexOf(startRow);
  const startColIndex = [...startRow.querySelectorAll("input[data-roster-field]")].indexOf(startInput);
  if (startRowIndex < 0 || startColIndex < 0) return [];
  const edits = [];
  grid.forEach((gridRow, rowOffset) => {
    const targetRow = rows[startRowIndex + rowOffset];
    if (!targetRow) return;
    const inputs = [...targetRow.querySelectorAll("input[data-roster-field]")];
    gridRow.forEach((value, colOffset) => {
      const targetInput = inputs[startColIndex + colOffset];
      if (!targetInput) return;
      edits.push({
        input: targetInput,
        staff: targetInput.dataset.staff || state.selectedRosterStaff,
        date: targetInput.dataset.date || "",
        field: targetInput.dataset.rosterField,
        value,
      });
    });
  });
  return edits;
}

async function handleRosterDetailClick(event) {
  if (event.target.closest("[data-logsheet-preview-key]")) {
    handleLogsheetPreviewClick(event);
    return;
  }
  const button = event.target.closest("button[data-roster-action]");
  if (!button) return;
  const staff = button.dataset.staff || state.selectedRosterStaff;
  const date = button.dataset.date || "";
  if (button.dataset.rosterAction === "add") {
    await addRosterActualRow(date, staff);
    return;
  }
  if (button.dataset.rosterAction === "delete") {
    await deleteRosterActualRows(staff, date);
    return;
  }
  if (button.dataset.rosterAction === "focus") {
    const row = button.closest("tr");
    row?.querySelector("input[data-roster-field]")?.focus();
  }
}

async function addFirstMissingRosterActualRow() {
  if (!state.selectedRosterStaff) return;
  const target = rosterStaffDetailRows(state.selectedRosterStaff).find((row) => row.canAdd)
    || rosterStaffDetailRows(state.selectedRosterStaff).find((row) => row.date);
  await addRosterActualRow(target?.date || "", state.selectedRosterStaff);
}

async function addRosterActualRow(date, staffName = state.selectedRosterStaff) {
  if (!state.ocr) {
    state.ocr = createOcrAggregate([]);
  }
  const rows = ocrRows().slice();
  rows.push({
    name: staffName,
    date,
    in: "",
    out: "",
    source_filename: staffLogsheetFile(staffName)?.name || "manual",
    source_filenames: [staffLogsheetFile(staffName)?.name || "manual"],
    all_times: [],
    warnings: ["人工新增 Actual Row"],
  });
  replaceOcrRows(rows);
  await refreshAfterRosterActualEdit(`已新增 ${staffName} ${formatScheduleDayOnly(date)} 的 Actual Row。`);
}

async function setOcrActualForStaffDate(staffName, date, field, value) {
  await setOcrActualCells([{ staff: staffName, date, field, value }]);
}

async function setOcrActualCells(edits) {
  const normalizedEdits = edits.filter((edit) => edit.staff && edit.date && ["in", "out"].includes(edit.field));
  if (!normalizedEdits.length) return;
  if (!state.ocr) {
    state.ocr = createOcrAggregate([]);
  }
  const rows = ocrRows().slice();
  normalizedEdits.forEach(({ staff, date, field, value }) => {
    setOcrActualInRows(rows, staff, date, field, value);
  });
  replaceOcrRows(rows);
  const first = normalizedEdits[0];
  const suffix = normalizedEdits.length > 1 ? `等 ${normalizedEdits.length} 格` : "";
  await refreshAfterRosterActualEdit(`已更新 ${first.staff} ${formatScheduleDayOnly(first.date)} ${suffix}的實際時間。`);
}

function setOcrActualInRows(rows, staffName, date, field, value) {
  if (!staffName || !date) return;
  let target = rows.find((row) => ocrRowMatchesStaffDate(row, staffName, date));
  if (!target) {
    target = {
      name: staffName,
      date,
      in: "",
      out: "",
      source_filename: staffLogsheetFile(staffName)?.name || "manual",
      source_filenames: [staffLogsheetFile(staffName)?.name || "manual"],
      all_times: [],
      warnings: ["人工新增 Actual Row"],
    };
    rows.push(target);
  }
  target[field === "in" ? "in" : "out"] = value || null;
  target.name = target.name || staffName;
  target.date = target.date || date;
  target.all_times = [target.in, target.out].filter(Boolean).sort((left, right) => (timeMinutes(left) ?? 0) - (timeMinutes(right) ?? 0));
}

async function deleteRosterActualRows(staffName, date) {
  const before = ocrRows();
  const after = before.filter((row) => !ocrRowMatchesStaffDate(row, staffName, date));
  if (after.length === before.length) {
    setStatus("找不到可刪除的 Actual Row。", true);
    return;
  }
  replaceOcrRows(after);
  await refreshAfterRosterActualEdit(`已刪除 ${staffName} ${formatScheduleDayOnly(date)} 的 Actual Row。`);
}

async function refreshAfterRosterActualEdit(message) {
  renderOcrResult();
  await refreshRosterComparison();
  if (state.selectedRosterStaff) renderRosterDetail(state.selectedRosterStaff);
  setStatus(message);
}

function replaceOcrRows(rows) {
  if (!state.ocr) return;
  state.ocr.daily_rows = rows;
  if (state.ocr.structured && typeof state.ocr.structured === "object") {
    state.ocr.structured.daily_rows = rows;
  }
}

function ocrRowMatchesStaffDate(row, staffName, date) {
  if (alignOcrDateToSchedule(row.date) !== date) return false;
  return sameStaffName(row.name, staffName)
    || sameStaffName(row.assigned_staff_name, staffName)
    || sameStaffName(staffNameFromFilename(row.source_filename), staffName);
}

function alignOcrDateToSchedule(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  const scheduleDates = scheduleDateValues();
  const isoMatch = text.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (isoMatch) {
    if (scheduleDates.includes(text)) return text;
    const [, , month, day] = isoMatch;
    const monthDayMatches = scheduleDates.filter((date) => String(date || "").slice(5) === `${month}-${day}`);
    if (monthDayMatches.length === 1) return monthDayMatches[0];
    const dayMatches = scheduleDates.filter((date) => String(date || "").endsWith(`-${day}`));
    return dayMatches.length === 1 ? dayMatches[0] : text;
  }
  const dayMatch = text.match(/(?:^|\D)([0-3]?\d)(?:\D|$)/);
  if (!dayMatch) return text;
  const day = Number(dayMatch[1]);
  const matches = scheduleDates.filter((date) => String(date || "").endsWith(`-${String(day).padStart(2, "0")}`));
  return matches.length === 1 ? matches[0] : text;
}

function scheduleDateValues() {
  return [...new Set((state.schedule?.entries || []).map((entry) => String(entry.date || "")).filter(Boolean))];
}

function sameStaffName(left, right) {
  const leftKey = normalizeNameKey(left);
  const rightKey = normalizeNameKey(right);
  if (!leftKey || !rightKey) return false;
  if (leftKey === rightKey) return true;
  return leftKey.includes(rightKey) || rightKey.includes(leftKey);
}

function normalizeNameKey(value) {
  return String(value || "").toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]+/g, "");
}

function staffNameFromFilename(filename) {
  return String(filename || "")
    .split(/[\\/]/)
    .pop()
    .replace(/\.[^.]+$/, "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^oil street\s+/i, "")
    .replace(/\b(?:timecard|timesheet|logsheet)\b/gi, "")
    .replace(/\s*\(\d+\)\s*$/, "")
    .replace(/\s+\d+$/, "")
    .replace(/\s+/g, " ")
    .trim();
}

function staffLogsheetFiles(staffName) {
  const staffKey = normalizeNameKey(staffName);
  const sourceFileKeys = staffLogsheetSourceFileKeys(staffName);
  const sourceMatched = [];
  const fallbackMatched = [];
  (state.logsheetFiles || []).forEach((file) => {
    const fileKey = logsheetFileKey(file.name);
    if (sourceFileKeys.has(fileKey)) {
      sourceMatched.push(file);
    } else if (file.assignedStaff && sameStaffName(file.assignedStaff, staffName)) {
      sourceMatched.push(file);
    } else if (
      staffKey &&
      file.previewUrl &&
      (sameStaffName(staffNameFromFilename(file.name), staffName) || normalizeNameKey(file.name).includes(staffKey))
    ) {
      fallbackMatched.push(file);
    }
  });
  return uniqueLogsheetFiles([...sourceMatched, ...fallbackMatched]).filter((file) => file.previewUrl);
}

function staffLogsheetSourceFileKeys(staffName) {
  const keys = new Set();
  (state.comparison?.rows || []).forEach((row) => {
    if (!row.has_actual) return;
    if (!sameStaffName(row.staff_name, staffName) && !sameStaffName(row.ocr_name, staffName)) return;
    [row.source_filename, ...(row.source_filenames || [])].forEach((filename) => {
      const key = logsheetFileKey(filename);
      if (key) keys.add(key);
    });
  });
  ocrRows().forEach((row) => {
    if (!sameStaffName(row.name, staffName) && !sameStaffName(staffNameFromFilename(row.source_filename), staffName)) return;
    [row.source_filename, ...(row.source_filenames || [])].forEach((filename) => {
      const key = logsheetFileKey(filename);
      if (key) keys.add(key);
    });
  });
  return keys;
}

function logsheetFileKey(filename) {
  return String(filename || "")
    .split(/[\\/]/)
    .pop()
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, "");
}

function uniqueLogsheetFiles(files) {
  const seen = new Set();
  const unique = [];
  files.forEach((file) => {
    const key = logsheetFileKey(file.name);
    if (!key || seen.has(key)) return;
    seen.add(key);
    unique.push(file);
  });
  return unique;
}

function staffLogsheetFile(staffName) {
  return staffLogsheetFiles(staffName)[0] || null;
}

function setRosterImageIndexForFile(staffName, fileKey) {
  const files = staffLogsheetFiles(staffName);
  const index = files.findIndex((file) => logsheetFileKey(file.name) === fileKey);
  if (index >= 0) {
    state.rosterImageIndex = index;
    state.rosterImageFileName = "";
    resetRosterImageView();
  }
}

function rosterColumnCount(splitHolidayColumns = shouldSplitHolidayColumns()) {
  return splitHolidayColumns ? 7 : 5;
}

function renderRosterHeader(splitHolidayColumns) {
  const table = els.rosterBody?.closest("table");
  const thead = table?.querySelector("thead");
  if (!table || !thead) return;
  renderRosterColumnStructure(table, splitHolidayColumns);
  thead.innerHTML = splitHolidayColumns
    ? `
      <tr>
        <th class="roster-staff-head" rowspan="2">員工</th>
        <th class="entries-head-group is-normal" colspan="2">
          <span class="entries-head-title">Normal day</span>
          <span class="entries-head-subtitle">非公眾假期</span>
        </th>
        <th class="entries-head-group is-ph" colspan="2">
          <span class="entries-head-title">PH day</span>
          <span class="entries-head-subtitle">公眾假期</span>
        </th>
        <th class="roster-diff-head" rowspan="2">實際差異</th>
        <th class="roster-schedule-head" rowspan="2">排班日</th>
      </tr>
      <tr>
        <th class="entries-metric-head"><span>天數</span><small>Days</small></th>
        <th class="entries-metric-head"><span>預定時數</span><small>Hours</small></th>
        <th class="entries-metric-head is-ph"><span>天數</span><small>Days</small></th>
        <th class="entries-metric-head is-ph"><span>預定時數</span><small>Hours</small></th>
      </tr>
    `
    : `
      <tr>
        <th>員工</th>
        <th class="entries-metric-head"><span>天數</span><small>Days</small></th>
        <th class="entries-metric-head"><span>預定時數</span><small>Hours</small></th>
        <th>實際差異</th>
        <th>排班日</th>
      </tr>
    `;
}

function renderRosterColumnStructure(table, splitHolidayColumns) {
  table.classList.toggle("is-holiday-split", Boolean(splitHolidayColumns));
  let colgroup = table.querySelector("colgroup[data-roster-columns]");
  if (!colgroup) {
    colgroup = document.createElement("colgroup");
    colgroup.dataset.rosterColumns = "true";
    table.insertBefore(colgroup, table.firstElementChild);
  }
  colgroup.innerHTML = splitHolidayColumns
    ? `
      <col class="roster-col-staff">
      <col class="roster-col-day">
      <col class="roster-col-hours">
      <col class="roster-col-ph-day">
      <col class="roster-col-ph-hours">
      <col class="roster-col-diff">
      <col class="roster-col-schedule">
    `
    : `
      <col class="roster-col-staff">
      <col class="roster-col-day">
      <col class="roster-col-hours">
      <col class="roster-col-diff">
      <col class="roster-col-schedule">
    `;
}

function logsheetFileByKey(fileKey) {
  return (state.logsheetFiles || []).find((file) => logsheetFileKey(file.name) === fileKey) || null;
}

function staffNameForLogsheetFile(file) {
  const fileKey = logsheetFileKey(file?.name);
  if (!fileKey) return "";
  if (file.assignedStaff) return file.assignedStaff;
  const compareRow = (state.comparison?.rows || []).find((row) => ocrRowFileKeys(row).has(fileKey));
  if (compareRow?.staff_name || compareRow?.ocr_name) return compareRow.staff_name || compareRow.ocr_name;
  const ocrRow = ocrRows().find((row) => ocrRowFileKeys(row).has(fileKey));
  if (ocrRow?.name) return ocrRow.name;
  return staffNameFromFilename(file.name);
}

function openLogsheetFilePreview(fileKey, staffName = "") {
  const file = logsheetFileByKey(fileKey);
  if (!file?.previewUrl) {
    setStatus("這個來源文件沒有可直接預覽的圖片；可能是 PDF，或尚未重新上傳原圖。", true);
    return;
  }
  const staff = staffName || staffNameForLogsheetFile(file);
  if (staff) {
    openRosterDetail(staff, { sourceFileKey: fileKey });
    return;
  }
  state.selectedRosterStaff = "";
  state.rosterImageIndex = 0;
  state.rosterImageFileName = "";
  resetRosterImageView();
  if (els.rosterDetailModal) els.rosterDetailModal.hidden = false;
  if (els.rosterDetailTitle) els.rosterDetailTitle.textContent = file.name;
  if (els.rosterDetailMeta) els.rosterDetailMeta.textContent = "來源文件預覽";
  if (els.rosterDetailHoursSummary) {
    els.rosterDetailHoursSummary.hidden = true;
    els.rosterDetailHoursSummary.textContent = "";
  }
  if (els.rosterDetailAddRow) els.rosterDetailAddRow.disabled = true;
  if (els.rosterDetailRows) {
    els.rosterDetailRows.innerHTML = '<tr><td class="muted" colspan="6">此來源文件尚未指派到員工。可先在來源文件清單選擇員工。</td></tr>';
  }
  renderRosterDetailImageFiles([file], new Set([fileKey]));
  els.rosterDetailClose?.focus();
}

function renderRosterDetailImage(staffName) {
  const files = staffLogsheetFiles(staffName);
  const sourceFileKeys = staffLogsheetSourceFileKeys(staffName);
  renderRosterDetailImageFiles(files, sourceFileKeys);
}

function renderRosterDetailImageFiles(files, sourceFileKeys = new Set()) {
  state.rosterImageIndex = clamp(state.rosterImageIndex, 0, Math.max(files.length - 1, 0));
  const file = files[state.rosterImageIndex] || null;
  const imageUrl = file?.previewUrl || "";
  updateRosterImageControls(files);
  if (els.rosterDetailImageTitle) els.rosterDetailImageTitle.textContent = file?.name || "沒有圖片";
  if (els.rosterDetailImageEmpty) {
    els.rosterDetailImageEmpty.hidden = Boolean(imageUrl);
    els.rosterDetailImageEmpty.textContent = rosterDetailImageEmptyText(files, sourceFileKeys);
  }
  if (!els.rosterDetailImage) return;
  if (imageUrl) {
    if (state.rosterImageFileName !== file.name) {
      state.rosterImageFileName = file.name;
      resetRosterImageView();
    }
    els.rosterDetailImage.src = imageUrl;
    els.rosterDetailImage.hidden = false;
    els.rosterDetailImage.onload = applyRosterImageTransform;
    applyRosterImageTransform();
  } else {
    state.rosterImageFileName = "";
    resetRosterImageView();
    els.rosterDetailImage.hidden = true;
    els.rosterDetailImage.removeAttribute("src");
  }
}

function rosterDetailImageEmptyText(files, sourceFileKeys) {
  if (files.length) return "這個檔案不是可直接預覽的圖片。";
  if (sourceFileKeys.size) {
    return "實際時間來自 OCR JSON，但目前沒有可直接預覽的原圖；可能未重新上傳圖片，或來源是 PDF。";
  }
  return currentProjectProfile().detailEmptyText;
}

function updateRosterImageControls(files) {
  const total = files.length;
  const current = total ? state.rosterImageIndex + 1 : 0;
  if (els.rosterDetailImageCount) els.rosterDetailImageCount.textContent = `${current} / ${total}`;
  if (els.rosterDetailPrevImage) els.rosterDetailPrevImage.disabled = total <= 1 || state.rosterImageIndex <= 0;
  if (els.rosterDetailNextImage) els.rosterDetailNextImage.disabled = total <= 1 || state.rosterImageIndex >= total - 1;
  if (els.rosterDetailResetImage) els.rosterDetailResetImage.disabled = total === 0;
}

function shiftRosterDetailImage(delta) {
  const files = staffLogsheetFiles(state.selectedRosterStaff);
  if (!files.length) return;
  state.rosterImageIndex = clamp(state.rosterImageIndex + delta, 0, files.length - 1);
  state.rosterImageFileName = "";
  resetRosterImageView();
  renderRosterDetailImage(state.selectedRosterStaff);
}

function handleRosterImageWheel(event) {
  if (!hasRosterDetailImage()) return;
  event.preventDefault();
  const nextScale = clamp(
    state.rosterImageView.scale * (event.deltaY < 0 ? 1.12 : 0.88),
    0.5,
    5,
  );
  state.rosterImageView.scale = nextScale;
  applyRosterImageTransform();
}

function handleRosterImagePointerDown(event) {
  if (!hasRosterDetailImage()) return;
  state.rosterImageDrag = {
    pointerId: event.pointerId,
    startX: event.clientX,
    startY: event.clientY,
    imageX: state.rosterImageView.x,
    imageY: state.rosterImageView.y,
  };
  els.rosterDetailImageStage?.setPointerCapture(event.pointerId);
  els.rosterDetailImageStage?.classList.add("dragging");
}

function handleRosterImagePointerMove(event) {
  const drag = state.rosterImageDrag;
  if (!drag || drag.pointerId !== event.pointerId || !hasRosterDetailImage()) return;
  state.rosterImageView.x = drag.imageX + event.clientX - drag.startX;
  state.rosterImageView.y = drag.imageY + event.clientY - drag.startY;
  applyRosterImageTransform();
}

function endRosterImageDrag(event) {
  if (state.rosterImageDrag?.pointerId === event.pointerId) {
    state.rosterImageDrag = null;
  }
  els.rosterDetailImageStage?.classList.remove("dragging");
}

function resetRosterImageView() {
  state.rosterImageView = { x: 0, y: 0, scale: 1 };
  state.rosterImageDrag = null;
  els.rosterDetailImageStage?.classList.remove("dragging");
  applyRosterImageTransform();
}

function applyRosterImageTransform() {
  if (!els.rosterDetailImage) return;
  const view = state.rosterImageView;
  els.rosterDetailImage.style.transform = `translate(${view.x}px, ${view.y}px) scale(${view.scale})`;
}

function hasRosterDetailImage() {
  return Boolean(els.rosterDetailImage?.getAttribute("src") && !els.rosterDetailImage.hidden);
}

function clamp(value, minimum, maximum) {
  return Math.max(minimum, Math.min(maximum, value));
}

function isComparisonIssue(row) {
  const status = String(row.status || "");
  if ((row.flags || []).length) return true;
  if (hasActualTimeWarning(row)) return true;
  return status !== "Matched";
}

function comparisonStatusText(summary) {
  const issues = [
    [currentProjectProfile().missingLogsheetLabel, summary.missing_logsheet_rows],
    ["未排班打卡", summary.unscheduled_punch_rows],
    ["姓名未配對", summary.unmatched_name_rows],
    ["姓名需覆核", summary.name_check_rows],
    ["遲到", summary.late_rows],
    ["早退", summary.early_leave_rows],
    ["早到", summary.early_in_rows],
    ["OT", summary.overtime_rows],
  ].filter(([, count]) => Number(count || 0) > 0);
  if (!Number(summary.compared_rows || 0)) return "沒有可核對資料。";
  if (!issues.length) return `已核對 ${summary.compared_rows} 筆，沒有發現主要問題。`;
  return `已核對 ${summary.compared_rows} 筆：` + issues.map(([label, count]) => `${label} ${count}`).join("、");
}

function comparisonStatusLabel(status) {
  const labels = {
    Matched: "已配對",
    "Early In": "提早上班",
    Late: "遲到",
    "Early Leave": "早退",
    "Late + Early Leave": "遲到 + 早退",
    "Missing In": "缺 In",
    "Missing Out": "缺 Out",
    "Missing In/Out": "缺 In/Out",
    "Missing Logsheet": currentProjectProfile().missingLogsheetLabel,
    "Unscheduled Punch": "未排班打卡",
    "Name Not Matched": "姓名未配對",
    "Date Not Matched": "日期未配對",
  };
  return labels[status] || status;
}

function comparisonStatusLabelForRow(row) {
  const actualReasons = compareActualTimeReasons(row);
  if (actualReasons.length) return actualReasons.join(" + ");
  if (isCompareRowOk(row)) return "已配對";
  return comparisonStatusLabel(row?.status || "");
}

function formatComparisonFlags(flags) {
  const labels = {
    "Name Check": "姓名需覆核",
    "Schedule Time Missing": "排班時間缺失",
  };
  return flags.map((flag) => labels[flag] || flag).join(", ");
}

function comparisonRowClass(row) {
  const status = String(row.status || "");
  if (isCompareRowOk(row)) return "compare-ok-row";
  if (["Name Not Matched", "Date Not Matched", "Missing In/Out", "Missing Logsheet"].includes(status)) return "compare-error-row";
  if (hasActualTimeWarning(row) || status === "Unscheduled Punch" || (row.flags || []).length) {
    return "compare-warning-row";
  }
  return "";
}

function displayMinutes(value) {
  if (value === null || value === undefined || value === "") return "";
  return `${value}`;
}

function renderOcrTable(rows) {
  els.ocrTableSection.hidden = false;
  els.ocrRowCount.textContent = `${rows.length} 筆`;
  renderTable(els.ocrTableBody, rows, (row) => [
    row.name,
    row.date,
    row.in,
    row.out,
  ]);
}

function ocrRows() {
  if (!state.ocr) return [];
  if (Array.isArray(state.ocr.daily_rows)) return state.ocr.daily_rows;
  if (Array.isArray(state.ocr.structured?.daily_rows)) return state.ocr.structured.daily_rows;
  return [];
}

function createOcrAggregate(files) {
  const sourceFilenames = files.map((file) => file.name);
  return {
    source_count: files.length,
    processed_count: 0,
    source_filename: sourceFilenames.join(", "),
    source_filenames: sourceFilenames,
    configured_model: "",
    response_model: "",
    finish_reason: "",
    daily_rows: [],
    structured: {
      document_type: "logsheet",
      daily_rows: [],
      results: [],
    },
    results: [],
    errors: [],
    no_data_files: [],
    usage: {},
  };
}

function addOcrResult(result) {
  if (!state.ocr) return;
  state.ocr.processed_count += 1;
  state.ocr.configured_model = state.ocr.configured_model || result.configured_model || "";
  state.ocr.response_model = state.ocr.response_model || result.response_model || "";
  state.ocr.finish_reason = state.ocr.finish_reason || result.finish_reason || "";
  state.ocr.results.push(result);
  state.ocr.structured.results.push(result.structured || null);
  state.ocr.daily_rows = mergeOcrDailyRows([
    ...state.ocr.daily_rows,
    ...rowsFromOcrResult(result),
  ]);
  applyLogsheetStaffAssignmentsToRows();
  state.ocr.structured.daily_rows = state.ocr.daily_rows;
  state.ocr.usage = combineUsage(state.ocr.results);
  renderLogsheetAssignments();
}

function addOcrError(filename, message) {
  if (!state.ocr) return;
  state.ocr.processed_count += 1;
  state.ocr.errors.push({ source_filename: filename, error: message });
}

function addOcrNoData(filename) {
  if (!state.ocr) return;
  if (!state.ocr.no_data_files.includes(filename)) {
    state.ocr.no_data_files.push(filename);
  }
}

function rowsFromOcrResult(result) {
  if (Array.isArray(result?.daily_rows)) return result.daily_rows;
  if (Array.isArray(result?.structured?.daily_rows)) return result.structured.daily_rows;
  return [];
}

function mergeOcrDailyRows(rows) {
  const merged = new Map();
  rows.forEach((row, index) => {
    const name = display(row.name).trim();
    const date = display(row.date).trim();
    const fallbackKey = `${display(row.source_filename)}:${index}`;
    const key = name || date ? `${name}||${date}` : fallbackKey;
    if (!merged.has(key)) {
      merged.set(key, {
        name: name || null,
        date: date || null,
        in: null,
        out: null,
        source_filename: row.source_filename || "",
        source_filenames: [],
        original_name: row.original_name || name || "",
        assigned_staff_name: row.assigned_staff_name || "",
        all_times: [],
        warnings: [],
      });
    }
    const target = merged.get(key);
    target.name = target.name || name || null;
    target.date = target.date || date || null;
    appendUnique(target.source_filenames, row.source_filenames || [row.source_filename].filter(Boolean));
    appendUnique(target.warnings, row.warnings || []);
    appendUnique(target.all_times, extractTimes([row.all_times, row.in, row.out]));
    target.all_times = [...new Set(target.all_times)].sort(compareTimes);
    if (target.all_times.length) {
      target.in = target.all_times[0];
      target.out = target.all_times.length > 1 ? target.all_times[target.all_times.length - 1] : null;
    } else {
      target.in = row.in || target.in;
      target.out = row.out || target.out;
    }
    if (!target.source_filename && target.source_filenames.length) {
      target.source_filename = target.source_filenames[0];
    }
  });
  return [...merged.values()];
}

function extractTimes(values) {
  const times = [];
  values.forEach((value) => {
    if (value === null || value === undefined || value === "") return;
    if (Array.isArray(value)) {
      times.push(...extractTimes(value));
      return;
    }
    const matches = String(value).match(/\b(?:[01]?\d|2[0-3])[:：.][0-5]\d\b/g) || [];
    matches.forEach((match) => {
      const [hour, minute] = match.replace("：", ":").replace(".", ":").split(":").map(Number);
      times.push(`${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`);
    });
  });
  return times;
}

function compareTimes(left, right) {
  return timeMinutes(left) - timeMinutes(right);
}

function timeMinutes(value) {
  const match = String(value).match(/(\d{1,2}):(\d{2})/);
  if (!match) return 24 * 60;
  return Number(match[1]) * 60 + Number(match[2]);
}

function combineUsage(results) {
  const usage = {};
  results.forEach((result) => {
    Object.entries(result.usage || {}).forEach(([key, value]) => {
      if (typeof value === "number") {
        usage[key] = (usage[key] || 0) + value;
      }
    });
  });
  return usage;
}

function appendUnique(target, values) {
  const source = Array.isArray(values) ? values : [values];
  source.forEach((value) => {
    if (value === null || value === undefined || value === "") return;
    if (!target.includes(value)) target.push(value);
  });
}

function showOcrProgress(total) {
  els.ocrProgress.hidden = false;
  els.ocrProgressBar.max = Math.max(total, 1);
  els.ocrProgressBar.value = 0;
  els.ocrProgressCount.textContent = `0 / ${total}`;
  els.ocrProgressText.textContent = "準備 OCR";
  els.ocrProgressList.innerHTML = "";
}

function setOcrProgress(current, total, message) {
  els.ocrProgress.hidden = false;
  els.ocrProgressBar.max = Math.max(total, 1);
  els.ocrProgressBar.value = current;
  els.ocrProgressCount.textContent = `${current} / ${total}`;
  els.ocrProgressText.textContent = message;
}

function hideOcrProgress() {
  els.ocrProgress.hidden = true;
  els.ocrProgressBar.value = 0;
  els.ocrProgressCount.textContent = "0 / 0";
  els.ocrProgressText.textContent = "等待 OCR";
  els.ocrProgressList.innerHTML = "";
}

function markOcrProgressItem(filename, status, message) {
  const key = `ocr-progress-${filename.replace(/[^a-z0-9_-]+/gi, "-")}`;
  let item = document.getElementById(key);
  if (!item) {
    item = document.createElement("div");
    item.id = key;
    els.ocrProgressList.appendChild(item);
  }
  item.className = `ocr-progress-item ${status === "error" ? "error" : ""} ${status === "no-data" ? "no-data" : ""}`;
  const label = status === "done" ? "完成" : status === "error" ? "失敗" : status === "no-data" ? "無資料" : "處理中";
  item.textContent = `${filename}：${label}${message ? " - " + message : ""}`;
}

function renderAll() {
  const schedule = state.schedule;
  renderScheduleVariantSelector();
  renderSummary(state.response.summary || {});
  renderMessages(schedule.warnings || [], schedule.errors || []);
  renderDateColumns(schedule.date_columns || []);
  renderStaff(schedule.staff || []);
  renderShiftTimes(schedule.shift_times || {});
  renderStaffFilter(schedule.staff || []);
  renderLogsheetAssignments();
  renderDngSheetReview();
  renderHolidayStatus();
  renderEntries();
  els.diagnostics.textContent = pretty(schedule.diagnostics || {});
  els.rawJson.textContent = pretty(schedule);
  renderExportTable();
  updateWorkflowState();
}

function renderSummary(summary) {
  const cards = [
    ["工作表", summary.sheet_name],
    ...(summary.schedule_month_label ? [["月份", summary.schedule_month_label]] : []),
    ["表頭列", summary.header_row],
    ["日期數", summary.date_count],
    ["員工數", summary.staff_count],
    ["排班筆數", summary.entry_count],
    ["班次規則數", summary.shift_time_count],
  ];
  els.summary.innerHTML = cards.map(([label, value]) => (
    `<div class="summary-card"><div class="label">${escapeHtml(label)}</div><div class="value">${escapeHtml(display(value))}</div></div>`
  )).join("");
}

function renderScheduleVariantSelector() {
  if (!els.scheduleVariantSection || !els.scheduleVariantSelect) return;
  const variants = state.scheduleVariants || [];
  if (variants.length <= 1) {
    els.scheduleVariantSection.hidden = true;
    els.scheduleVariantSelect.innerHTML = "";
    if (els.scheduleVariantStatus) els.scheduleVariantStatus.textContent = "此排班表只有一個月份。";
    return;
  }
  els.scheduleVariantSection.hidden = false;
  els.scheduleVariantSelect.innerHTML = variants.map((variant) => (
    `<option value="${escapeAttr(variant.key)}"${variant.key === state.selectedScheduleVariantKey ? " selected" : ""}>${escapeHtml(variant.label)}</option>`
  )).join("");
  if (els.scheduleVariantStatus) {
    const selected = selectedScheduleVariant(state.selectedScheduleVariantKey);
    const totalDates = selected?.summary?.date_count ?? (selected?.schedule?.date_columns || []).length;
    const totalEntries = selected?.summary?.entry_count ?? (selected?.schedule?.entries || []).length;
    const monthCount = variants.filter((variant) => variant.key !== ALL_SCHEDULE_VARIANT_KEY).length || variants.length;
    els.scheduleVariantStatus.textContent = `這份排班表包含 ${monthCount} 個月份；目前使用 ${selected?.label || ""}，${totalDates} 天，${totalEntries} 筆排班。`;
  }
}

function renderMessages(warnings, errors) {
  const items = [
    ...warnings.map((item) => ({ ...item, kind: "warning" })),
    ...errors.map((item) => ({ ...item, kind: "error", severity: "error" })),
  ];
  if (!items.length) {
    if (els.messagesSection) els.messagesSection.hidden = true;
    els.messages.innerHTML = "";
    els.messages.className = "message-list empty";
    return;
  }
  if (els.messagesSection) els.messagesSection.hidden = false;
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

function isScheduleSummaryHoursField(field) {
  return field === "hours" || field.endsWith("Hours") || scheduleSummaryMonthMetric(field) === "hours";
}

function isScheduleSummaryOverrideField(field) {
  return SCHEDULE_SUMMARY_OVERRIDE_FIELDS.has(field) || isScheduleSummaryMonthField(field);
}

function summaryOverrideInputValue(value, field) {
  const number = Number(value || 0);
  return isScheduleSummaryHoursField(field) ? formatRosterHours(number) : String(Math.round(number));
}

function renderScheduleSummaryInput(row, field, label) {
  const override = scheduleSummaryOverrideForStaff(row.staff);
  const isManual = Object.hasOwn(override, field);
  const isHours = isScheduleSummaryHoursField(field);
  return `
    <input
      class="summary-override-input${isManual ? " is-manual" : ""}"
      type="number"
      inputmode="decimal"
      min="0"
      max="${isHours ? "999" : "366"}"
      step="${isHours ? "0.25" : "1"}"
      value="${escapeAttr(summaryOverrideInputValue(row[field], field))}"
      data-summary-staff="${escapeAttr(row.staff)}"
      data-summary-field="${escapeAttr(field)}"
      aria-label="${escapeAttr(`${row.staff} ${label}`)}"
    >
  `;
}

function normalizeScheduleSummaryOverrideValue(field, value) {
  const text = String(value ?? "").trim();
  if (!text) return "";
  const number = Number(text);
  if (!Number.isFinite(number) || number < 0) return null;
  return isScheduleSummaryHoursField(field) ? roundHours(number) : Math.round(number);
}

function clearRelatedScheduleSummaryOverrides(rowOverride, field) {
  if (isScheduleSummaryMonthField(field)) {
    if (scheduleSummaryMonthMetric(field) === "days") {
      delete rowOverride.days;
      delete rowOverride.normalDays;
      delete rowOverride.publicHolidayDays;
    } else {
      delete rowOverride.hours;
      delete rowOverride.normalHours;
      delete rowOverride.publicHolidayHours;
    }
  } else if (field === "days") {
    delete rowOverride.normalDays;
    delete rowOverride.publicHolidayDays;
  } else if (field === "hours") {
    delete rowOverride.normalHours;
    delete rowOverride.publicHolidayHours;
  } else if (field === "normalDays" || field === "publicHolidayDays") {
    delete rowOverride.days;
  } else if (field === "normalHours" || field === "publicHolidayHours") {
    delete rowOverride.hours;
  }
  const monthMetric = field === "days" || field === "normalDays" || field === "publicHolidayDays"
    ? "days"
    : field === "hours" || field === "normalHours" || field === "publicHolidayHours"
      ? "hours"
      : "";
  if (monthMetric) {
    Object.keys(rowOverride).forEach((key) => {
      if (isScheduleSummaryMonthField(key) && scheduleSummaryMonthMetric(key) === monthMetric) {
        delete rowOverride[key];
      }
    });
  }
}

function scheduleSummaryFieldLabel(field) {
  if (isScheduleSummaryMonthField(field)) {
    const [, month, metric] = field.split(":");
    return `${scheduleMonthLabel(month)} ${metric === "hours" ? "Hours" : "Days"}`;
  }
  const labels = {
    days: "Days",
    hours: "Hours",
    normalDays: "Normal day Days",
    normalHours: "Normal day Hours",
    publicHolidayDays: "PH day Days",
    publicHolidayHours: "PH day Hours",
  };
  return labels[field] || field;
}

function handleScheduleSummaryOverrideChange(event) {
  const input = event.target?.closest?.("[data-summary-staff][data-summary-field]");
  if (!input) return;
  const staff = input.dataset.summaryStaff || "";
  const field = input.dataset.summaryField || "";
  if (!staff || !isScheduleSummaryOverrideField(field)) return;
  const normalized = normalizeScheduleSummaryOverrideValue(field, input.value);
  if (normalized === null) {
    setStatus("請輸入有效的天數或時數。", true);
    renderEntries();
    return;
  }

  const overrides = ensureScheduleSummaryOverrides();
  const rowOverride = overrides[staff] && typeof overrides[staff] === "object" ? overrides[staff] : {};
  clearRelatedScheduleSummaryOverrides(rowOverride, field);
  if (normalized === "") {
    delete rowOverride[field];
  } else {
    rowOverride[field] = normalized;
  }
  if (Object.keys(rowOverride).length) {
    overrides[staff] = rowOverride;
  } else {
    delete overrides[staff];
  }

  renderEntries();
  if (state.comparison) renderRosterSummary(state.comparison.rows || []);
  els.rawJson.textContent = pretty(state.schedule);
  renderExportTable();
  updateWorkflowState();
  setStatus(`${staff} ${scheduleSummaryFieldLabel(field)} 已更新。`);
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
  const rosterRows = buildScheduleEntryRosterRows(filtered);
  const allRosterRows = buildScheduleEntryRosterRows(indexedEntries);
  const monthColumns = scheduleMonthColumnsFromRows(allRosterRows);
  const splitMonthColumns = monthColumns.length > 1;
  const splitHolidayColumns = !splitMonthColumns && shouldSplitHolidayColumns();
  renderEntriesHeader({ splitHolidayColumns, monthColumns: splitMonthColumns ? monthColumns : [] });
  const holidayEntryCount = rosterRows.reduce((total, row) => total + row.publicHolidayCount, 0);
  const holidaySuffix = holidayEntryCount ? "，PH " + holidayEntryCount + " 筆" : "";
  els.entryCount.textContent = rosterRows.length + " / " + allRosterRows.length
    + " 位員工，" + filtered.length + " / " + state.entries.length + " 筆" + holidaySuffix;
  renderTable(els.entries, rosterRows, (row) => {
    const summaryCells = splitMonthColumns
      ? [
          row.staff,
          ...monthColumns.flatMap((month) => [
            htmlCell(renderScheduleSummaryInput(row, month.daysField, `${month.label} Days`)),
            htmlCell(renderScheduleSummaryInput(row, month.hoursField, `${month.label} Hours`)),
          ]),
        ]
      : splitHolidayColumns
      ? [
          row.staff,
          htmlCell(renderScheduleSummaryInput(row, "normalDays", "Normal day Days")),
          htmlCell(renderScheduleSummaryInput(row, "normalHours", "Normal day Hours")),
          htmlCell(renderScheduleSummaryInput(row, "publicHolidayDays", "PH day Days")),
          htmlCell(renderScheduleSummaryInput(row, "publicHolidayHours", "PH day Hours")),
        ]
      : [
          row.staff,
          htmlCell(renderScheduleSummaryInput(row, "days", "Days")),
          htmlCell(renderScheduleSummaryInput(row, "hours", "Hours")),
        ];
    return [
      ...summaryCells,
      htmlCell(renderScheduleRosterIssues(row)),
      htmlCell(renderScheduleRosterChips(row)),
    ];
  });
}

function shouldSplitHolidayColumns() {
  return Boolean(state.holidayCountSunday || state.holidayUseOfficial || state.customHolidays.length);
}

function renderEntriesHeader(options = {}) {
  const splitHolidayColumns = Boolean(options.splitHolidayColumns);
  const monthColumns = Array.isArray(options.monthColumns) ? options.monthColumns : [];
  const splitMonthColumns = monthColumns.length > 1;
  if (!els.entriesTableHead) return;
  renderEntriesColumnStructure({ splitHolidayColumns, monthColumns });
  if (splitMonthColumns) {
    const monthHeaders = monthColumns.map((month) => `
        <th class="entries-head-group is-month" colspan="2">
          <span class="entries-head-title">${escapeHtml(month.label)}</span>
          <span class="entries-head-subtitle">月份</span>
        </th>
      `).join("");
    const metricHeaders = monthColumns.map(() => `
        <th class="entries-metric-head"><span>天數</span><small>Days</small></th>
        <th class="entries-metric-head"><span>預定時數</span><small>Hours</small></th>
      `).join("");
    els.entriesTableHead.innerHTML = `
      <tr>
        <th class="entries-staff-head" rowspan="2">員工</th>
        ${monthHeaders}
        <th class="entries-review-head" rowspan="2">需覆核</th>
        <th class="entries-schedule-head" rowspan="2">排班日</th>
      </tr>
      <tr>${metricHeaders}</tr>
    `;
    return;
  }
  els.entriesTableHead.innerHTML = splitHolidayColumns
    ? `
      <tr>
        <th class="entries-staff-head" rowspan="2">員工</th>
        <th class="entries-head-group is-normal" colspan="2">
          <span class="entries-head-title">Normal day</span>
          <span class="entries-head-subtitle">非公眾假期</span>
        </th>
        <th class="entries-head-group is-ph" colspan="2">
          <span class="entries-head-title">PH day</span>
          <span class="entries-head-subtitle">公眾假期</span>
        </th>
        <th class="entries-review-head" rowspan="2">需覆核</th>
        <th class="entries-schedule-head" rowspan="2">排班日</th>
      </tr>
      <tr>
        <th class="entries-metric-head"><span>天數</span><small>Days</small></th>
        <th class="entries-metric-head"><span>預定時數</span><small>Hours</small></th>
        <th class="entries-metric-head is-ph"><span>天數</span><small>Days</small></th>
        <th class="entries-metric-head is-ph"><span>預定時數</span><small>Hours</small></th>
      </tr>
    `
    : `
      <tr>
        <th>員工</th>
        <th class="entries-metric-head"><span>天數</span><small>Days</small></th>
        <th class="entries-metric-head"><span>預定時數</span><small>Hours</small></th>
        <th>需覆核</th>
        <th>排班日</th>
      </tr>
    `;
}

function renderEntriesColumnStructure(options = {}) {
  const splitHolidayColumns = Boolean(options.splitHolidayColumns);
  const monthColumns = Array.isArray(options.monthColumns) ? options.monthColumns : [];
  const splitMonthColumns = monthColumns.length > 1;
  const table = els.entriesTableHead?.closest("table");
  if (!table) return;
  table.classList.toggle("is-holiday-split", Boolean(splitHolidayColumns) && !splitMonthColumns);
  table.classList.toggle("is-month-split", splitMonthColumns);
  let colgroup = table.querySelector("colgroup[data-entries-columns]");
  if (!colgroup) {
    colgroup = document.createElement("colgroup");
    colgroup.dataset.entriesColumns = "true";
    table.insertBefore(colgroup, table.firstElementChild);
  }
  if (splitMonthColumns) {
    const monthCols = monthColumns.map(() => `
      <col class="entries-col-month-day">
      <col class="entries-col-month-hours">
    `).join("");
    colgroup.innerHTML = `
      <col class="entries-col-staff">
      ${monthCols}
      <col class="entries-col-review">
      <col class="entries-col-schedule">
    `;
    return;
  }
  colgroup.innerHTML = splitHolidayColumns
    ? `
      <col class="entries-col-staff">
      <col class="entries-col-day">
      <col class="entries-col-hours">
      <col class="entries-col-ph-day">
      <col class="entries-col-ph-hours">
      <col class="entries-col-review">
      <col class="entries-col-schedule">
    `
    : `
      <col class="entries-col-staff">
      <col class="entries-col-day">
      <col class="entries-col-hours">
      <col class="entries-col-review">
      <col class="entries-col-schedule">
    `;
}

function buildScheduleEntryRosterRows(indexedEntries = []) {
  const groups = new Map();
  const staffOrder = new Map((state.schedule?.staff || [])
    .map((staff, index) => [String(staff.name || "").trim(), index]));
  const makeGroup = (staff, order) => ({
    staff,
    order,
    dates: new Set(),
    normalDates: new Set(),
    publicHolidayDates: new Set(),
    hours: 0,
    normalHours: 0,
    publicHolidayHours: 0,
    months: new Map(),
    warnings: 0,
    unresolved: 0,
    reviewed: 0,
    holidayEntries: 0,
    logs: [],
  });

  indexedEntries.forEach(({ entry, index }) => {
    const staff = String(entry.staff_name || "").trim() || "未命名員工";
    if (!groups.has(staff)) {
      groups.set(staff, makeGroup(staff, staffOrder.get(staff) ?? index ?? groups.size));
    }
    const group = groups.get(staff);
    const date = String(entry.date || "");
    const status = scheduleEntryStatus(entry);
    const hours = scheduleEntryHours(entry);
    const holiday = holidayInfoForDate(date);
    const monthKey = scheduleMonthKeyFromDate(date);
    if (date) group.dates.add(date);
    group.hours += hours;
    if (monthKey) {
      if (!group.months.has(monthKey)) {
        group.months.set(monthKey, { month: monthKey, dates: new Set(), hours: 0 });
      }
      const monthSummary = group.months.get(monthKey);
      if (date) monthSummary.dates.add(date);
      monthSummary.hours += hours;
    }
    if (holiday.isHoliday) {
      if (date) group.publicHolidayDates.add(date);
      group.publicHolidayHours += hours;
    } else {
      if (date) group.normalDates.add(date);
      group.normalHours += hours;
    }
    if (status === "missing") group.unresolved += 1;
    if (status === "warning") group.warnings += 1;
    if (status === "reviewed") group.reviewed += 1;
    if (holiday.isHoliday) group.holidayEntries += 1;
    group.logs.push({
      date,
      day: formatScheduleDayOnly(date),
      code: scheduleEntryChipCode(entry),
      hours,
      status,
      isPublicHoliday: holiday.isHoliday,
      holidayLabel: holiday.label,
      label: scheduleEntryChipLabel(entry, holiday),
    });
  });

  return [...groups.values()]
    .map((group) => {
      const scheduleMonths = [...group.months.values()]
        .sort((left, right) => left.month.localeCompare(right.month))
        .map((month) => ({
          month: month.month,
          label: scheduleMonthLabel(month.month),
          daysField: scheduleMonthField(month.month, "days"),
          hoursField: scheduleMonthField(month.month, "hours"),
        }));
      const monthFields = {};
      scheduleMonths.forEach((month) => {
        const source = group.months.get(month.month);
        monthFields[month.daysField] = source?.dates.size || 0;
        monthFields[month.hoursField] = roundHours(source?.hours || 0);
      });
      return applyScheduleSummaryOverrides({
        ...group,
        ...monthFields,
        scheduleMonths,
        days: group.dates.size,
        normalDays: group.normalDates.size,
        publicHolidayDays: group.publicHolidayDates.size,
        issueCount: group.unresolved + group.warnings,
        publicHolidayCount: group.holidayEntries,
        logs: group.logs.sort((left, right) => String(left.date).localeCompare(String(right.date))),
      });
    })
    .sort((left, right) => left.order - right.order || left.staff.localeCompare(right.staff));
}

function scheduleEntryStatus(entry) {
  if (entry.review) return "reviewed";
  if (String(entry.resolution_source || "").startsWith("unresolved")) return "missing";
  if ((entry.warnings || []).length) return "warning";
  return "ok";
}

function scheduleEntryChipCode(entry) {
  return entry.shift_code || entry.raw_shift_code || display(entry.raw_value) || "-";
}

function scheduleEntryChipLabel(entry, holiday = { isHoliday: false, label: "" }) {
  const parts = [
    entry.date,
    entry.staff_name,
    entry.schedule_cell,
    display(entry.raw_value),
    entry.shift_code ? `班次 ${entry.shift_code}` : "",
    entry.scheduled_in || entry.scheduled_out ? `${entry.scheduled_in || "-"}-${entry.scheduled_out || "-"}` : "",
    entry.scheduled_hours !== null && entry.scheduled_hours !== undefined ? `${entry.scheduled_hours}h` : "",
    holiday.isHoliday ? `PH ${holiday.label || ""}`.trim() : "",
    entry.resolution_source,
    (entry.warnings || []).join(", "),
  ].filter(Boolean);
  return parts.join(" | ");
}

function renderScheduleRosterIssues(row) {
  if (!row.issueCount && !row.reviewed) {
    return '<span class="schedule-issue-count is-clean">0</span>';
  }
  const parts = [];
  if (row.unresolved) parts.push(`${row.unresolved} 未解析`);
  if (row.warnings) parts.push(`${row.warnings} 警告`);
  if (row.reviewed) parts.push(`${row.reviewed} 已修正`);
  const klass = row.unresolved ? "is-error" : row.warnings ? "is-warning" : "is-reviewed";
  return `<span class="schedule-issue-count ${klass}">${escapeHtml(parts.join(" / "))}</span>`;
}

function renderScheduleRosterChips(row) {
  const chips = row.logs.map((log) => (
    `<span class="roster-shift-chip is-${escapeAttr(log.status)}${log.isPublicHoliday ? " is-public-holiday" : ""}" title="${escapeAttr(log.label)}">` +
    `<span>${escapeHtml(log.day || "-")}</span><strong>${escapeHtml(log.code || "-")}</strong>${log.isPublicHoliday ? "<small>PH</small>" : ""}</span>`
  )).join("");
  return `<div class="roster-schedule-list">${chips || '<span class="muted">沒有排班</span>'}</div>`;
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

function resetExportTableSelection() {
  state.exportTableSelection = {
    rows: new Set(),
    columns: new Set(),
    cells: new Set(),
  };
}

function clearExportTable() {
  resetExportTableSelection();
  if (els.exportTableDataset) {
    els.exportTableDataset.innerHTML = "";
    els.exportTableDataset.disabled = true;
  }
  if (els.exportTableHead) els.exportTableHead.innerHTML = "";
  if (els.exportTableBody) {
    els.exportTableBody.innerHTML = '<tr><td class="muted">尚未載入資料。</td></tr>';
  }
  updateExportTableSelectionStatus();
}

function exportTableDatasets() {
  const datasets = [
    {
      id: "compare_rows",
      label: "核對明細",
      columns: [
        ["date", "日期"],
        ["staff_name", "排班員工"],
        ["ocr_name", "OCR 姓名"],
        ["confidence", "信心"],
        ["shift_code", "班次"],
        ["scheduled_in", "預定上班"],
        ["scheduled_out", "預定下班"],
        ["scheduled_hours", "預定時數"],
        ["actual_in", "實際上班"],
        ["actual_out", "實際下班"],
        ["actual_hours", "實際時數"],
        ["raw_late_minutes", "原始遲到"],
        ["late_minutes", "計算遲到"],
        ["early_leave_minutes", "早退"],
        ["status", "狀態"],
        ["flags", "標記"],
        ["notes", "備註"],
        ["source_filename", "來源文件"],
      ],
      rows: exportCompareRows(),
    },
    {
      id: "schedule_entries",
      label: "排班資料",
      columns: [
        ["date", "日期"],
        ["day", "日"],
        ["staff_name", "員工"],
        ["shift_code", "班次"],
        ["scheduled_in", "預定上班"],
        ["scheduled_out", "預定下班"],
        ["scheduled_hours", "預定時數"],
        ["actual_in", "實際上班"],
        ["actual_out", "實際下班"],
        ["actual_hours", "實際時數"],
        ["status", "狀態"],
        ["source_filename", "來源文件"],
        ["schedule_cell", "排班儲存格"],
        ["resolution_source", "解析來源"],
        ["warnings", "警告"],
      ],
      rows: exportScheduleEntryRows(),
    },
    {
      id: "roster_summary",
      label: "員工排班彙總",
      columns: [
        ["staff", "員工"],
        ["days", "天數"],
        ["hours", "預定時數"],
        ["normalDays", "Normal 天數"],
        ["normalHours", "Normal 時數"],
        ["publicHolidayDays", "PH 天數"],
        ["publicHolidayHours", "PH 時數"],
        ["actualHours", "實際時數"],
        ["actualDiff", "實際差異"],
        ["issues", "需覆核"],
        ["schedule", "排班日"],
      ],
      rows: exportRosterSummaryRows(),
    },
    {
      id: "shift_times",
      label: "班次時間",
      columns: [
        ["code", "班次"],
        ["start", "上班"],
        ["end", "下班"],
        ["hours", "時數"],
        ["applies_to", "適用"],
        ["specific_dates", "指定日期"],
        ["source", "來源"],
        ["cell", "儲存格"],
      ],
      rows: exportShiftTimeRows(),
    },
  ];
  return datasets.filter((dataset) => dataset.rows.length);
}

function renderExportTable() {
  if (!els.exportTableBody || !els.exportTableHead || !els.exportTableDataset) return;
  const datasets = exportTableDatasets();
  if (!datasets.length) {
    clearExportTable();
    return;
  }
  const defaultDataset = datasets.find((dataset) => dataset.id === DEFAULT_EXPORT_TABLE_DATASET);
  if (!state.exportTableUserSelected && defaultDataset && state.exportTableDataset !== defaultDataset.id) {
    state.exportTableDataset = defaultDataset.id;
    resetExportTableSelection();
  } else if (!datasets.some((dataset) => dataset.id === state.exportTableDataset)) {
    state.exportTableDataset = defaultDataset?.id || datasets[0].id;
    resetExportTableSelection();
  }
  els.exportTableDataset.disabled = false;
  els.exportTableDataset.innerHTML = datasets.map((dataset) => (
    `<option value="${escapeAttr(dataset.id)}"${dataset.id === state.exportTableDataset ? " selected" : ""}>` +
    `${escapeHtml(dataset.label)} (${dataset.rows.length})</option>`
  )).join("");
  const table = currentExportTable();
  els.exportTableHead.innerHTML = exportTableHeadHtml(table);
  els.exportTableBody.innerHTML = exportTableBodyHtml(table);
  updateExportTableSelectionStatus();
}

function currentExportTable() {
  const datasets = exportTableDatasets();
  return datasets.find((dataset) => dataset.id === state.exportTableDataset) || datasets[0] || {
    id: "",
    label: "",
    columns: [],
    rows: [],
  };
}

function exportTableHeadHtml(table) {
  return `
    <tr>
      <th class="export-row-head">
        <button type="button" class="export-row-selector" data-export-select-all-rows="true" aria-label="選取全部列">#</button>
      </th>
      ${table.columns.map(([key, label]) => (
        `<th class="${state.exportTableSelection.columns.has(key) ? "is-selected-column" : ""}">` +
        `<button type="button" class="export-column-selector" data-export-column="${escapeAttr(key)}" title="選取 ${escapeAttr(label)} 整欄" aria-label="選取 ${escapeAttr(label)} 整欄">${escapeHtml(label)}</button>` +
        `</th>`
      )).join("")}
    </tr>
  `;
}

function exportTableBodyHtml(table) {
  if (!table.rows.length) {
    return `<tr><td class="muted" colspan="${table.columns.length + 1}">沒有資料。</td></tr>`;
  }
  return table.rows.map((row, rowIndex) => {
    const rowSelected = state.exportTableSelection.rows.has(rowIndex);
    const cells = table.columns.map(([key]) => {
      const cellKey = exportCellKey(rowIndex, key);
      const cellSelected = state.exportTableSelection.cells.has(cellKey);
      const columnSelected = state.exportTableSelection.columns.has(key);
      const classes = [
        "export-cell",
        rowSelected ? "is-selected-row" : "",
        columnSelected ? "is-selected-column" : "",
        cellSelected ? "is-selected-cell" : "",
      ].filter(Boolean).join(" ");
      return (
        `<td class="${classes}" data-export-row="${rowIndex}" data-export-column="${escapeAttr(key)}">` +
        `${escapeHtml(exportCellText(row[key]))}</td>`
      );
    }).join("");
    return (
      `<tr class="${rowSelected ? "is-selected-row" : ""}">` +
      `<th class="export-row-head">` +
      `<button type="button" class="export-row-selector${rowSelected ? " is-selected" : ""}" data-export-row="${rowIndex}">${rowIndex + 1}</button>` +
      `</th>${cells}</tr>`
    );
  }).join("");
}

function handleExportTableDatasetChange() {
  state.exportTableDataset = els.exportTableDataset?.value || DEFAULT_EXPORT_TABLE_DATASET;
  state.exportTableUserSelected = true;
  resetExportTableSelection();
  renderExportTable();
}

function handleExportTableClick(event) {
  const allRowsButton = event.target.closest("[data-export-select-all-rows]");
  if (allRowsButton) {
    toggleAllExportRows();
    renderExportTable();
    return;
  }
  const columnButton = event.target.closest("[data-export-column]");
  if (columnButton && columnButton.classList.contains("export-column-selector")) {
    toggleSetValue(state.exportTableSelection.columns, columnButton.dataset.exportColumn || "");
    renderExportTable();
    return;
  }
  const rowButton = event.target.closest(".export-row-selector[data-export-row]");
  if (rowButton) {
    toggleSetValue(state.exportTableSelection.rows, Number(rowButton.dataset.exportRow));
    renderExportTable();
    return;
  }
  const cell = event.target.closest("[data-export-row][data-export-column]");
  if (cell) {
    toggleSetValue(state.exportTableSelection.cells, exportCellKey(Number(cell.dataset.exportRow), cell.dataset.exportColumn || ""));
    renderExportTable();
  }
}

function toggleAllExportRows() {
  const table = currentExportTable();
  if (state.exportTableSelection.rows.size === table.rows.length) {
    state.exportTableSelection.rows.clear();
  } else {
    state.exportTableSelection.rows = new Set(table.rows.map((_row, index) => index));
  }
}

function toggleSetValue(set, value) {
  if (value === "" || Number.isNaN(value)) return;
  if (set.has(value)) {
    set.delete(value);
  } else {
    set.add(value);
  }
}

function clearExportTableSelection() {
  resetExportTableSelection();
  renderExportTable();
  setStatus("Excel 表格選取已清除。");
}

async function copyExportTableSelection(mode = "selected") {
  const table = currentExportTable();
  if (!table.rows.length) {
    setStatus("沒有可複製的 Excel 表格資料。", true);
    return;
  }
  const selection = exportCopySelection(table, mode);
  const tsv = exportTableToTsv(table, selection);
  await navigator.clipboard.writeText(tsv);
  const columnText = selection.columns.length === table.columns.length ? "全部欄" : `${selection.columns.length} 欄`;
  setStatus(`已複製 ${selection.rows.length} 列、${columnText}，可直接貼到 Excel。`);
}

function exportCopySelection(table, mode) {
  if (mode === "all") {
    return {
      rows: table.rows.map((_row, index) => index),
      columns: table.columns.map(([key]) => key),
      cellOnly: false,
    };
  }
  const { rows, columns, cells } = state.exportTableSelection;
  if (!rows.size && !columns.size && cells.size) {
    const cellRows = uniqueSorted([...cells].map((key) => Number(key.split(":")[0])));
    const cellColumns = table.columns
      .map(([key]) => key)
      .filter((key) => cellRows.some((rowIndex) => cells.has(exportCellKey(rowIndex, key))));
    return { rows: cellRows, columns: cellColumns, cellOnly: true };
  }
  return {
    rows: rows.size ? uniqueSorted([...rows]) : table.rows.map((_row, index) => index),
    columns: columns.size ? table.columns.map(([key]) => key).filter((key) => columns.has(key)) : table.columns.map(([key]) => key),
    cellOnly: false,
  };
}

function exportTableToTsv(table, selection) {
  const includeHeaders = Boolean(els.exportTableIncludeHeaders?.checked);
  const lines = [];
  const selectedColumns = table.columns.filter(([key]) => selection.columns.includes(key));
  if (includeHeaders) {
    lines.push(selectedColumns.map(([_key, label]) => tsvCell(label)).join("\t"));
  }
  selection.rows.forEach((rowIndex) => {
    const row = table.rows[rowIndex] || {};
    const values = selectedColumns.map(([key]) => {
      if (selection.cellOnly && !state.exportTableSelection.cells.has(exportCellKey(rowIndex, key))) return "";
      return tsvCell(exportCellText(row[key]));
    });
    lines.push(values.join("\t"));
  });
  return lines.join("\n");
}

function updateExportTableSelectionStatus() {
  if (!els.exportTableSelectionStatus) return;
  const table = currentExportTable();
  if (!table.rows.length) {
    els.exportTableSelectionStatus.textContent = "尚未載入資料。";
    return;
  }
  const { rows, columns, cells } = state.exportTableSelection;
  const parts = [];
  if (rows.size) parts.push(`${rows.size} 列`);
  if (columns.size) {
    const selectedColumnLabels = table.columns
      .filter(([key]) => columns.has(key))
      .map(([_key, label]) => label);
    const visibleLabels = selectedColumnLabels.slice(0, 3).join("、");
    const suffix = selectedColumnLabels.length > 3 ? ` 等 ${selectedColumnLabels.length} 欄` : "";
    parts.push(`${columns.size} 欄${visibleLabels ? `（${visibleLabels}${suffix}）` : ""}`);
  }
  if (cells.size) parts.push(`${cells.size} 格`);
  els.exportTableSelectionStatus.textContent = `${table.label}：${table.rows.length} 列，${table.columns.length} 欄${parts.length ? `；已選 ${parts.join("、")}` : "；未選取時會複製全部"}`;
}

function exportScheduleEntryRows() {
  const compareByScheduleKey = new Map((state.comparison?.rows || [])
    .filter((row) => row.has_schedule)
    .map((row) => [rosterKey(row.staff_name, row.date), row]));
  return (state.schedule?.entries || []).map((entry) => {
    const compareRow = compareByScheduleKey.get(rosterKey(entry.staff_name, entry.date));
    return {
      date: entry.date || "",
      day: formatScheduleDayOnly(entry.date),
      staff_name: entry.staff_name || "",
      shift_code: entry.shift_code || entry.raw_shift_code || "",
      scheduled_in: entry.scheduled_in || "",
      scheduled_out: entry.scheduled_out || "",
      scheduled_hours: formatRosterHours(scheduleEntryHours(entry)),
      actual_in: compareRow?.actual_in || "",
      actual_out: compareRow?.actual_out || "",
      actual_hours: compareRow?.has_actual ? formatRosterHours(actualDurationHours(compareRow.actual_in, compareRow.actual_out)) : "",
      status: compareRow ? comparisonStatusLabelForRow(compareRow) : "",
      source_filename: sourceFilenamesForRow(compareRow).join("；"),
      schedule_cell: entry.schedule_cell || "",
      resolution_source: entry.resolution_source || "",
      warnings: (entry.warnings || []).join("；"),
    };
  });
}

function exportRosterSummaryRows() {
  return buildRosterRows(state.comparison?.rows || []).map((row) => ({
    staff: row.staff,
    days: row.days,
    hours: formatRosterHours(row.hours),
    normalDays: row.normalDays,
    normalHours: formatRosterHours(row.normalHours),
    publicHolidayDays: row.publicHolidayDays,
    publicHolidayHours: formatRosterHours(row.publicHolidayHours),
    actualHours: formatRosterHours(row.actualHours),
    actualDiff: formatSignedRosterHours(row.actualDiff),
    issues: row.issues,
    schedule: row.logs.map((log) => `${log.day || "-"} ${log.code || "-"}`).join("；"),
  }));
}

function exportCompareRows() {
  return (state.comparison?.rows || []).map((row) => ({
    date: row.date || "",
    staff_name: row.staff_name || "",
    ocr_name: row.ocr_name || "",
    confidence: formatConfidenceScore(row),
    shift_code: row.shift_code || row.raw_shift_code || "",
    scheduled_in: row.scheduled_in || "",
    scheduled_out: row.scheduled_out || "",
    scheduled_hours: row.has_schedule ? formatRosterHours(scheduleEntryHours(row)) : "",
    actual_in: row.actual_in || "",
    actual_out: row.actual_out || "",
    actual_hours: row.has_actual ? formatRosterHours(actualDurationHours(row.actual_in, row.actual_out)) : "",
    raw_late_minutes: displayMinutes(row.raw_late_minutes),
    late_minutes: displayMinutes(row.late_minutes),
    early_leave_minutes: displayMinutes(row.early_leave_minutes),
    status: comparisonStatusLabelForRow(row),
    flags: formatComparisonFlags(row.flags || []),
    source_filename: sourceFilenamesForRow(row).join("；"),
    notes: row.notes || "",
  }));
}

function exportShiftTimeRows() {
  return Object.entries(state.schedule?.shift_times || {}).map(([code, shift]) => ({
    code,
    start: shift.start || "",
    end: shift.end || "",
    hours: shift.hours ?? "",
    applies_to: shift.applies_to || "",
    specific_dates: (shift.specific_dates || []).join("；"),
    source: shift.source || "",
    cell: shift.cell || shift.coordinate || "",
  }));
}

function exportCellKey(rowIndex, columnKey) {
  return `${rowIndex}:${columnKey}`;
}

function exportCellText(value) {
  if (Array.isArray(value)) return value.join("；");
  if (value && typeof value === "object") return compactJson(value);
  return value ?? "";
}

function tsvCell(value) {
  return String(value ?? "").replace(/\r?\n/g, " ").replace(/\t/g, " ");
}

function uniqueSorted(values) {
  return [...new Set(values)].filter((value) => Number.isFinite(value)).sort((left, right) => left - right);
}

async function copyJson() {
  if (!state.schedule) {
    setStatus("沒有可複製的 JSON。", true);
    return;
  }
  await navigator.clipboard.writeText(pretty(state.schedule));
  setStatus("JSON 已複製。");
}

async function copyOcrJson() {
  if (!state.ocr) {
    setStatus("沒有可複製的 OCR JSON。", true);
    return;
  }
  await navigator.clipboard.writeText(pretty(state.ocr.structured || state.ocr));
  setStatus("OCR JSON 已複製。");
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

function downloadOcrJson() {
  if (!state.ocr) {
    setStatus("沒有可下載的 OCR JSON。", true);
    return;
  }
  const blob = new Blob([pretty(state.ocr.structured || state.ocr)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  const filename = (state.ocr.source_filename || "logsheet").replace(/\.[^.]+$/, "");
  anchor.href = url;
  anchor.download = `${filename}.ocr.json`;
  anchor.click();
  URL.revokeObjectURL(url);
  setStatus("OCR JSON 下載已開始。");
}

function resetReview() {
  if (!state.originalSchedule) {
    setStatus("沒有可重設的修正。", true);
    return;
  }
  state.schedule = deepClone(state.originalSchedule);
  state.entries = state.schedule.entries || [];
  state.scheduleConfirmed = false;
  renderAll();
  setWorkflowStep("check-schedule");
  setStatus("已重設所有修正，請重新確認排班表。");
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
  renderExportTable();
  refreshRosterComparison();
  updateWorkflowState();
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

function normalizeManualActualTime(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  const colonMatch = text.replace(/[.：]/g, ":").match(/^(\d{1,2}):([0-5]\d)$/);
  if (colonMatch) {
    const hour = Number(colonMatch[1]);
    const minute = Number(colonMatch[2]);
    return hour >= 0 && hour <= 23 ? `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}` : null;
  }
  const compactMatch = text.match(/^(\d{3,4})$/);
  if (!compactMatch) return null;
  const digits = compactMatch[1].padStart(4, "0");
  const hour = Number(digits.slice(0, 2));
  const minute = Number(digits.slice(2));
  if (hour > 23 || minute > 59) return null;
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
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
