const DEFAULT_API_BASE = "http://127.0.0.1:8000";

const hasDocument = typeof document !== "undefined";
const goalEl = hasDocument ? document.getElementById("goal") : null;
const urlEl = hasDocument ? document.getElementById("url") : null;
const domainEl = hasDocument ? document.getElementById("domain") : null;
const maxStepsEl = hasDocument ? document.getElementById("maxSteps") : null;
const apiBaseEl = hasDocument ? document.getElementById("apiBase") : null;
const runBtn = hasDocument ? document.getElementById("runBtn") : null;
const continueBtn = hasDocument ? document.getElementById("continueBtn") : null;
const agentHintEl = hasDocument ? document.getElementById("agentHint") : null;
const statusEl = hasDocument ? document.getElementById("status") : null;
const resultEl = hasDocument ? document.getElementById("result") : null;
const statusBadgeEl = hasDocument ? document.getElementById("statusBadge") : null;
const modelBadgeEl = hasDocument ? document.getElementById("modelBadge") : null;
const configStatusEl = hasDocument ? document.getElementById("configStatus") : null;
const markdownLinkEl = hasDocument ? document.getElementById("markdownLink") : null;
const quickChips = hasDocument ? Array.from(document.querySelectorAll(".quick-chip")) : [];
let liveRefreshTimer = null;

function normalizeApiBase(value) {
  const raw = String(value || DEFAULT_API_BASE).trim();
  if (/^https?:\/\//i.test(raw)) {
    return raw.replace(/\/+$/, "");
  }
  const protocol = /^(localhost|127\.0\.0\.1|\[?::1\]?)(:\d+)?(\/|$)/i.test(raw) ? "http" : "https";
  return `${protocol}://${raw}`.replace(/\/+$/, "");
}

function normalizeUrl(url) {
  if (!url) return "https://example.com";
  return /^https?:\/\//i.test(url) ? url : `https://${url}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function truncate(value, limit = 180) {
  const text = String(value ?? "").replace(/\s+/g, " ").trim();
  return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
}

function linkTo(url, label) {
  if (!url || !/^https?:\/\//i.test(url)) {
    return escapeHtml(label || url || "");
  }
  return `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(label || url)}</a>`;
}

function listItems(items, renderItem, limit = 5) {
  if (!Array.isArray(items) || !items.length) return "";
  return `<ol>${items.slice(0, limit).map((item, index) => `<li>${renderItem(item, index)}</li>`).join("")}</ol>`;
}

function card(title, body) {
  if (!body) return "";
  return `<section class="card"><h2>${escapeHtml(title)}</h2>${body}</section>`;
}

function scoreBadge(item) {
  if (item?.score === undefined || item?.score === null || item?.score === "") return "";
  return `<span class="score">Score ${escapeHtml(item.score)}</span>`;
}

function renderMonitor(monitorMessage, observations = []) {
  if (!monitorMessage && (!Array.isArray(observations) || !observations.length)) return "";
  const rows = Array.isArray(observations)
    ? observations.slice(-4).map((item) => {
      const verdict = item.verdict || {};
      const cls = verdict.ok ? "" : "warn";
      const pageAction = item.pageAction?.action
        ? `<br><span class="small">页面动作：${escapeHtml(item.pageAction.action.reason || item.pageAction.action.type)} (${escapeHtml(item.pageAction.result?.reason || item.pageAction.result?.ok || "")})</span>`
        : "";
      return `<li><span class="pill ${cls}">${escapeHtml(verdict.ok ? "满足" : "继续")}</span> ${escapeHtml(verdict.reason || "observed")}<br><span class="small">${linkTo(item.url, truncate(item.title || item.url, 80))}</span>${pageAction}</li>`;
    }).join("")
    : "";
  return card("浏览器监视", `<p>${escapeHtml(monitorMessage || "已记录监视轨迹")}</p>${rows ? `<ul>${rows}</ul>` : ""}`);
}

