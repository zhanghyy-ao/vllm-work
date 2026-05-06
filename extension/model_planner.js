const SAFE_ACTION_TYPES = new Set([
  "highlight",
  "click",
  "type",
  "press",
  "scroll",
  "navigate",
  "extract",
  "summarize",
  "collect",
  "compare",
  "brief",
  "find",
  "copy",
  "wait"
]);

async function planTaskWithModel(command, observation, settings) {
  if (!settings?.useLlm) {
    return null;
  }
  if (!settings.apiKey || !settings.modelName) {
    throw new Error("LLM Planner 已开启，但缺少 API Key 或 Model。");
  }

  const apiBase = (settings.apiBase || "https://api.openai.com/v1").replace(/\/$/, "");
  const response = await fetch(`${apiBase}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${settings.apiKey}`
    },
    body: JSON.stringify({
      model: settings.modelName,
      temperature: 0.1,
      messages: [
        {
          role: "system",
          content: [
            "你是一个安全的浏览器辅助操作 Planner。",
            "你只能输出 JSON，不要输出 Markdown。",
            "输出格式必须是 {summary, confidence, warnings, actions}。",
            "actions 只能使用允许动作：highlight, click, type, press, scroll, navigate, extract, summarize, collect, compare, brief, find, copy, wait。",
            "targetId 必须来自 observation.elements。",
            "禁止生成最终发送、提交、付款、删除、发布、上传等高风险动作；遇到这些动作只允许 highlight 按钮并写 warning。",
            "优先生成短计划，每步必须包含 reason。"
          ].join("\n")
        },
        {
          role: "user",
          content: JSON.stringify({
            task: command,
            observation: compactObservation(observation)
          }, null, 2)
        }
      ]
    })
  });

  if (!response.ok) {
    throw new Error(`LLM Planner 请求失败：${response.status}`);
  }

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content || "";
  return sanitizeModelPlan(parseJsonPlan(content));
}

function compactObservation(observation) {
  return {
    url: observation.url,
    title: observation.title,
    text: (observation.text || "").slice(0, 2200),
    elements: (observation.elements || []).slice(0, 80).map((element) => ({
      id: element.id,
      tag: element.tag,
      role: element.role,
      type: element.type,
      label: element.label,
      text: element.text,
      placeholder: element.placeholder,
      name: element.name
    }))
  };
}

function parseJsonPlan(content) {
  const trimmed = content.trim()
    .replace(/^```json\s*/i, "")
    .replace(/^```\s*/i, "")
    .replace(/```$/i, "")
    .trim();
  const jsonStart = trimmed.indexOf("{");
  const jsonEnd = trimmed.lastIndexOf("}");
  if (jsonStart < 0 || jsonEnd < jsonStart) {
    throw new Error("LLM Planner 没有返回 JSON。");
  }
  return JSON.parse(trimmed.slice(jsonStart, jsonEnd + 1));
}

function sanitizeModelPlan(plan) {
  const actions = Array.isArray(plan.actions) ? plan.actions : [];
  return {
    summary: String(plan.summary || "LLM 生成计划"),
    confidence: Number(plan.confidence || 0.5),
    warnings: Array.isArray(plan.warnings) ? plan.warnings.map(String) : [],
    actions: actions
      .filter((action) => SAFE_ACTION_TYPES.has(action.type))
      .slice(0, 8)
      .map((action) => ({
        type: action.type,
        targetId: action.targetId,
        value: action.value,
        key: action.key,
        reason: String(action.reason || "LLM Planner 生成。")
      }))
  };
}
