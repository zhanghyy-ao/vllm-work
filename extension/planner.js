const DEFAULT_SEARCH_URL = "https://www.bing.com/search?q=";

function planTask(command, observation) {
  const text = (command || "").trim();
  const elements = observation.elements || [];

  if (!text) {
    return makePlan("请输入任务指令。", 0, []);
  }

  if (isReplyTask(text)) {
    return planReply(text, elements);
  }

  if (isGithubBriefTask(text, observation)) {
    return planBrief("github", "分析当前 GitHub 仓库，提取用途、运行线索和工程风险。");
  }

  if (isUiAnalysisTask(text)) {
    return planBrief("ui", "分析当前界面结构、可用控件、主要工作流和风险按钮。");
  }

  if (isProjectAnalysisTask(text)) {
    return planBrief("project", "分析当前项目或页面的目标、模块、可复用性和下一步行动。");
  }

  if (isResearchTask(text)) {
    return planBrief("research", "整理当前页面或搜索结果，形成研究简报。");
  }

  if (isDocsTask(text, observation)) {
    return planDocsBrief(text);
  }

  if (isFindTask(text)) {
    return planFind(text);
  }

  if (isSummarizeTask(text)) {
    return planSummarize(text);
  }

  if (isCollectTask(text)) {
    return planCollect(text);
  }

  if (isCompareTask(text)) {
    return planCompare(text, observation);
  }

  if (isFormTask(text)) {
    return planFormFill(text, elements);
  }

  if (isSearchTask(text)) {
    return planSearch(text, observation, elements);
  }

  return planClickOrExtract(text, observation, elements);
}

function makePlan(summary, confidence, actions, warnings = []) {
  return {
    summary,
    confidence,
    warnings,
    actions
  };
}

function isSearchTask(text) {
  return /搜索|查找|寻找|找到|检索|主题|资料|论文|search/i.test(text);
}

function isFormTask(text) {
  return /填写|填表|表单|姓名=|邮箱=|电话=|主题=|备注=|name=|email=/i.test(text);
}

function isReplyTask(text) {
  return /回复|回信|回消息|发送草稿|reply/i.test(text);
}

function isResearchTask(text) {
  return /研究|调研|资料|搜索结果|找资料|找.*内容|research|survey/i.test(text);
}

function isGithubBriefTask(text, observation) {
  return /github|repo|仓库|代码库|README|开源项目/i.test(text)
    || /github\.com/i.test(observation.url || "");
}

function isUiAnalysisTask(text) {
  return /分析.*界面|界面.*分析|页面结构|有哪些按钮|能做什么|UI|可用功能/i.test(text);
}

function isProjectAnalysisTask(text) {
  return /分析.*项目|项目.*分析|可复用性|工程价值|工程风险|模块划分|架构分析/i.test(text);
}

function isFindTask(text) {
  return /帮忙查找|帮我查找|页面中找|在.*中找|定位|find on page/i.test(text);
}

function isDocsTask(text, observation) {
  return /文档|教程|安装|配置|API|接口|docs|documentation/i.test(text)
    || /docs|documentation|readme/i.test(`${observation.url || ""} ${observation.title || ""}`);
}

function isSummarizeTask(text) {
  return /总结|摘要|概括|提炼|要点|summari[sz]e/i.test(text);
}

function isCollectTask(text) {
  return /提取|抽取|收集|导出|抓取|链接|邮箱|价格|数据|结构化|collect|extract/i.test(text);
}

function isCompareTask(text) {
  return /比较|对比|排序|哪个更好|哪个更适合|推荐|compare|rank/i.test(text);
}