function renderChecklist(result) {
  const workflowChecklist = result?.llm?.dynamic_agent_loop?.requirement_slots
    || result?.llm?.plan?.requirement_slots
    || result?.llm?.dynamic_agent_loop?.evidence_checklist
    || result?.llm?.plan?.evidence_checklist
    || [];
  const latestNode = Array.isArray(result?.workflow?.nodes) && result.workflow.nodes.length
    ? result.workflow.nodes[result.workflow.nodes.length - 1]
    : null;
  const liveChecklist = latestNode?.inputs?.checklist_status || [];
  const items = Array.isArray(liveChecklist) && liveChecklist.length ? liveChecklist : workflowChecklist;
  if (!Array.isArray(items) || !items.length) return "";
  return card(
    "任务缺口",
    `<ul>${items.slice(0, 8).map((item) => {
      const status = item.status || "unknown";
      const cls = status === "satisfied" ? "" : status === "partial" ? "warn" : "error";
      const label = status === "satisfied" ? "已满足" : status === "partial" ? "部分满足" : "待补充";
      return `<li><span class="pill ${cls}">${escapeHtml(label)}</span> <strong>${escapeHtml(item.stage || item.requirement_slot || item.evidence_stage || item.purpose || "stage")}</strong><p>${escapeHtml(truncate(item.evidence || item.purpose || item.example_query || "", 160))}</p></li>`;
    }).join("")}</ul>`
  );
}

function renderRecentActions(result) {
  const steps = Array.isArray(result?.steps) ? result.steps : [];
  if (!steps.length) return "";
  return card(
    "最近动作",
    `<ol>${steps.slice(-5).map((step) => {
      const detail = step.detail || {};
      const fields = detail.fields || {};
      const cls = step.ok ? "" : "error";
      const target = fields.requirement_slot || fields.evidence_stage || step.action || "action";
      const url = detail.url || "";
      const submitAfterType = fields.submit_after_type;
      const submitLine = submitAfterType
        ? `<br><span class="small">自动提交：${escapeHtml(submitAfterType.ok ? (submitAfterType.method || "submitted") : "failed")} </span>`
        : "";
      const failureLine = !step.ok && step.failure_type
        ? `<br><span class="small">失败类型：${escapeHtml(step.failure_type)}</span>`
        : "";
      return `<li><span class="pill ${cls}">${escapeHtml(step.ok ? "成功" : "失败")}</span> ${escapeHtml(step.action || "action")}<br><span class="small">${escapeHtml(target)}</span>${submitLine}${failureLine}${url ? `<br><span class="small">${linkTo(url, truncate(url, 78))}</span>` : ""}</li>`;
    }).join("")}</ol>`
  );
}

function renderFailureAnalysis(result) {
  const rows = Array.isArray(result?.report?.failure_analysis)
    ? result.report.failure_analysis
    : Array.isArray(result?.failure_analysis)
      ? result.failure_analysis
      : [];
  if (!rows.length) return "";
  return card(
    "失败分析",
    `<ul>${rows.map((item) => {
      const example = item?.latest_example || {};
      const detail = example?.error ? `<p>${escapeHtml(truncate(example.error, 160))}</p>` : "";
      const action = example?.action ? `<br><span class="small">最近动作：${escapeHtml(example.action)}</span>` : "";
      return `<li><span class="pill ${item?.count ? "warn" : ""}">${escapeHtml(String(item?.count ?? 0))}</span> <strong>${escapeHtml(item?.failure_type || "unknown_failure")}</strong>${action}${detail}</li>`;
    }).join("")}</ul>`
  );
}

