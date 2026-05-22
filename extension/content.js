const AGENT_ATTR = "data-browser-agent-id";
const HIGHLIGHT_CLASS = "browser-agent-highlight";
let lastAgentArtifact = "";

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "COLLECT_OBSERVATION") {
    try {
      sendResponse({ ok: true, observation: collectObservation() });
    } catch (error) {
      sendResponse({ ok: false, error: String(error) });
    }
    return true;
  }

  if (message?.type === "EXECUTE_PLAN") {
    executePlan(message.plan)
      .then((result) => sendResponse({ ok: true, result }))
      .catch((error) => sendResponse({ ok: false, error: String(error) }));
    return true;
  }

  return false;
});

function collectObservation() {
  ensureStyles();
  const elements = collectInteractiveElements();
  return {
    url: location.href,
    title: document.title,
    text: visibleText(document.body).slice(0, 5000),
    elements,
    headings: Array.from(document.querySelectorAll("h1, h2, h3"))
      .filter(isVisible)
      .map((node) => visibleText(node))
      .filter(Boolean)
      .slice(0, 20),
    links: collectStructuredData("links").items.slice(0, 40),
    cards: collectCards().slice(0, 20),
    tables: collectTables().slice(0, 4),
    emails: Array.from(new Set((visibleText(document.body).match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi) || []))).slice(0, 20),
    prices: Array.from(new Set((visibleText(document.body).match(/(?:¥|\$|￥)\s?\d+(?:\.\d{1,2})?/g) || []))).slice(0, 20)
  };
}

function collectInteractiveElements() {
  const selector = [
    "a[href]",
    "button",
    "input",
    "textarea",
    "select",
    "[role='button']",
    "[role='link']",
    "[role='textbox']",
    "[contenteditable='true']",
    "[onclick]",
    "[aria-label]"
  ].join(",");

  return Array.from(document.querySelectorAll(selector))
    .filter(isVisible)
    .slice(0, 160)
    .map((element, index) => {
      const id = `e${index + 1}`;
      element.setAttribute(AGENT_ATTR, id);
      const rect = element.getBoundingClientRect();
      return {
        id,
        tag: element.tagName.toLowerCase(),
        selector: cssSelectorFor(element),
        role: element.getAttribute("role") || implicitRole(element),
        type: element.getAttribute("type") || "",
        name: element.getAttribute("name") || "",
        label: labelFor(element),
        text: visibleText(element).slice(0, 160),
        placeholder: element.getAttribute("placeholder") || "",
        href: element.href || element.getAttribute("href") || "",
        value: "value" in element ? String(element.value || "") : "",
        formId: element.closest("form")?.id || "",
        sectionLabel: sectionLabelFor(element),
        visible: true,
        enabled: !element.disabled && element.getAttribute("aria-disabled") !== "true",
        contentEditable: element.isContentEditable,
        clickable: Boolean(element.onclick || element.getAttribute("onclick")),
        bbox: {
          x: Math.round(rect.x),
          y: Math.round(rect.y),
          width: Math.round(rect.width),
          height: Math.round(rect.height)
        }
      };
    });
}

function cssSelectorFor(element) {
  if (element.id) return `#${CSS.escape(element.id)}`;
  if (element.name) return `${element.tagName.toLowerCase()}[name="${String(element.name).replace(/"/g, '\\"')}"]`;
  const aria = element.getAttribute("aria-label");
  if (aria) return `${element.tagName.toLowerCase()}[aria-label="${String(aria).replace(/"/g, '\\"')}"]`;
  const href = element.getAttribute("href");
  if (href) return `${element.tagName.toLowerCase()}[href="${String(href).replace(/"/g, '\\"')}"]`;
  return element.tagName.toLowerCase();
}

function sectionLabelFor(element) {
  const parent = element.closest("section, article, form, main");
  if (!parent) return "";
  const aria = parent.getAttribute("aria-label");
  if (aria) return aria.trim();
  const heading = parent.querySelector("h1, h2, h3");
  return heading ? visibleText(heading) : "";
}

async function executePlan(plan) {
  ensureStyles();
  const logs = [];
  let needsFollowUp = false;
  for (const action of plan.actions || []) {
    const startedAt = new Date().toISOString();
    try {
      const output = await executeAction(action);
      logs.push({ ...action, ok: true, output, timestamp: startedAt });
      if (action.type === "navigate") {
        needsFollowUp = true;
        break;
      }
    } catch (error) {
      logs.push({ ...action, ok: false, error: String(error), timestamp: startedAt });
      break;
    }
    await delay(260);
  }
  return {
    url: location.href,
    logs,
    needsFollowUp,
    finishedAt: new Date().toISOString()
  };
}

