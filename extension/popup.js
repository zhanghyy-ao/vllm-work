let currentPlan = null;
let currentObservation = null;

const taskInput = document.getElementById("task");
const planBtn = document.getElementById("planBtn");
const runBtn = document.getElementById("runBtn");
const planOutput = document.getElementById("planOutput");
const logOutput = document.getElementById("logOutput");
const useLlmInput = document.getElementById("useLlm");
const saveSettingsBtn = document.getElementById("saveSettings");
const backendUrlInput = document.getElementById("backendUrl");
const checkBackendBtn = document.getElementById("checkBackendBtn");
const backendStatus = document.getElementById("backendStatus");
const workflowMeta = document.getElementById("workflowMeta");
const queueTree = document.getElementById("queueTree");

loadSettings();

document.querySelectorAll("[data-example]").forEach((button) => {
  button.addEventListener("click", () => {
    taskInput.value = button.dataset.example;
    taskInput.focus();
  });
});

saveSettingsBtn.addEventListener("click", async () => {
  await chrome.storage.local.set({
    plannerSettings: readSettingsFromForm()
  });
  logOutput.textContent = "后端设置已保存。扩展现在只通过 Python Backend 请求模型。";
});

checkBackendBtn.addEventListener("click", async () => {
  await withBusy(checkBackendBtn, "检测中...", async () => {
    const status = await checkBackend(readSettingsFromForm());
    backendStatus.textContent = [
      `服务：${status.service}`,
      `后端默认来源：${status.llmDefaultSource || "python-rule"}`,
      `环境变量 LLM：${status.llmEnvConfigured ? `已启用 (${status.llmModel || "unknown"})` : "未启用"}`,
      `环境变量通道：${status.llmTransport || "unknown"}`,
      "请求路径：Chrome 插件 -> Python Backend -> 第三方模型网关",
    ].join("\n");
  });
});

planBtn.addEventListener("click", async () => {
  await withBusy(planBtn, "生成中...", async () => {
    const observation = await sendToActiveTab({ type: "COLLECT_OBSERVATION" });
    if (!observation?.ok || !observation?.observation) {
      throw new Error(observation?.error || "当前页面 observation 采集失败。");
    }
    currentObservation = observation.observation;
    const settings = readSettingsFromForm();
    backendStatus.textContent = "准备调用 Python 后端生成计划...";
    try {
      const response = await planTaskWithBackend(taskInput.value, currentObservation, settings);
      currentPlan = response;
      if (response?.source) {
        const lines = [
          `后端已响应：${response.source}`,
          `LLM 请求：${response?.llmRequested ? "是" : "否"}`,
          `LLM 可用：${response?.llmEnabled ? `是 (${response?.llmModel || "unknown"})` : "否"}`,
          `LLM 通道：${response?.llmTransport || "unknown"}`,
          `当前规划器：${response?.source === "python-llm" ? "LLM 规划" : "规则回退规划"}`,
        ];
        if (Array.isArray(response?.warnings) && response.warnings.length) {
          lines.push("告警：");
          response.warnings.slice(0, 4).forEach((item, index) => {
            lines.push(`${index + 1}. ${item}`);
          });
        }
        backendStatus.textContent = lines.join("\n");
      }
      renderWorkflow(response?.controller);
      if (!response?.plan?.actions?.length) {
        currentPlan = { plan: planTask(taskInput.value, currentObservation) };
      }
    } catch (error) {
      currentPlan = planTask(taskInput.value, currentObservation);
      currentPlan.warnings = [
        ...(currentPlan.warnings || []),
        `Python 后端不可用，已回退本地规则：${error.message || error}`
      ];
      backendStatus.textContent = String(error?.message || error);
      renderWorkflow(null);
    }
    currentPlan = currentPlan.plan || currentPlan;
    planOutput.textContent = JSON.stringify(currentPlan, null, 2);
    runBtn.disabled = !(currentPlan.actions && currentPlan.actions.length);
    logOutput.textContent = `观测到 ${currentObservation.elements.length} 个可交互元素。`;
  });
});