function renderRequirementProgression(result) {
  const items = Array.isArray(result?.report?.requirement_progression) ? result.report.requirement_progression : [];
  if (!items.length) return "";
  return card(
    "需求推进",
    `<ol>${items.slice(0, 8).map((item) => {
      const status = item.status || "missing";
      const cls = status === "satisfied" ? "" : status === "partial" ? "warn" : "error";
      const label = status === "satisfied" ? "已满足" : status === "partial" ? "推进中" : "待补";
      const action = item.latest_action ? `<br><span class="small">动作：${escapeHtml(item.latest_action)}</span>` : "";
      const url = item.latest_url ? `<br><span class="small">${linkTo(item.latest_url, truncate(item.latest_url, 72))}</span>` : "";
      const evidence = item.evidence_summary ? `<p>${escapeHtml(truncate(item.evidence_summary, 160))}</p>` : "";
      return `<li><span class="pill ${cls}">${escapeHtml(label)}</span> <strong>${escapeHtml(item.requirement_slot || item.purpose || "slot")}</strong>${action}${url}${evidence}</li>`;
    }).join("")}</ol>`
  );
}

function renderEvidencePlan(result) {
  const items = Array.isArray(result?.report?.evidence_plan)
    ? result.report.evidence_plan
    : Array.isArray(result?.report?.search_plan)
      ? result.report.search_plan
      : [];
  if (!items.length) return "";
  return card(
    "证据提示",
    `<ol>${items.slice(0, 5).map((item) => {
      const purpose = item?.purpose || item?.requirement_slot || "evidence step";
      const hint = item?.evidence_hint || item?.query || "";
      const source = item?.source ? `<br><span class="small">来源：${escapeHtml(item.source)}</span>` : "";
      return `<li><strong>${escapeHtml(purpose)}</strong>${hint ? `<p>${escapeHtml(truncate(hint, 160))}</p>` : ""}${source}</li>`;
    }).join("")}</ol>`
  );
}

function renderWorkflowMeta(result) {
  const workflow = result?.workflow || {};
  const template = workflow.template || "dynamic_workflow";
  const steps = Array.isArray(result?.steps) ? result.steps.length : 0;
  const nodes = Array.isArray(workflow?.nodes) ? workflow.nodes.length : 0;
  const mode = result?.llm?.dynamic_agent_loop?.mode || "observe_plan_act_verify";
  return card(
    "Agent Loop",
    `<div class="meta">
      <span class="pill">${escapeHtml(template)}</span>
      <span class="pill">mode: ${escapeHtml(mode)}</span>
      <span class="pill">steps: ${escapeHtml(steps)}</span>
      <span class="pill">nodes: ${escapeHtml(nodes)}</span>
    </div>
    <p>每轮基于当前页面状态、历史动作、证据缺口和截图线索重新规划下一步，而不是按固定脚本执行。</p>`
  );
}