async function executeAction(action) {
  if (action.type === "navigate") {
    const targetUrl = String(action.value || "").trim();
    if (!targetUrl) return "navigated";
    window.setTimeout(() => {
      location.assign(targetUrl);
    }, 40);
    return "navigated";
  }

  if (action.type === "scroll") {
    window.scrollBy({ top: action.value || 600, behavior: "smooth" });
    return "scrolled";
  }

  if (action.type === "wait") {
    await delay(action.value || 1000);
    return "waited";
  }

  if (action.type === "extract") {
    const snippets = extractSnippets(action.value || "");
    lastAgentArtifact = snippets.join("\n\n") || "没有提取到明显相关片段。";
    showAgentToast(lastAgentArtifact);
    return snippets;
  }

  if (action.type === "summarize") {
    lastAgentArtifact = summarizePage();
    showAgentToast(lastAgentArtifact);
    return lastAgentArtifact;
  }

  if (action.type === "collect") {
    if ((action.value || "cards") === "cards") {
      await ensureCardCandidatesReady();
    }
    const artifact = collectStructuredData(action.value || "cards");
    lastAgentArtifact = JSON.stringify(artifact, null, 2);
    showAgentToast(lastAgentArtifact);
    return artifact;
  }

  if (action.type === "compare") {
    lastAgentArtifact = compareCards(action.value || "");
    showAgentToast(lastAgentArtifact);
    return lastAgentArtifact;
  }

  if (action.type === "brief") {
    lastAgentArtifact = buildBrief(action.value || "research");
    showAgentToast(lastAgentArtifact);
    return lastAgentArtifact;
  }

  if (action.type === "find") {
    lastAgentArtifact = findOnPage(action.value || "");
    showAgentToast(lastAgentArtifact);
    return lastAgentArtifact;
  }

  if (action.type === "copy") {
    await copyText(lastAgentArtifact || "暂无可复制内容。");
    return "copied";
  }

  const target = findTarget(action.targetId);
  if (!target) {
    throw new Error(`Target not found: ${action.targetId}`);
  }

  highlight(target);

  if (action.type === "highlight") {
    return "highlighted";
  }

  if (action.type === "click") {
    target.click();
    return "clicked";
  }

  if (action.type === "type") {
    setElementValue(target, action.value || "");
    return "typed";
  }

  if (action.type === "press") {
    target.focus();
    const eventInit = { key: action.key || "Enter", bubbles: true, cancelable: true };
    target.dispatchEvent(new KeyboardEvent("keydown", eventInit));
    target.dispatchEvent(new KeyboardEvent("keyup", eventInit));
    if ((action.key || "Enter") === "Enter") {
      submitNearestForm(target);
    }
    return `pressed ${action.key || "Enter"}`;
  }

  throw new Error(`Unsupported action type: ${action.type}`);
}

function findTarget(id) {
  return document.querySelector(`[${AGENT_ATTR}="${CSS.escape(id)}"]`);
}

function setElementValue(element, value) {
  element.focus();
  if (element.isContentEditable) {
    element.textContent = value;
    element.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: value }));
    return;
  }

  const tag = String(element.tagName || "").toUpperCase();
  if (tag === "INPUT") {
    const descriptor = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value");
    if (descriptor?.set) {
      descriptor.set.call(element, value);
    } else {
      element.value = value;
    }
  } else if (tag === "TEXTAREA") {
    const descriptor = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value");
    if (descriptor?.set) {
      descriptor.set.call(element, value);
    } else {
      element.value = value;
    }
  } else if (tag === "SELECT") {
    element.value = value;
  } else {
    // Fallback for custom widgets with role=textbox and similar non-standard inputs.
    element.textContent = value;
  }
  element.dispatchEvent(new Event("input", { bubbles: true }));
  element.dispatchEvent(new Event("change", { bubbles: true }));
}

function submitNearestForm(element) {
  const form = element.closest("form");
  if (form) {
    form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
  }
}

