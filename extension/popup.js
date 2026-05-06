let currentPlan = null;
let currentObservation = null;

const taskInput = document.getElementById("task");
const planBtn = document.getElementById("planBtn");
const runBtn = document.getElementById("runBtn");
const planOutput = document.getElementById("planOutput");
const logOutput = document.getElementById("logOutput");
const useLlmInput = document.getElementById("useLlm");
const apiBaseInput = document.getElementById("apiBase");
const apiKeyInput = document.getElementById("apiKey");
const modelNameInput = document.getElementById("modelName");
const saveSettingsBtn = document.getElementById("saveSettings");

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
  logOutput.textContent = "LLM Planner 设置已保存。";
});

planBtn.addEventListener("click", async () => {
  await withBusy(planBtn, "生成中...", async () => {
    const observation = await sendToActiveTab({ type: "COLLECT_OBSERVATION" });
    currentObservation = observation.observation;
    const settings = readSettingsFromForm();
    try {
      currentPlan = await planTaskWithModel(taskInput.value, currentObservation, settings);
      if (!currentPlan) {
        currentPlan = planTask(taskInput.value, currentObservation);
      }
    } catch (error) {
      currentPlan = planTask(taskInput.value, currentObservation);
      currentPlan.warnings = [
        ...(currentPlan.warnings || []),
        `LLM Planner 失败，已回退本地规则：${error.message || error}`
      ];
    }
    planOutput.textContent = JSON.stringify(currentPlan, null, 2);
    runBtn.disabled = !(currentPlan.actions && currentPlan.actions.length);
    logOutput.textContent = `观测到 ${currentObservation.elements.length} 个可交互元素。`;
  });
});

runBtn.addEventListener("click", async () => {
  if (!currentPlan) return;
  await withBusy(runBtn, "执行中...", async () => {
    const response = await sendToActiveTab({ type: "EXECUTE_PLAN", plan: currentPlan });
    logOutput.textContent = JSON.stringify(response.result, null, 2);
  });
});

async function sendToActiveTab(message) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    throw new Error("没有找到当前标签页。");
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

async function loadSettings() {
  const { plannerSettings } = await chrome.storage.local.get("plannerSettings");
  const settings = plannerSettings || {};
  useLlmInput.checked = Boolean(settings.useLlm);
  apiBaseInput.value = settings.apiBase || "https://api.openai.com/v1";
  apiKeyInput.value = settings.apiKey || "";
  modelNameInput.value = settings.modelName || "";
}

function readSettingsFromForm() {
  return {
    useLlm: useLlmInput.checked,
    apiBase: apiBaseInput.value.trim() || "https://api.openai.com/v1",
    apiKey: apiKeyInput.value.trim(),
    modelName: modelNameInput.value.trim()
  };
}

async function withBusy(button, label, callback) {
  const original = button.textContent;
  button.disabled = true;
  button.textContent = label;
  try {
    await callback();
  } catch (error) {
    logOutput.textContent = String(error);
  } finally {
    button.textContent = original;
    button.disabled = false;
    runBtn.disabled = !currentPlan?.actions?.length;
  }
}