function planSearch(command, observation, elements) {
  const query = cleanSearchQuery(command);
  const searchInput = bestElement(elements, ["search", "搜索", "查找", "query", "关键词"], isTextInput);
  const submit = bestElement(elements, ["搜索", "查找", "提交", "search"], isClickable);

  if (searchInput) {
    const actions = [
      {
        type: "type",
        targetId: searchInput.id,
        value: query,
        reason: `找到搜索输入框：“${searchInput.label || searchInput.placeholder || searchInput.tag}”。`
      }
    ];

    if (submit) {
      actions.push({
        type: "click",
        targetId: submit.id,
        reason: `点击搜索按钮：“${submit.label || submit.text || submit.tag}”。`
      });
    } else {
      actions.push({
        type: "press",
        targetId: searchInput.id,
        key: "Enter",
        reason: "页面没有明显搜索按钮，使用 Enter 提交。"
      });
    }

    actions.push({
      type: "extract",
      value: query,
      reason: "提交后提取页面中与主题相关的内容。"
    });

    return makePlan(`在当前页面搜索“${query}”。`, 0.82, actions);
  }

  return makePlan(`当前页面没有搜索框，跳转到搜索引擎搜索“${query}”。`, 0.68, [
    {
      type: "navigate",
      value: DEFAULT_SEARCH_URL + encodeURIComponent(query),
      reason: "未发现页面内搜索框，使用默认搜索引擎。"
    }
  ]);
}

function planFormFill(command, elements) {
  const fields = parseFields(command);
  const actions = [];
  const misses = [];

  for (const [key, value] of Object.entries(fields)) {
    const target = bestElement(elements, [key], isTextInput);
    if (!target) {
      misses.push(key);
      continue;
    }
    actions.push({
      type: "type",
      targetId: target.id,
      value,
      reason: `字段“${key}”匹配到“${target.label || target.placeholder || target.name || target.id}”。`
    });
  }

  const submit = bestElement(elements, ["提交", "保存", "发送", "submit"], isClickable);
  if (submit) {
    actions.push({
      type: "highlight",
      targetId: submit.id,
      reason: "表单提交属于高风险动作，先高亮按钮，等待用户确认。"
    });
  }

  return makePlan(
    `填写 ${actions.filter((a) => a.type === "type").length} 个字段。`,
    actions.length ? 0.78 : 0.2,
    actions,
    misses.length ? [`未匹配字段：${misses.join("、")}`] : []
  );
}

function planReply(command, elements) {
  const value = cleanReplyText(command);
  const input = bestElement(elements, ["消息", "回复", "评论", "输入", "reply", "message"], isTextInput)
    || elements.find((el) => el.contentEditable);
  const send = bestElement(elements, ["发送", "回复", "send", "提交"], isClickable);

  const actions = [];
  if (input) {
    actions.push({
      type: "type",
      targetId: input.id,
      value,
      reason: `找到消息输入区域：“${input.label || input.placeholder || input.tag}”。`
    });
  }
  if (send) {
    actions.push({
      type: "highlight",
      targetId: send.id,
      reason: "发送消息属于高风险动作，Demo 只填入草稿并高亮发送按钮。"
    });
  }

  return makePlan("生成回复草稿，不自动发送。", actions.length ? 0.76 : 0.25, actions);
}

function planSummarize(command) {
  return makePlan("总结当前页面可见内容。", 0.7, [
    {
      type: "summarize",
      value: command,
      reason: "用户希望获得页面摘要，直接基于当前页面可见文本生成要点。"
    },
    {
      type: "copy",
      reason: "将摘要复制到剪贴板，便于粘贴到报告或消息中。"
    }
  ]);
}

function planBrief(kind, summary) {
  return makePlan(summary, 0.74, [
    {
      type: "brief",
      value: kind,
      reason: `当前任务适合使用 ${kind} 真实场景简报。`
    },
    {
      type: "copy",
      reason: "将简报复制到剪贴板。"
    }
  ]);
}

function planDocsBrief(command) {
  return makePlan("在当前文档页中定位相关内容并生成摘要。", 0.73, [
    {
      type: "extract",
      value: command,
      reason: "先提取与用户问题相关的文档片段。"
    },
    {
      type: "brief",
      value: "docs",
      reason: "再按文档站格式整理安装、配置或 API 线索。"
    },
    {
      type: "copy",
      reason: "将文档摘要复制到剪贴板。"
    }
  ]);
}