function buildBrief(kind) {
  if (kind === "github") {
    return buildGithubBrief();
  }
  if (kind === "docs") {
    return buildDocsBrief();
  }
  if (kind === "ui") {
    return buildUiBrief();
  }
  if (kind === "project") {
    return buildProjectBrief();
  }
  return buildResearchBrief();
}

function buildResearchBrief() {
  const cards = collectCards().slice(0, 6);
  const links = collectStructuredData("links").items.slice(0, 6);
  const sourceItems = cards.length
    ? cards.map((card, index) => `${index + 1}. ${card.title}\n   ${card.summary}\n   ${card.href || "当前页"}`)
    : links.map((link, index) => `${index + 1}. ${link.text}\n   ${link.href}`);

  return [
    `研究简报：${document.title}`,
    `来源：${location.href}`,
    "核心材料：",
    ...(sourceItems.length ? sourceItems : ["1. 当前页面没有明显结果卡片或链接。"]),
    "下一步建议：优先打开最相关的 2--3 个来源，提取安装方式、使用限制和可复现实验入口。"
  ].join("\n");
}

function buildGithubBrief() {
  const title = visibleText(document.querySelector("strong[itemprop='name'], h1, [data-testid='repository-container-header']")) || document.title;
  const about = visibleText(document.querySelector("[data-pjax='#repo-content-pjax-container'] [class*='BorderGrid'], [aria-label='Repository details'], aside")) || "";
  const headings = Array.from(document.querySelectorAll("article h1, article h2, article h3, #readme h1, #readme h2, #readme h3, h1, h2, h3"))
    .filter(isVisible)
    .map((node) => visibleText(node))
    .filter(Boolean)
    .slice(0, 8);
  const links = collectStructuredData("links").items
    .filter((link) => /issues|pull|releases|license|readme|docs|wiki|github/i.test(`${link.text} ${link.href}`))
    .slice(0, 8);

  return [
    `GitHub 仓库简报：${title}`,
    `来源：${location.href}`,
    about ? `项目简介：${about.slice(0, 360)}` : "项目简介：未在当前可见区域提取到 About 信息。",
    `README/页面结构：${headings.join(" / ") || "未提取到标题"}`,
    "关键链接：",
    ...(links.length ? links.map((link, index) => `${index + 1}. ${link.text} - ${link.href}`) : ["1. 当前页未提取到明显关键链接。"]),
    "工程判断：优先检查 README 的安装步骤、License、最近提交和 issue 活跃度，再决定是否作为课程 Demo 基座。"
  ].join("\n");
}

function buildDocsBrief() {
  const headings = Array.from(document.querySelectorAll("h1, h2, h3"))
    .filter(isVisible)
    .map((node) => visibleText(node))
    .filter(Boolean)
    .slice(0, 10);
  const codeBlocks = Array.from(document.querySelectorAll("pre, code"))
    .filter(isVisible)
    .map((node) => visibleText(node))
    .filter((text) => text.length > 8)
    .slice(0, 5);
  const snippets = extractSnippets("install 安装 setup 配置 API key token playwright browser");

  return [
    `文档页简报：${document.title}`,
    `来源：${location.href}`,
    `页面结构：${headings.join(" / ") || "未提取到标题"}`,
    "相关片段：",
    ...(snippets.length ? snippets : ["1. 当前可见区域没有匹配到明显安装/配置/API 片段。"]),
    "代码/命令线索：",
    ...(codeBlocks.length ? codeBlocks.map((text, index) => `${index + 1}. ${text.slice(0, 240)}`) : ["1. 当前可见区域没有明显代码块。"])
  ].join("\n");
}

function buildUiBrief() {
  const elements = collectInteractiveElements();
  const groups = elements.reduce((acc, element) => {
    const key = element.role || element.tag;
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});
  const risky = elements.filter((element) =>
    /提交|发送|删除|付款|支付|发布|上传|submit|send|delete|pay|publish|upload/i.test(
      `${element.label} ${element.text} ${element.placeholder} ${element.name}`
    )
  ).slice(0, 8);
  const workflows = inferWorkflows(elements);

  return [
    `界面分析：${document.title}`,
    `来源：${location.href}`,
    `可交互元素：${elements.length} 个`,
    `控件分布：${Object.entries(groups).map(([key, count]) => `${key}=${count}`).join("，") || "无"}`,
    "可能工作流：",
    ...(workflows.length ? workflows.map((item, index) => `${index + 1}. ${item}`) : ["1. 未识别到明显工作流。"]),
    "需要谨慎确认的按钮：",
    ...(risky.length ? risky.map((element, index) => `${index + 1}. ${element.label || element.text || element.id}`) : ["1. 当前可见区域未发现明显高风险按钮。"])
  ].join("\n");
}