runBtn.addEventListener("click", async () => {
  if (!currentPlan) return;
  await withBusy(runBtn, "执行中...", async () => {
    const settings = readSettingsFromForm();
    const result = await runWithFollowUp(currentPlan, taskInput.value, 3);
    const taskMode = /推荐|对比|比较|性价比|耳机|手机|笔记本|headphone|recommend|compare/i.test(taskInput.value || "")
      ? "recommendation"
      : "general";
    if (taskMode === "recommendation" && currentObservation) {
      try {
        const rec = await requestRecommendation(taskInput.value, currentObservation, result, settings);
        result.recommendation = rec.recommendation || rec;
      } catch (error) {
        result.recommendationError = String(error?.message || error);
      }
    }
    logOutput.textContent = JSON.stringify(result, null, 2);
  });
});

async function runWithFollowUp(initialPlan, task, maxRounds) {
  let round = 1;
  let plan = initialPlan;
  let merged = null;

  while (round <= maxRounds) {
    const response = await sendToActiveTab({ type: "EXECUTE_PLAN", plan });
    const result = response?.result || {};
    merged = merged ? mergeRunResult(merged, result, round) : { round, ...result };
    const needsFollowUp = Boolean(result?.needsFollowUp);
    if (!needsFollowUp) {
      return merged;
    }
    await delay(900);
    const observation = await sendToActiveTab({ type: "COLLECT_OBSERVATION" });
    if (!observation?.ok || !observation?.observation) {
      return mergeRunResult(merged, { followUpError: observation?.error || "follow-up observation failed" }, round + 1);
    }
    currentObservation = observation.observation;
    const settings = readSettingsFromForm();
    const replanned = await planTaskWithBackend(task, currentObservation, settings);
    plan = replanned?.plan || replanned;
    if (!plan?.actions?.length) {
      return mergeRunResult(merged, { followUpError: "follow-up replan has no actions" }, round + 1);
    }
    round += 1;
  }
  return mergeRunResult(merged || {}, { followUpError: `exceeded maxRounds=${maxRounds}` }, maxRounds + 1);
}

function mergeRunResult(base, current, round) {
  const logs = []
    .concat(Array.isArray(base?.logs) ? base.logs : [])
    .concat(Array.isArray(current?.logs) ? current.logs : []);
  return {
    ...base,
    ...current,
    round,
    logs,
    followUp: true
  };
}

async function sendToActiveTab(message) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    throw new Error("没有找到当前标签页。");
  }
  if (isRestrictedTabUrl(tab.url || "")) {
    throw new Error("当前页面是浏览器受限页面（如 chrome://、扩展页或新标签页），插件不能直接注入。请先打开一个普通网页再执行。");
  }

  try {
    return await chrome.tabs.sendMessage(tab.id, message);
  } catch (_error) {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"]
    });
    return chrome.tabs.sendMessage(tab.id, message);
  }
}

function isRestrictedTabUrl(url) {
  const value = String(url || "").toLowerCase();
  return (
    value.startsWith("chrome://") ||
    value.startsWith("chrome-extension://") ||
    value.startsWith("edge://") ||
    value.startsWith("about:") ||
    value === "data:" ||
    value.startsWith("devtools://")
  );
}

async function loadSettings() {
  const { plannerSettings } = await chrome.storage.local.get("plannerSettings");
  const settings = plannerSettings || {};
  useLlmInput.checked = settings.useLlm !== undefined ? Boolean(settings.useLlm) : true;
  backendUrlInput.value = settings.backendUrl || "http://127.0.0.1:8787";
}

function readSettingsFromForm() {
  return {
    useLlm: useLlmInput.checked,
    backendUrl: backendUrlInput.value.trim() || "http://127.0.0.1:8787"
  };
}

async function withBusy(button, label, callback) {
  const original = button.textContent;
  button.disabled = true;
  button.textContent = label;
  try {
    await callback();
  } catch (error) {
    logOutput.textContent = String(error?.message || error);
  } finally {
    button.textContent = original;
    button.disabled = false;
    runBtn.disabled = !currentPlan?.actions?.length;
  }
}

async function checkBackend(settings) {
  const response = await fetch(`${stripTrailingSlash(settings.backendUrl)}/api/extension/health`);
  if (!response.ok) {
    throw new Error(`后端检测失败：${response.status}`);
  }
  return response.json();
}