function planFind(command) {
  const query = cleanFindQuery(command);
  return makePlan(`在当前页面查找“${query}”。`, 0.7, [
    {
      type: "find",
      value: query,
      reason: "用户希望在当前页面定位相关内容。"
    },
    {
      type: "copy",
      reason: "将查找结果复制到剪贴板。"
    }
  ]);
}

function planCollect(command) {
  const target = detectCollectTarget(command);
  return makePlan(`结构化抽取页面中的${target.label}。`, 0.72, [
    {
      type: "collect",
      value: target.kind,
      reason: `用户指令指向“${target.label}”抽取。`
    },
    {
      type: "copy",
      reason: "将抽取结果复制到剪贴板。"
    }
  ]);
}

function planCompare(command, observation) {
  const focus = cleanCompareFocus(command);
  const hasEnoughCards = (observation?.cards || []).length >= 3;
  const elements = observation?.elements || [];
  const searchInput = bestElement(elements, ["search", "搜索", "查找", "query", "关键词", "耳机"], isTextInput);
  const searchSubmit = bestElement(elements, ["搜索", "查找", "search"], isClickable);

  if (!hasEnoughCards) {
    if (searchInput) {
      const actions = [
        {
          type: "type",
          targetId: searchInput.id,
          value: focus || command,
          reason: `候选不足，先在页面内搜索“${focus || command}”。`
        }
      ];
      if (searchSubmit) {
        actions.push({
          type: "click",
          targetId: searchSubmit.id,
          reason: "点击页面内搜索按钮。"
        });
      } else {
        actions.push({
          type: "press",
          targetId: searchInput.id,
          key: "Enter",
          reason: "未识别到搜索按钮，使用 Enter 提交。"
        });
      }
      actions.push(
        {
          type: "collect",
          value: "cards",
          reason: "收集搜索结果中的商品候选卡片。"
        },
        {
          type: "compare",
          value: command,
          reason: "对候选进行比较并给出推荐。"
        },
        {
          type: "copy",
          reason: "将比较结果复制到剪贴板。"
        }
      );
      return makePlan("当前页候选不足，已切换为页面内搜索+比较流程。", 0.82, actions);
    }
    return makePlan("当前页面候选不足，先搜索再比较。", 0.76, [
      {
        type: "navigate",
        value: `${DEFAULT_SEARCH_URL}${encodeURIComponent(focus || command)}`,
        reason: `先搜索“${focus || command}”，收集真实候选。`
      },
      {
        type: "collect",
        value: "cards",
        reason: "收集搜索结果中的商品候选卡片。"
      },
      {
        type: "compare",
        value: command,
        reason: "对候选进行比较并给出推荐。"
      },
      {
        type: "copy",
        reason: "将比较结果复制到剪贴板。"
      }
    ]);
  }
  return makePlan("比较页面中的结果卡片并给出简短推荐。", 0.7, [
    {
      type: "collect",
      value: "cards",
      reason: "先刷新候选卡片，避免用到旧页面缓存。"
    },
    {
      type: "compare",
      value: command,
      reason: "用户希望对页面候选项进行比较和排序。"
    },
    {
      type: "copy",
      reason: "将比较结果复制到剪贴板。"
    }
  ]);
}