function buildProjectBrief() {
  const headings = Array.from(document.querySelectorAll("h1, h2, h3"))
    .filter(isVisible)
    .map((node) => visibleText(node))
    .filter(Boolean)
    .slice(0, 10);
  const cards = collectCards().slice(0, 8);
  const links = collectStructuredData("links").items
    .filter((link) => /github|docs|readme|license|issue|demo|paper|arxiv|playwright|browser/i.test(`${link.text} ${link.href}`))
    .slice(0, 10);

  return [
    `项目分析：${document.title}`,
    `来源：${location.href}`,
    `页面/项目结构：${headings.join(" / ") || "未提取到标题"}`,
    "模块或候选项：",
    ...(cards.length ? cards.map((card, index) => `${index + 1}. ${card.title} - ${card.summary}`) : ["1. 当前页面没有明显卡片模块。"]),
    "关键资源链接：",
    ...(links.length ? links.map((link, index) => `${index + 1}. ${link.text} - ${link.href}`) : ["1. 当前页面没有明显项目资源链接。"]),
    "可复用性判断：优先复用动作 schema、页面观测、日志/评测模块；对真实提交、发送、支付类动作保持人工确认。"
  ].join("\n");
}

function findOnPage(query) {
  const snippets = extractSnippets(query);
  const elements = collectInteractiveElements()
    .filter((element) => /./.test(query) && scoreText(`${element.label} ${element.text} ${element.placeholder} ${element.name}`, query) > 0)
    .slice(0, 6);

  const firstTarget = elements[0] ? findTarget(elements[0].id) : null;
  if (firstTarget) {
    highlight(firstTarget);
  }

  return [
    `页面查找：${query}`,
    `来源：${location.href}`,
    "相关片段：",
    ...(snippets.length ? snippets : ["1. 没有找到明显文本片段。"]),
    "相关可操作元素：",
    ...(elements.length ? elements.map((element, index) => `${index + 1}. ${element.label || element.text || element.placeholder || element.id} (${element.role || element.tag})`) : ["1. 没有匹配到可操作元素。"])
  ].join("\n");
}

function inferWorkflows(elements) {
  const text = elements.map((element) => `${element.label} ${element.text} ${element.placeholder} ${element.name}`).join(" ");
  const workflows = [];
  if (/搜索|search|query|关键词/i.test(text)) workflows.push("搜索/检索信息");
  if (/姓名|邮箱|email|name|message|备注|表单|contact/i.test(text)) workflows.push("填写表单或联系信息");
  if (/回复|消息|评论|chat|reply|message/i.test(text)) workflows.push("生成消息或评论草稿");
  if (/下载|download|导出|export/i.test(text)) workflows.push("下载或导出资料");
  if (/筛选|排序|filter|sort/i.test(text)) workflows.push("筛选、排序或比较结果");
  return workflows;
}

function scoreText(text, query) {
  const haystack = String(text || "").toLowerCase();
  return String(query || "").toLowerCase().split(/\s+/).filter(Boolean)
    .reduce((score, token) => score + (haystack.includes(token) ? 1 : 0), 0);
}

function summarizePage() {
  const title = document.title || visibleText(document.querySelector("h1"));
  const headings = Array.from(document.querySelectorAll("h1, h2, h3"))
    .filter(isVisible)
    .map((node) => visibleText(node))
    .filter(Boolean);
  const paragraphs = Array.from(document.querySelectorAll("p, li, article, section"))
    .filter(isVisible)
    .map((node) => visibleText(node))
    .filter((text) => text.length >= 18 && text.length <= 360)
    .filter(uniqueByText)
    .slice(0, 8);

  const bullets = [
    ...headings.slice(0, 4).map((text) => `页面模块：${text}`),
    ...paragraphs.slice(0, 5)
  ].slice(0, 6);

  return [
    `页面摘要：${title}`,
    ...bullets.map((text, index) => `${index + 1}. ${text}`)
  ].join("\n");
}