function renderNeedsReview(result, monitorMessage = "", observations = []) {
  const workflow = result?.workflow || {};
  const report = result?.report || {};
  const lastObservation = Array.isArray(observations) && observations.length ? observations[observations.length - 1] : null;
  const verdict = lastObservation?.verdict || {};
  const suggestionByReason = {
    not_on_repository_page_yet: "插件已经到达 GitHub，但还没进入具体仓库页。建议直接打开一个仓库候选，再继续比较 stars、README 和最近更新。",
    zero_or_no_match_results: "当前搜索结果没有有效命中。建议把任务改短一些，只保留核心关键词后重试。",
    shopping_search_page_needs_product_or_review_page: "目前还停留在商品搜索页。建议先打开商品详情页或评测页，再继续收集证据。",
    not_on_video_page_yet: "目前还没进入具体视频页。建议先打开一个视频候选，再继续整理字幕和内容。",
    insufficient_task_match: "当前页面和目标的匹配度还不够。建议切换到更垂直的来源页，或缩小任务范围后重试。",
  };
  const reasonLabel = verdict.reason || "needs_manual_review";
  const suggestions = [];
  if (monitorMessage) suggestions.push(monitorMessage);
  if (suggestionByReason[reasonLabel]) suggestions.push(suggestionByReason[reasonLabel]);
  if (Array.isArray(report.next_actions)) suggestions.push(...report.next_actions);
  if (Array.isArray(report.uncertainties)) suggestions.push(...report.uncertainties);
  const uniqueSuggestions = Array.from(new Set(suggestions.filter(Boolean))).slice(0, 4);
  const pageHint = lastObservation?.url
    ? `<p>当前停留页面：${linkTo(lastObservation.url, truncate(lastObservation.title || lastObservation.url, 90))}</p>`
    : "";
  const body = `
    <p>这一步需要人工接一下，因为自动流程还没有拿到足够稳定的候选或证据。</p>
    <p><strong>卡住原因：</strong>${escapeHtml(reasonLabel)}</p>
    ${pageHint}
    ${uniqueSuggestions.length ? `<ul>${uniqueSuggestions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : ""}
  `;
  return card("需要你接手一下", body);
}

function renderTimeline(timeline = []) {
  if (!Array.isArray(timeline) || !timeline.length) return "";
  const body = `<ul>${timeline.slice(-12).map((item) => {
    const level = item?.level || "info";
    const cls = level === "error" ? "error" : level === "warn" ? "warn" : "";
    return `<li><span class="pill ${cls}">${escapeHtml(level)}</span> ${escapeHtml(item?.text || "")}</li>`;
  }).join("")}</ul>`;
  return card("Agent Streaming", body);
}

function renderAgentResult(result, monitorMessage = "", observations = [], timeline = []) {
  if (!result || typeof result !== "object") {
    return '<p class="empty">运行结果将显示在这里</p>';
  }
  const report = result.report || {};
  const workflow = result.workflow || {};
  const digest = report.video_digest || {};
  const okClass = result.ok ? "" : "error";
  const meta = `
    <div class="meta">
      <span class="pill ${okClass}">${escapeHtml(result.ok ? "完成" : "需复核")}</span>
      <span class="pill">域：${escapeHtml(workflow.domain || "auto")}</span>
      <span class="pill">候选：${escapeHtml((report.candidates || []).length)}</span>
      <span class="pill">证据：${escapeHtml((result.memory?.evidence || []).length)}</span>
    </div>`;
  const summary = card("任务摘要", `${meta}<p>${escapeHtml(report.summary || result.goal || "暂无摘要")}</p>`);
  const workflowMeta = renderWorkflowMeta(result);
  const checklist = renderChecklist(result);
  const requirementProgression = renderRequirementProgression(result);
  const failureAnalysis = renderFailureAnalysis(result);
  const streaming = renderTimeline(timeline);
  const recentActions = renderRecentActions(result);
  const evidencePlan = renderEvidencePlan(result);
  const reasoning = card(
    "动作依据",
    listItems(report.reasoning_outline, (item) => escapeHtml(item), 4) +
      listItems(report.requirement_progression, (item) => `${escapeHtml(item.requirement_slot || item.purpose || "slot")}：${escapeHtml(item.evidence_summary || item.purpose || "")}`, 4)
  );
  const recommendations = card(
    "推荐与候选",
    listItems(report.recommendations?.length ? report.recommendations : report.candidates, (item, index) => {
      const name = item.name || item.title || `候选 ${index + 1}`;
      const reason = item.reason || item.support || item.description || "";
      return `${linkTo(item.url, truncate(name, 86))}${scoreBadge(item)}${reason ? `<p>${escapeHtml(truncate(reason, 150))}</p>` : ""}`;
    }, 5)
  );
  const matrix = card(
    "对比证据",
    listItems(report.comparison_matrix, (item) => {
      const bits = [
        item.score_reasons?.length && `依据：${item.score_reasons.join("、")}`,
        item.price_signal && `价格：${item.price_signal}`,
        item.stars && `stars：${item.stars}`,
        item.language && `语言：${item.language}`,
        item.best_for && `适合：${item.best_for}`,
        item.fit_notes,
        item.snippet,
      ].filter(Boolean).join(" | ");
      return `${linkTo(item.url, truncate(item.name || item.title || "证据页", 74))}${scoreBadge(item)}${bits ? `<p>${escapeHtml(truncate(bits, 190))}</p>` : ""}`;
    }, 4)
  );
  const video = card(
    "视频整理",
    digest.url || digest.title
      ? `<p>${linkTo(digest.url, truncate(digest.title || digest.url, 110))}</p>
         ${digest.visible_transcript ? `<p>${escapeHtml(truncate(digest.visible_transcript, 220))}</p>` : ""}
         ${digest.screenshot_path ? `<p class="small">截图：${escapeHtml(digest.screenshot_path)}</p>` : ""}`
      : ""
  );
  const multimodal = card(
    "多模态状态",
    listItems(report.multimodal_notes, (item) => {
      const cls = item.status === "available" ? "" : item.status === "unavailable" ? "warn" : "";
      return `<span class="pill ${cls}">${escapeHtml(item.provider || "vision")} ${escapeHtml(item.status || "")}</span><p>${escapeHtml(truncate(item.finding || item.reason || item.purpose || "", 160))}</p>`;
    }, 4)
  );
  const monitor = renderMonitor(monitorMessage, observations);
  const needsReview = result.ok ? "" : renderNeedsReview(result, monitorMessage, observations);
  const uncertainties = card("不确定性/下一步", [
    listItems(report.uncertainties, (item) => escapeHtml(item), 3),
    listItems(report.next_actions, (item) => escapeHtml(item), 3),
  ].join(""));
  return [summary, workflowMeta, checklist, requirementProgression, evidencePlan, recentActions, streaming, failureAnalysis, reasoning, recommendations, matrix, video, multimodal, monitor, needsReview, uncertainties].filter(Boolean).join("");
}

function setStatus(text, isError = false) {
  if (!statusEl) return;
  statusEl.textContent = text;
  statusEl.classList.toggle("error", isError);
}

function setStatusBadge(status = "idle") {
  if (!statusBadgeEl) return;
  const normalized = String(status || "idle");
  statusBadgeEl.textContent = normalized.replace("_", " ");
  statusBadgeEl.className = `status-badge ${normalized}`;
}

function setModelBadge(text = "model pending") {
  if (!modelBadgeEl) return;
  modelBadgeEl.textContent = text;
}

function setConfigStatus(text, state = "") {
  if (!configStatusEl) return;
  configStatusEl.textContent = text;
  configStatusEl.className = `config-status ${state}`.trim();
}

async function fetchBackendConfig(apiBase = getApiBase()) {
  const response = await fetch(`${apiBase}/api/config`);
  const data = await response.json();
  if (!response.ok || !data.ok) {
    throw new Error(data.error || "无法读取后端配置");
  }
  return data;
}

function setResult(result, monitorMessage = "", observations = [], timeline = []) {
  if (!resultEl) return;
  resultEl.innerHTML = renderAgentResult(result, monitorMessage, observations, timeline);
}

function getApiBase() {
  return normalizeApiBase(apiBaseEl?.value || DEFAULT_API_BASE);
}

function syncMarkdownLink(apiBase = getApiBase()) {
  if (!markdownLinkEl) return;
  markdownLinkEl.href = `${apiBase}/api/latest-report`;
}

async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tabs.length || !tabs[0].id) {
    throw new Error("无法获取当前标签页");
  }
  return tabs[0];
}

async function loadDraft() {
  const data = await chrome.storage.local.get([
    "goal",
    "url",
    "domain",
    "maxSteps",
    "apiBase",
    "agentStatus",
    "agentError",
    "lastResult",
    "finalUrl",
    "monitorMessage",
    "monitorObservations",
    "agentTimeline"
  ]);
  if (data.goal) goalEl.value = data.goal;
  if (data.url) urlEl.value = data.url;
  if (data.domain && domainEl) domainEl.value = data.domain;
  if (data.maxSteps) maxStepsEl.value = String(data.maxSteps);
  if (data.apiBase && apiBaseEl) apiBaseEl.value = data.apiBase;
  syncMarkdownLink(getApiBase());

  if (data.agentStatus === "running") {
    setStatusBadge("running");
    setResult(data.lastResult || { ok: false, goal: data.goal || "", report: { summary: "Agent 正在分步规划和执行。" } }, data.monitorMessage || "正在执行 Agent...", data.monitorObservations || [], data.agentTimeline || []);
    setStatus("正在执行 Agent...");
  } else if (data.agentStatus === "monitoring") {
    setStatusBadge("monitoring");
    setResult(data.lastResult || null, data.monitorMessage || "正在监视页面是否满足任务要求", data.monitorObservations || [], data.agentTimeline || []);
    setStatus("监视中...");
  } else if (data.agentStatus === "done") {
    setStatusBadge("done");
    setResult(data.lastResult || {}, data.monitorMessage || "", data.monitorObservations || [], data.agentTimeline || []);
    setStatus(data.finalUrl ? `执行完成，已控制浏览器打开：${data.finalUrl}` : "执行完成");
  } else if (data.agentStatus === "needs_review") {
    setStatusBadge("needs_review");
    setResult(data.lastResult || {}, data.monitorMessage || "监视后仍未确认满足任务要求", data.monitorObservations || [], data.agentTimeline || []);
    setStatus("需要复核：页面可能仍未满足任务要求", true);
  } else if (data.agentStatus === "error") {
    setStatusBadge("error");
    setResult(data.lastResult || { ok: false, report: { summary: "Agent 执行失败。" } }, data.agentError || "", data.monitorObservations || [], data.agentTimeline || []);
    setStatus(`执行失败：${data.agentError || "未知错误"}`, true);
  } else {
    setStatusBadge("idle");
  }
}

function startLiveRefresh() {
  if (liveRefreshTimer) return;
  liveRefreshTimer = setInterval(() => {
    loadDraft();
  }, 1200);
}

async function saveDraft() {
  syncMarkdownLink(getApiBase());
  await chrome.storage.local.set({
    goal: goalEl.value,
    url: urlEl.value,
    domain: domainEl?.value || "auto",
    maxSteps: Number(maxStepsEl.value || 10),
    apiBase: getApiBase()
  });
}

async function refreshBackendConfig() {
  try {
    syncMarkdownLink();
    const config = await fetchBackendConfig();
    const keyState = config.api_key_configured && config.vision_api_key_configured ? "keys ok" : "missing key";
    setModelBadge(`${config.model || "model"} / ${config.vision_model || "vision"}`);
    setConfigStatus(
      `后端在线：${config.provider || "provider"} ${config.model || ""}，多模态：${config.vision_provider || ""} ${config.vision_model || ""}，${keyState}`,
      config.api_key_configured ? "ready" : "error"
    );
    return config;
  } catch (error) {
    syncMarkdownLink();
    setModelBadge("backend offline");
    setConfigStatus(`后端不可用：${error.message}`, "error");
    return null;
  }
}

async function runAgent() {
  const goal = goalEl.value.trim();
  const url = normalizeUrl(urlEl.value.trim() || "https://example.com");
  const domain = domainEl?.value || "auto";
  const maxSteps = Number(maxStepsEl.value || 10);
  const apiBase = getApiBase();

  if (!goal) {
    setStatus("请先填写任务目标", true);
    return;
  }

  runBtn.disabled = true;
  setStatusBadge("running");
  setStatus("正在交给浏览器控制器...");
  setResult({ ok: false, goal, report: { summary: "任务已提交，等待后端规划、浏览器执行和页面监视。" } });
  await saveDraft();

  try {
    const tab = await getActiveTab();
    const backendConfig = await fetchBackendConfig(apiBase);
    if (!backendConfig.api_key_configured) {
      throw new Error("后端模型 API key 未配置");
    }
    await chrome.runtime.sendMessage({
      type: "RUN_AGENT",
      tabId: tab.id,
      apiBase,
      payload: {
        goal,
        url: url || tab.url || "https://example.com",
        domain,
        max_steps: maxSteps,
        use_llm: true
      }
    });

    setStatus("浏览器控制已启动，页面会自动跳转");
  } catch (error) {
    setStatusBadge("error");
    setStatus(`执行失败：${error.message}`, true);
  } finally {
    runBtn.disabled = false;
  }
}

async function continueAgentFromCurrentPage() {
  const goal = goalEl.value.trim();
  const hint = agentHintEl?.value.trim() || "";
  const domain = domainEl?.value || "auto";
  const maxSteps = Number(maxStepsEl.value || 10);
  const apiBase = getApiBase();

  if (!goal) {
    setStatus("请先填写任务目标", true);
    return;
  }
  if (!hint) {
    setStatus("请先补充一句继续提示", true);
    return;
  }

  continueBtn.disabled = true;
  setStatusBadge("running");
  setStatus("正在根据你的提示继续执行...");
  await saveDraft();

  try {
    const tab = await getActiveTab();
    const resumedGoal = `${goal}\n\n继续提示：${hint}`;
    const existing = await chrome.storage.local.get(["agentTimeline"]);
    const priorTimeline = Array.isArray(existing.agentTimeline) ? existing.agentTimeline : [];
    await chrome.storage.local.set({
      agentTimeline: [
        ...priorTimeline,
        { ts: new Date().toISOString(), level: "info", text: `用户追加提示：${hint}` }
      ].slice(-40)
    });
    const backendConfig = await fetchBackendConfig(apiBase);
    if (!backendConfig.api_key_configured) {
      throw new Error("后端模型 API key 未配置");
    }
    await chrome.runtime.sendMessage({
      type: "RUN_AGENT",
      tabId: tab.id,
      apiBase,
      payload: {
        goal: resumedGoal,
        url: tab.url || normalizeUrl(urlEl.value.trim() || "https://example.com"),
        domain,
        max_steps: maxSteps,
        use_llm: true,
        resume_from_current_tab: true
      }
    });
    setStatus("已把继续提示交给 Agent，正在从当前页面恢复执行");
  } catch (error) {
    setStatusBadge("error");
    setStatus(`继续执行失败：${error.message}`, true);
  } finally {
    continueBtn.disabled = false;
  }
}

if (hasDocument) {
  runBtn.addEventListener("click", runAgent);
  if (continueBtn) {
    continueBtn.addEventListener("click", continueAgentFromCurrentPage);
  }
  if (apiBaseEl) {
    apiBaseEl.addEventListener("change", () => {
      saveDraft();
      refreshBackendConfig();
    });
  }
  quickChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      if (goalEl && chip.dataset.goal) goalEl.value = chip.dataset.goal;
      if (urlEl && chip.dataset.url) urlEl.value = chip.dataset.url;
      setStatus("已填入快捷任务，可直接运行。");
      setStatusBadge("idle");
    });
  });
  document.addEventListener("DOMContentLoaded", async () => {
    await loadDraft();
    startLiveRefresh();
    try {
      const tab = await getActiveTab();
      if (urlEl && (!urlEl.value || urlEl.value === "https://example.com") && tab?.url && /^https?:\/\//i.test(tab.url)) {
        urlEl.value = tab.url;
      }
    } catch (_error) {
      // The popup can still run with a manually supplied URL.
    }
    await refreshBackendConfig();
  });
}

if (typeof module !== "undefined") {
  module.exports = {
    escapeHtml,
    fetchBackendConfig,
    linkTo,
    normalizeApiBase,
    normalizeUrl,
    renderAgentResult,
    renderTimeline,
    renderMonitor,
    scoreBadge,
    truncate,
  };
}
