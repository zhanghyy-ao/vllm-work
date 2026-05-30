const API_BASE = "http://127.0.0.1:8000";

const hasDocument = typeof document !== "undefined";
const goalEl = hasDocument ? document.getElementById("goal") : null;
const urlEl = hasDocument ? document.getElementById("url") : null;
const maxStepsEl = hasDocument ? document.getElementById("maxSteps") : null;
const runBtn = hasDocument ? document.getElementById("runBtn") : null;
const statusEl = hasDocument ? document.getElementById("status") : null;
const resultEl = hasDocument ? document.getElementById("result") : null;
const statusBadgeEl = hasDocument ? document.getElementById("statusBadge") : null;
const quickChips = hasDocument ? Array.from(document.querySelectorAll(".quick-chip")) : [];

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

function renderAgentResult(result, monitorMessage = "", observations = []) {
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
  const reasoning = card(
    "可见规划",
    listItems(report.reasoning_outline, (item) => escapeHtml(item), 4) +
      listItems(report.search_plan, (item) => `${escapeHtml(item.purpose || "检索")}：${escapeHtml(item.query || "")}`, 4)
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
  const uncertainties = card("不确定性/下一步", [
    listItems(report.uncertainties, (item) => escapeHtml(item), 3),
    listItems(report.next_actions, (item) => escapeHtml(item), 3),
  ].join(""));
  return [summary, reasoning, recommendations, matrix, video, multimodal, monitor, uncertainties].filter(Boolean).join("");
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

function setResult(result, monitorMessage = "", observations = []) {
  if (!resultEl) return;
  resultEl.innerHTML = renderAgentResult(result, monitorMessage, observations);
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
    "maxSteps",
    "agentStatus",
    "agentError",
    "lastResult",
    "finalUrl",
    "monitorMessage",
    "monitorObservations"
  ]);
  if (data.goal) goalEl.value = data.goal;
  if (data.url) urlEl.value = data.url;
  if (data.maxSteps) maxStepsEl.value = String(data.maxSteps);

  if (data.agentStatus === "running") {
    setStatusBadge("running");
    setStatus("正在执行 Agent...");
  } else if (data.agentStatus === "monitoring") {
    setStatusBadge("monitoring");
    setResult(data.lastResult || null, data.monitorMessage || "正在监视页面是否满足任务要求", data.monitorObservations || []);
    setStatus("监视中...");
  } else if (data.agentStatus === "done") {
    setStatusBadge("done");
    setResult(data.lastResult || {}, data.monitorMessage || "", data.monitorObservations || []);
    setStatus(data.finalUrl ? `执行完成，已控制浏览器打开：${data.finalUrl}` : "执行完成");
  } else if (data.agentStatus === "needs_review") {
    setStatusBadge("needs_review");
    setResult(data.lastResult || {}, data.monitorMessage || "监视后仍未确认满足任务要求", data.monitorObservations || []);
    setStatus("需要复核：页面可能仍未满足任务要求", true);
  } else if (data.agentStatus === "error") {
    setStatusBadge("error");
    setStatus(`执行失败：${data.agentError || "未知错误"}`, true);
  } else {
    setStatusBadge("idle");
  }
}

async function saveDraft() {
  await chrome.storage.local.set({
    goal: goalEl.value,
    url: urlEl.value,
    maxSteps: Number(maxStepsEl.value || 10)
  });
}

async function runAgent() {
  const goal = goalEl.value.trim();
  const url = normalizeUrl(urlEl.value.trim() || "https://example.com");
  const maxSteps = Number(maxStepsEl.value || 10);

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
    await chrome.runtime.sendMessage({
      type: "RUN_AGENT",
      tabId: tab.id,
      payload: {
        goal,
        url,
        domain: "auto",
        max_steps: maxSteps,
        use_llm: true,
        provider: "deepseek",
        model: "deepseek-chat",
        api_key_env: "DEEPSEEK_API_KEY",
        api_base_url: "https://api.deepseek.com",
        vision_provider: "gemini",
        vision_model: "gemini-1.5-flash",
        vision_api_key_env: "GEMINI_API_KEY"
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

if (hasDocument) {
  runBtn.addEventListener("click", runAgent);
  quickChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      if (goalEl && chip.dataset.goal) goalEl.value = chip.dataset.goal;
      if (urlEl && chip.dataset.url) urlEl.value = chip.dataset.url;
      setStatus("已填入快捷任务，可直接运行。");
      setStatusBadge("idle");
    });
  });
  document.addEventListener("DOMContentLoaded", loadDraft);
}

if (typeof module !== "undefined") {
  module.exports = {
    escapeHtml,
    linkTo,
    normalizeUrl,
    renderAgentResult,
    renderMonitor,
    scoreBadge,
    truncate,
  };
}