function collectStructuredData(kind) {
  const base = {
    kind,
    sourceUrl: location.href,
    collectedAt: new Date().toISOString()
  };

  if (kind === "links") {
    return {
      ...base,
      items: Array.from(document.querySelectorAll("a[href]"))
        .filter(isVisible)
        .map((link) => ({
          text: visibleText(link) || link.getAttribute("aria-label") || link.href,
          href: link.href
        }))
        .filter((item) => item.text && item.href)
        .filter(uniqueByHref)
        .slice(0, 20)
    };
  }

  if (kind === "emails") {
    const text = document.body.innerText || "";
    return {
      ...base,
      items: Array.from(new Set(text.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi) || []))
    };
  }

  if (kind === "contacts") {
    const text = document.body.innerText || "";
    return {
      ...base,
      emails: Array.from(new Set(text.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi) || [])),
      links: Array.from(document.querySelectorAll("a[href]"))
        .filter(isVisible)
        .map((link) => ({
          text: visibleText(link) || link.getAttribute("aria-label") || link.href,
          href: link.href
        }))
        .filter((item) => item.text && item.href)
        .filter(uniqueByHref)
        .slice(0, 20)
    };
  }

  if (kind === "prices") {
    const text = document.body.innerText || "";
    return {
      ...base,
      items: Array.from(new Set(text.match(/(?:¥|\$|￥)\s?\d+(?:\.\d{1,2})?/g) || []))
    };
  }

  if (kind === "tables") {
    return {
      ...base,
      items: Array.from(document.querySelectorAll("table"))
        .filter(isVisible)
        .map(tableToObject)
        .slice(0, 5)
    };
  }

  return {
    ...base,
    items: collectCards().slice(0, 12)
  };
}