async function planTaskWithBackend(command, observation, settings) {
  const response = await fetch(`${stripTrailingSlash(settings.backendUrl)}/api/extension/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      task: command,
      observation,
      settings: {
        useLlm: Boolean(settings.useLlm)
      }
    })
  });
  if (!response.ok) {
    let payload = null;
    try {
      payload = await response.json();
    } catch (_error) {
      payload = null;
    }
    if (payload && typeof payload === "object") {
      const head = `后端计划失败：${response.status}`;
      const details = [
        payload.taskMode ? `任务模式：${payload.taskMode}` : "",
        payload.llmRequired ? "LLM 要求：必须参与" : "",
        payload.llmStatus ? `LLM 状态：${payload.llmStatus}` : "",
        payload.failureCode ? `失败码：${payload.failureCode}` : "",
        Array.isArray(payload.warnings) && payload.warnings.length ? `告警：${payload.warnings[0]}` : "",
      ].filter(Boolean);
      throw new Error([head, ...details].join(" | "));
    }
    const text = await response.text();
    throw new Error(`后端计划失败：${response.status} ${text}`);
  }
  return response.json();
}

async function requestRecommendation(task, observation, execution, settings) {
  const response = await fetch(`${stripTrailingSlash(settings.backendUrl)}/api/extension/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      task,
      observation,
      execution,
      settings: {
        useLlm: Boolean(settings.useLlm)
      }
    })
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const msg = payload?.message || payload?.error || `recommend failed ${response.status}`;
    throw new Error(msg);
  }
  return payload;
}

function stripTrailingSlash(value) {
  return String(value || "").replace(/\/+$/, "");
}

function renderWorkflow(controller) {
  if (!controller) {
    workflowMeta.textContent = "未收到工作流控制器，当前仅显示动作计划。";
    queueTree.innerHTML = "";
    return;
  }
  const activeWorkers = Array.isArray(controller.workerAssignments)
    ? controller.workerAssignments.filter((item) => ["pending", "active", "running"].includes(String(item.status || ""))).length
    : 0;
  workflowMeta.textContent = `来源：${controller.plannerSource || "unknown"} | 当前阶段：${controller.currentPhase || "-"} | 活跃 worker：${activeWorkers} | 思考：${controller.phaseReasoning || "无"}`;
  const branchesByParent = new Map();
  for (const branch of controller.parallelBranches || []) {
    const parentId = branch.parentTaskId || branch.parent_task_id || "";
    if (!branchesByParent.has(parentId)) branchesByParent.set(parentId, []);
    branchesByParent.get(parentId).push(branch);
  }
  queueTree.innerHTML = "";
  for (const task of controller.taskQueue || []) {
    const taskNode = document.createElement("div");
    taskNode.className = `queue-task ${String(task.status || "")}`;
    if ((controller.activeTask && controller.activeTask.taskId === task.taskId) || task.status === "active") {
      taskNode.classList.add("active");
    }
    taskNode.innerHTML = `
      <div class="queue-title">${escapeHtml(task.title || task.phase || "任务")}</div>
      <div class="queue-sub">阶段：${escapeHtml(task.phase || "-")} | 状态：${escapeHtml(task.status || "-")}</div>
      <div class="queue-sub">${escapeHtml(task.goal || "")}</div>
    `;
    const branches = branchesByParent.get(task.taskId) || [];
    if (branches.length) {
      const children = document.createElement("div");
      children.className = "queue-children";
      branches.forEach((branch) => {
        const branchNode = document.createElement("div");
        branchNode.className = `queue-branch ${escapeHtml(branch.status || "")}`;
        branchNode.innerHTML = `
          <div class="queue-title">${escapeHtml(branch.title || branch.taskId || "分支任务")}</div>
          <div class="queue-sub">worker：${escapeHtml(branch.workerId || "-")} | 模式：${escapeHtml(branch.executionMode || "parallel")}</div>
          <div class="queue-sub">${escapeHtml(branch.targetUrl || branch.goal || "")}</div>
        `;
        children.appendChild(branchNode);
      });
      taskNode.appendChild(children);
    }
    queueTree.appendChild(taskNode);
  }
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function delay(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}