function cleanCompareFocus(command) {
  return command
    .replace(/帮我|请|比较|对比|排序|哪个更好|哪个更适合|推荐|这些|方案|产品|工具|compare|rank/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function planClickOrExtract(command, observation, elements) {
  const clickText = command.replace(/点击|打开|进入/g, "").trim();
  const target = bestElement(elements, [clickText], isClickable);
  if (target) {
    return makePlan(`点击“${clickText}”。`, 0.65, [
      {
        type: "click",
        targetId: target.id,
        reason: `找到文本或标签最接近的可点击元素：“${target.label || target.text || target.id}”。`
      }
    ]);
  }

  return makePlan("未识别到明确操作，先提取页面相关内容。", 0.45, [
    {
      type: "extract",
      value: command,
      reason: "作为保底策略，从页面文本中提取相关片段。"
    }
  ]);
}

function detectCollectTarget(command) {
  if (/链接|网址|url|link/i.test(command) && /邮箱|邮件|email/i.test(command)) {
    return { kind: "contacts", label: "链接和邮箱" };
  }
  if (/邮箱|邮件|email/i.test(command)) return { kind: "emails", label: "邮箱" };
  if (/价格|价钱|金额|price/i.test(command)) return { kind: "prices", label: "价格" };
  if (/链接|网址|url|link/i.test(command)) return { kind: "links", label: "链接" };
  if (/表格|table/i.test(command)) return { kind: "tables", label: "表格" };
  return { kind: "cards", label: "结果卡片" };
}

function cleanSearchQuery(command) {
  return command
    .replace(/帮我|请|搜索|查找|寻找|找到|检索|相关主题的内容|相关内容|主题|资料|论文|search/gi, " ")
    .replace(/[：:]/g, " ")
    .replace(/\s+/g, " ")
    .trim() || command.trim();
}

function cleanReplyText(command) {
  const parts = command.split(/[：:]/);
  if (parts.length > 1) {
    return parts.slice(1).join(":").trim();
  }
  return command.replace(/回复|回信|回消息|发送草稿|reply/gi, "").trim();
}

function cleanFindQuery(command) {
  return command
    .replace(/帮忙查找|帮我查找|页面中找|在.*中找|定位|find on page/gi, " ")
    .replace(/[：:]/g, " ")
    .replace(/\s+/g, " ")
    .trim() || command.trim();
}

function parseFields(command) {
  const fields = {};
  const normalized = command
    .replace(/请|帮我|填写|填表|表单/g, " ")
    .replace(/，/g, " ")
    .replace(/；/g, " ");
  const pairPattern = /([\u4e00-\u9fa5A-Za-z_ -]{1,12})\s*=\s*([^=\s]+(?:\s(?![\u4e00-\u9fa5A-Za-z_ -]{1,12}\s*=)[^=\s]+)*)/g;
  let match;
  while ((match = pairPattern.exec(normalized)) !== null) {
    fields[match[1].trim()] = match[2].trim();
  }

  if (Object.keys(fields).length) {
    return fields;
  }

  const presets = [
    ["姓名", /姓名[:： ]+([^\s，,]+)/],
    ["邮箱", /邮箱[:： ]+([^\s，,]+)/],
    ["电话", /电话[:： ]+([^\s，,]+)/],
    ["主题", /主题[:： ]+([^\s，,]+)/],
    ["备注", /备注[:： ]+(.+)$/]
  ];

  for (const [key, pattern] of presets) {
    const found = command.match(pattern);
    if (found) {
      fields[key] = found[1].trim();
    }
  }
  return fields;
}

function bestElement(elements, keywords, predicate) {
  const scored = elements
    .filter(predicate)
    .map((el) => ({ el, score: scoreElement(el, keywords) }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score);
  return scored[0]?.el || null;
}

function scoreElement(element, keywords) {
  const haystack = [
    element.label,
    element.text,
    element.placeholder,
    element.name,
    element.role,
    element.type,
    element.id
  ].filter(Boolean).join(" ").toLowerCase();

  return keywords.reduce((score, keyword) => {
    const key = String(keyword || "").toLowerCase();
    if (!key) return score;
    if (haystack.includes(key)) return score + 10;
    return score + fuzzyScore(haystack, key);
  }, 0);
}

function fuzzyScore(haystack, keyword) {
  let score = 0;
  for (const char of keyword) {
    if (haystack.includes(char.toLowerCase())) {
      score += 1;
    }
  }
  return score >= Math.min(2, keyword.length) ? score : 0;
}

function isTextInput(element) {
  return ["input", "textarea"].includes(element.tag)
    || element.contentEditable
    || /textbox|searchbox|combobox/.test(element.role || "");
}

function isClickable(element) {
  return ["button", "a", "select"].includes(element.tag)
    || /button|link|menuitem|option/.test(element.role || "")
    || element.clickable;
}