function compareCards(command) {
  const cards = collectCards().filter(isValidProductCard);
  if (cards.length < 2) {
    return [
      "结果比较：",
      "当前页面没有足够的商品候选项（已过滤导航/账号入口等噪声）。",
      "建议：先执行搜索并打开 2-3 个商品详情页后再比较。"
    ].join("\n");
  }

  const keyword = command
    .replace(/比较|对比|排序|哪个更好|哪个更适合|推荐|这些|方案/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const ranked = cards.map((card) => ({
    ...card,
    score: scoreCard(card, keyword)
  })).sort((a, b) => b.score - a.score).slice(0, 5);

  return [
    "结果比较：",
    ...ranked.map((card, index) => {
      const meta = [
        card.price ? `价格 ${card.price}` : "",
        card.rating ? `评分 ${card.rating}` : "",
        `相关性 ${card.score}`
      ].filter(Boolean).join("，");
      return `${index + 1}. ${card.title}\n   ${meta}\n   ${card.summary}`;
    }),
    `推荐：优先查看“${ranked[0].title}”，并继续打开其详情页核对参数、评价数量和价格波动。`
  ].join("\n");
}

function collectCards() {
  const jdCandidates = collectJdSearchCards();
  if (jdCandidates.length >= 2) {
    return rankCards(jdCandidates).slice(0, 24);
  }
  const selectors = [
    "[data-agent-result]",
    "[data-agent-card]",
    "[data-sku]",
    ".gl-item",
    ".sku-item",
    ".good-item",
    "[class*='product']",
    "[class*='goods']",
    "[class*='sku']",
    ".result",
    ".card",
    "article",
    "section"
  ].join(",");
  const nodes = Array.from(document.querySelectorAll(selectors)).filter(isVisible);

  const cards = nodes
    .map((node) => normalizeCard(node))
    .filter((card) => isValidProductCard(card))
    .filter(uniqueByHrefOrTitle)
    .slice(0, 36);

  return rankCards(cards).slice(0, 24);
}

function collectJdSearchCards() {
  const nodes = Array.from(document.querySelectorAll(".gl-item, li.gl-item, [data-sku], .j-sku-item"));
  if (!nodes.length) return [];
  return nodes
    .map((node) => normalizeCard(node))
    .filter((card) => isValidProductCard(card))
    .filter(uniqueByHrefOrTitle)
    .slice(0, 48);
}

function scoreCard(card, keyword) {
  const text = `${card.title} ${card.summary}`.toLowerCase();
  const tokens = keyword.toLowerCase().split(/\s+/).filter(Boolean);
  const keywordScore = tokens.reduce((sum, token) => sum + (text.includes(token) ? 3 : 0), 0);
  const ratingScore = Number(card.rating || 0);
  const contentScore = Math.min(6, Math.floor(card.summary.length / 40));
  const priceScore = card.price ? 2 : 0;
  const detailScore = card.href && !/^javascript:/i.test(card.href) ? 2 : 0;
  return keywordScore + ratingScore + contentScore + priceScore + detailScore;
}

function normalizeCard(node) {
  const text = robustNodeText(node);
  const titleNode = node.querySelector(
    ".p-name em, .title, .name, .goods-name, .product-title, h1, h2, h3, h4, a[title], strong, b, em"
  );
  const title = (
    (titleNode ? visibleText(titleNode) : "")
    || node.querySelector("a[title]")?.getAttribute("title")
    || text.slice(0, 80)
  ).trim();
  const priceNode = node.querySelector(".p-price, .price, [class*='price'], [data-price]");
  const priceText = robustNodeText(priceNode || node);
  const price = priceText.match(/(?:¥|\$|￥)\s?\d+(?:\.\d{1,2})?/)?.[0] || "";
  const rating = text.match(/(?:评分|rating|score)[:： ]?\s?([0-9](?:\.[0-9])?)/i)?.[1] || "";
  const link = resolveDetailLink(node);
  const summary = text.replace(title, "").replace(price, "").trim().slice(0, 260);

  return {
    title,
    summary,
    price,
    rating,
    href: link
  };
}

function resolveDetailLink(node) {
  const anchors = Array.from(node.querySelectorAll("a[href]"));
  for (const anchor of anchors) {
    const href = anchor.href || anchor.getAttribute("href") || "";
    if (!href || /^javascript:/i.test(href)) continue;
    if (/item\.jd\.com|detail|product|sku|goods|dp\/|\/item\//i.test(href)) return href;
  }
  const fallback = anchors.find((a) => (a.href || "").startsWith("http"));
  return fallback?.href || "";
}

function isValidProductCard(card) {
  if (!card.title || card.title.length < 2) return false;
  if (isNavLikeTitle(card.title)) return false;
  if (!card.price && card.summary.length < 18) return false;
  if (card.href && /^javascript:/i.test(card.href)) return false;
  if (!card.href && !card.price) return false;
  return true;
}

function isNavLikeTitle(title) {
  return /首页|登录|注册|我的京东|企业采购|网站导航|客服|地区|消息|购物车|帮助中心|全部分类|更多/i.test(title);
}

function rankCards(cards) {
  return cards
    .map((card) => {
      let base = 0;
      if (card.price) base += 4;
      if (card.rating) base += 2;
      if (card.href) base += 3;
      if (card.summary.length > 40) base += 1;
      return { ...card, _baseScore: base };
    })
    .sort((a, b) => b._baseScore - a._baseScore)
    .map(({ _baseScore, ...card }) => card);
}

function tableToObject(table) {
  return Array.from(table.querySelectorAll("tr")).map((row) =>
    Array.from(row.querySelectorAll("th, td")).map((cell) => visibleText(cell))
  );
}

function collectTables() {
  return Array.from(document.querySelectorAll("table"))
    .filter(isVisible)
    .map(tableToObject)
    .filter((rows) => rows.length > 0)
    .slice(0, 6);
}

function uniqueByText(text, index, all) {
  return all.findIndex((other) => other === text) === index;
}

function uniqueByHref(item, index, all) {
  return all.findIndex((other) => other.href === item.href) === index;
}

function uniqueByTitle(item, index, all) {
  return all.findIndex((other) => other.title === item.title) === index;
}

function uniqueByHrefOrTitle(item, index, all) {
  return all.findIndex((other) => {
    if (item.href && other.href) return other.href === item.href;
    return other.title === item.title;
  }) === index;
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      showAgentToast(`已复制到剪贴板：\n\n${text.slice(0, 1000)}`);
      return;
    } catch (_error) {
      // Fallback to execCommand when the page is not focused.
    }
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  textarea.remove();
  showAgentToast(`已复制到剪贴板：\n\n${text.slice(0, 1000)}`);
}

function extractSnippets(keyword) {
  const tokens = keyword.toLowerCase().split(/\s+/).filter(Boolean);
  const blocks = Array.from(document.querySelectorAll("article, section, li, p, h1, h2, h3, .card, [data-agent-result]"))
    .filter(isVisible)
    .map((node) => visibleText(node))
    .filter((text) => text.length > 12);

  return blocks
    .map((text) => ({
      text,
      score: tokens.reduce((sum, token) => sum + (text.toLowerCase().includes(token) ? 1 : 0), 0)
    }))
    .filter((item) => item.score > 0 || !tokens.length)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
    .map((item, index) => `${index + 1}. ${item.text.slice(0, 280)}`);
}

function labelFor(element) {
  const aria = element.getAttribute("aria-label");
  if (aria) return aria.trim();

  const labelledBy = element.getAttribute("aria-labelledby");
  if (labelledBy) {
    const label = document.getElementById(labelledBy);
    if (label) return visibleText(label);
  }

  if (element.id) {
    const label = document.querySelector(`label[for="${CSS.escape(element.id)}"]`);
    if (label) return visibleText(label);
  }

  const wrappingLabel = element.closest("label");
  if (wrappingLabel) return visibleText(wrappingLabel);

  return "";
}

function implicitRole(element) {
  const tag = element.tagName.toLowerCase();
  if (tag === "a") return "link";
  if (tag === "button") return "button";
  if (tag === "textarea") return "textbox";
  if (tag === "select") return "combobox";
  if (tag === "input") {
    const type = element.getAttribute("type") || "text";
    if (["button", "submit", "reset"].includes(type)) return "button";
    if (type === "search") return "searchbox";
    return "textbox";
  }
  return "";
}

function isVisible(element) {
  const style = window.getComputedStyle(element);
  const rect = element.getBoundingClientRect();
  return style.visibility !== "hidden"
    && style.display !== "none"
    && rect.width > 3
    && rect.height > 3
    && rect.bottom >= 0
    && rect.right >= 0
    && rect.top <= window.innerHeight
    && rect.left <= window.innerWidth;
}

function isProbablyRenderable(element) {
  const style = window.getComputedStyle(element);
  const rect = element.getBoundingClientRect();
  return style.visibility !== "hidden"
    && style.display !== "none"
    && rect.width > 6
    && rect.height > 6;
}

function robustNodeText(node) {
  if (!node) return "";
  const inner = String(node.innerText || "").replace(/\s+/g, " ").trim();
  if (inner) return inner;
  return String(node.textContent || "").replace(/\s+/g, " ").trim();
}

async function ensureCardCandidatesReady() {
  let cards = collectCards();
  if (cards.length >= 2) return cards;
  const startY = window.scrollY;
  window.scrollBy({ top: Math.max(window.innerHeight, 900), behavior: "auto" });
  await delay(600);
  cards = collectCards();
  if (cards.length >= 2) {
    window.scrollTo({ top: startY, behavior: "auto" });
    return cards;
  }
  window.scrollBy({ top: Math.max(window.innerHeight, 900), behavior: "auto" });
  await delay(700);
  cards = collectCards();
  window.scrollTo({ top: startY, behavior: "auto" });
  return cards;
}

function visibleText(node) {
  return (node?.innerText || node?.textContent || "").replace(/\s+/g, " ").trim();
}

function highlight(element) {
  document.querySelectorAll(`.${HIGHLIGHT_CLASS}`).forEach((node) => node.classList.remove(HIGHLIGHT_CLASS));
  element.classList.add(HIGHLIGHT_CLASS);
  element.scrollIntoView({ behavior: "smooth", block: "center", inline: "center" });
}

function ensureStyles() {
  if (document.getElementById("browser-agent-style")) return;
  const style = document.createElement("style");
  style.id = "browser-agent-style";
  style.textContent = `
    .${HIGHLIGHT_CLASS} {
      outline: 3px solid #0f766e !important;
      box-shadow: 0 0 0 6px rgba(15, 118, 110, 0.2) !important;
      transition: outline 120ms ease, box-shadow 120ms ease;
    }
    #browser-agent-toast {
      position: fixed;
      right: 20px;
      bottom: 20px;
      z-index: 2147483647;
      max-width: 460px;
      max-height: 320px;
      overflow: auto;
      border-radius: 16px;
      padding: 14px 16px;
      color: #f8fafc;
      background: #111827;
      box-shadow: 0 18px 48px rgba(15, 23, 42, 0.32);
      font: 13px/1.5 -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
      white-space: pre-wrap;
    }
  `;
  document.documentElement.appendChild(style);
}

function showAgentToast(text) {
  let toast = document.getElementById("browser-agent-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "browser-agent-toast";
    document.body.appendChild(toast);
  }
  toast.textContent = text;
  window.clearTimeout(showAgentToast.timer);
  showAgentToast.timer = window.setTimeout(() => toast.remove(), 12000);
}

function delay(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}
