const API_BASE = "http://127.0.0.1:8000";
const MONITOR_DELAY_MS = 2500;
const MAX_MONITOR_STEPS = 6;

async function appendTimeline(entry) {
  const data = await chrome.storage.local.get(["agentTimeline"]);
  const timeline = Array.isArray(data.agentTimeline) ? data.agentTimeline : [];
  timeline.push({
    ts: new Date().toISOString(),
    level: entry?.level || "info",
    text: entry?.text || "",
  });
  await chrome.storage.local.set({ agentTimeline: timeline.slice(-40) });
}

function cloneResult(result) {
  return result && typeof result === "object" ? JSON.parse(JSON.stringify(result)) : result;
}

function buildIntermediateResult(result, timeline = [], monitorMessage = "", monitorObservations = []) {
  const next = cloneResult(result) || {};
  const report = next.report && typeof next.report === "object" ? next.report : {};
  next.report = report;
  report.summary = report.summary || next.goal || "Agent 正在基于当前页面状态持续规划和执行。";
  if (!Array.isArray(report.reasoning_outline)) {
    report.reasoning_outline = [];
  }
  if (monitorMessage && !report.reasoning_outline.includes(monitorMessage)) {
    report.reasoning_outline = [...report.reasoning_outline, monitorMessage].slice(-8);
  }
  next.monitor = {
    message: monitorMessage,
    observations: monitorObservations
  };
  next.streaming = {
    timeline
  };
  return next;
}

function buildTimelineFromResult(result) {
  const timeline = [];
  const summary = result?.report?.summary || result?.goal || "";
  if (summary) {
    timeline.push({ level: "info", text: `任务理解：${summary}` });
  }
  const progression = Array.isArray(result?.report?.requirement_progression) ? result.report.requirement_progression : [];
  for (const item of progression.slice(0, 4)) {
    const evidence = item?.evidence_summary ? `，依据：${truncateForTimeline(item.evidence_summary, 70)}` : "";
    timeline.push({ level: "info", text: `需求槽位：${item.requirement_slot || item.purpose || "slot"} -> ${item.status || "missing"}${evidence}` });
  }
  const outline = Array.isArray(result?.report?.reasoning_outline) ? result.report.reasoning_outline : [];
  for (const item of outline.slice(0, 3)) {
    timeline.push({ level: "info", text: `动作依据：${item}` });
  }
  const steps = Array.isArray(result?.steps) ? result.steps : [];
  for (const step of steps.slice(0, 6)) {
    const detail = step?.detail || {};
    const fields = detail?.fields || {};
    const mode = fields?.search_execution_mode ? `，执行模式：${fields.search_execution_mode}` : "";
    const submit = fields?.submit_after_type?.method ? `，自动提交：${fields.submit_after_type.method}` : "";
    const failure = step?.failure_type ? `，失败类型：${step.failure_type}` : "";
    timeline.push({
      level: step?.ok ? "info" : "warn",
      text: `动作：${step?.action || "action"}${fields?.evidence_stage ? ` (${fields.evidence_stage})` : ""}${mode}${submit}${failure}`
    });
  }
  const failureRows = Object.entries(result?.failure_analysis?.failure_type_counts || {});
  for (const [failureType, count] of failureRows) {
    if (!count) continue;
    timeline.push({
      level: "warn",
      text: `失败统计：${failureType} x ${count}`
    });
  }
  return timeline;
}

function truncateForTimeline(value, limit = 80) {
  const text = String(value ?? "").replace(/\s+/g, " ").trim();
  return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
}

function normalizeUrl(url) {
  if (!url) return "https://example.com";
  return /^https?:\/\//i.test(url) ? url : `https://${url}`;
}

function findFinalUrl(result) {
  const events = Array.isArray(result?.events) ? result.events : [];
  for (let i = events.length - 1; i >= 0; i -= 1) {
    const url = events[i]?.url;
    if (typeof url === "string" && /^https?:\/\//i.test(url)) {
      return url;
    }
  }
  return null;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function normalizeActionTarget(value) {
  return String(value || "").replace(/#.*$/, "");
}

function urlHost(url) {
  try {
    return new URL(url).hostname.toLowerCase();
  } catch (_error) {
    return "";
  }
}

function isLowQualityCandidateUrl(url, text = "") {
  const host = urlHost(url);
  const haystack = `${url} ${text}`.toLowerCase();
  const blockedHosts = [
    "gitcode.csdn.net",
    "devpress.csdn.net",
    "blog.csdn.net",
    "atomgit.com"
  ];
  if (blockedHosts.includes(host) || host.endsWith(".csdn.net")) {
    return true;
  }
  return /开源社区|代码托管|仓库镜像|mirror|转载|登录后|验证码|403|forbidden|access denied|atomgit|gitcode|csdn/.test(haystack);
}

function candidateQualityScore(goal, domain, url, text = "") {
  if (!/^https?:\/\//i.test(url || "")) return -100;
  if (isLowQualityCandidateUrl(url, text)) return -50;
  const host = urlHost(url);
  const haystack = `${goal} ${text} ${url}`.toLowerCase();
  let score = 0;
  if (domain === "shopping") {
    if (["rtings.com", "soundguys.com", "whathifi.com", "techradar.com", "tomsguide.com", "theverge.com"].some((item) => host.endsWith(item))) score += 10;
    if (["smzdm.com", "zol.com.cn", "jd.com", "tmall.com", "taobao.com", "amazon.com", "bestbuy.com", "soundcore.com", "sony.com", "edifier.com"].some((item) => host.endsWith(item))) score += 7;
    if (["youtube.com", "youtu.be", "bilibili.com"].some((item) => host.endsWith(item))) score += 5;
    if (/评测|review|reviews|对比|compare|comparison|价格|price|pros|cons|优点|缺点|评论|comment/.test(haystack)) score += 4;
  } else if (domain === "github") {
    if (host === "github.com") score += 10;
  } else if (domain === "video") {
    if (["youtube.com", "youtu.be", "bilibili.com", "vimeo.com"].some((item) => host.endsWith(item))) score += 8;
  } else if (/review|评测|compare|comparison|recommend|推荐|repository|repo|readme/.test(haystack)) {
    score += 4;
  }
  return score;
}

function requirementProgression(result = {}) {
  return Array.isArray(result?.report?.requirement_progression) ? result.report.requirement_progression : [];
}

function missingRequirementSlots(result = {}) {
  return requirementProgression(result)
    .filter((item) => !["satisfied", "partial"].includes(String(item?.status || "")))
    .map((item) => String(item?.requirement_slot || ""))
    .filter(Boolean);
}

function candidateMatchesRequirementSlot(url, text = "", requirementSlot = "") {
  const haystack = `${url} ${text}`.toLowerCase();
  if (requirementSlot === "comparative_reviews") {
    return /评测|review|reviews|对比|compare|comparison|pros|cons|优点|缺点|rtings|soundguys|whathifi|techradar|tomsguide|theverge|smzdm|zol/.test(haystack);
  }
  if (requirementSlot === "marketplace_pages") {
    return /商品|参数|价格|price|spec|official|官网|jd\.com|tmall\.com|taobao\.com|amazon\.com|bestbuy\.com|soundcore\.com|sony\.com|edifier\.com/.test(haystack);
  }
  if (requirementSlot === "user_comments") {
    return /评论|差评|comment|comments|complaint|issue|problem|reddit|forum|bbs|评价/.test(haystack);
  }
  if (requirementSlot === "video_reviews") {
    return /youtube|youtu\.be|bilibili|video|watch|视频/.test(haystack);
  }
  return true;
}

function requirementSlotPriorityBoost(url, text = "", requirementSlot = "") {
  if (!candidateMatchesRequirementSlot(url, text, requirementSlot)) {
    return 0;
  }
  if (requirementSlot === "marketplace_pages") {
    return 14;
  }
  if (requirementSlot === "user_comments") {
    return 12;
  }
  if (requirementSlot === "video_reviews") {
    return 10;
  }
  if (requirementSlot === "comparative_reviews") {
    return 8;
  }
  return 6;
}

function rankFollowUpUrls(goal, result = {}) {
  const report = result?.report || {};
  const domain = inferTaskDomain(goal, result);
  const missingSlots = missingRequirementSlots(result);
  const items = [
    ...(Array.isArray(report.recommendations) ? report.recommendations : []),
    ...(Array.isArray(report.candidates) ? report.candidates : []),
    ...(Array.isArray(report.source_readings) ? report.source_readings : []),
    ...(Array.isArray(report.comparison_matrix) ? report.comparison_matrix : []),
    ...(Array.isArray(report.next_actions) ? report.next_actions : []),
  ];
  const seen = new Set();
  const ranked = [];
  for (const item of items) {
    const url = typeof item === "string" ? item : item?.url;
    const text = typeof item === "string" ? "" : [item?.name, item?.title, item?.description, item?.support, item?.review_signal].filter(Boolean).join(" ");
    if (typeof url !== "string" || !/^https?:\/\//i.test(url)) continue;
    if (isLowQualityCandidateUrl(url, text)) continue;
    if (!linkRelevantToTask(goal, domain, url, text)) continue;
    const normalized = normalizeActionTarget(url);
    if (seen.has(normalized)) continue;
    seen.add(normalized);
    let score = candidateQualityScore(goal, domain, url, text);
    for (const slot of missingSlots) {
      score += requirementSlotPriorityBoost(url, text, slot);
    }
    ranked.push({ url, score });
  }
  return ranked.sort((left, right) => right.score - left.score).map((item) => item.url);
}

async function observeTab(tabId) {
  const [execution] = await chrome.scripting.executeScript({
    target: { tabId },
    func: () => {
      const text = (document.body?.innerText || "").replace(/\s+/g, " ").trim();
      const links = Array.from(document.querySelectorAll("a[href]"))
        .map((link, index) => {
          const rect = link.getBoundingClientRect();
          return {
            index,
            text: (link.textContent || "").replace(/\s+/g, " ").trim().slice(0, 120),
            url: link.href,
            visible: rect.width > 0 && rect.height > 0
          };
        })
        .filter((link) => link.visible && /^https?:\/\//i.test(link.url))
        .map(({ visible, ...link }) => link)
        .filter((link) => /^https?:\/\//i.test(link.url))
        .slice(0, 80);
      const controls = Array.from(document.querySelectorAll("input, textarea, button, [role=button]"))
        .map((el, index) => {
          const rect = el.getBoundingClientRect();
          const label =
            el.getAttribute("aria-label") ||
            el.getAttribute("placeholder") ||
            el.getAttribute("name") ||
            el.textContent ||
            "";
          return {
            index,
            tag: el.tagName.toLowerCase(),
            type: el.getAttribute("type") || "",
            role: el.getAttribute("role") || "",
            label: label.replace(/\s+/g, " ").trim().slice(0, 120),
            visible: rect.width > 0 && rect.height > 0,
            disabled: Boolean(el.disabled || el.getAttribute("aria-disabled") === "true")
          };
        })
        .filter((item) => item.visible && !item.disabled)
        .slice(0, 60);
      return {
        title: document.title,
        url: location.href,
        text: text.slice(0, 8000),
        links,
        controls
      };
    }
  });
  return execution?.result || { title: "", url: "", text: "", links: [] };
}

function collectFollowUpUrls(result) {
  return rankFollowUpUrls(String(result?.goal || ""), result);
}

function githubRepoRoot(url) {
  try {
    const parsed = new URL(url);
    if (parsed.hostname !== "github.com") return null;
    const parts = parsed.pathname.split("/").filter(Boolean);
    if (parts.length < 2) return null;
    const [owner, repo] = parts;
    const blocked = new Set([
      "about",
      "apps",
      "blog",
      "collections",
      "contact",
      "customer-stories",
      "enterprise",
      "events",
      "features",
      "github-copilot",
      "login",
      "marketplace",
      "mobile",
      "new",
      "notifications",
      "orgs",
      "pricing",
      "pulls",
      "readme",
      "search",
      "security",
      "settings",
      "signup",
      "solutions",
      "sponsors",
      "topics",
      "trending"
    ]);
    if (blocked.has(owner) || repo.includes(".")) return null;
    return `https://github.com/${owner}/${repo}`;
  } catch (_error) {
    return null;
  }
}

function inferTaskDomain(goal, result = {}) {
  const explicitDomain = result?.workflow?.domain || result?.domain || "";
  if (["github", "paper", "shopping", "video", "general"].includes(explicitDomain)) {
    return explicitDomain;
  }
  const text = goal.toLowerCase();
  if (/github|仓库|开源|repo|repository|项目/i.test(text)) return "github";
  if (/视频|b站|bilibili|youtube|字幕|关键帧|课程|教程|video/i.test(text)) return "video";
  if (/购物|商品|价格|推荐买|耳机|键盘|手机|电脑|降噪|评测|对比/i.test(text)) return "shopping";
  return "general";
}

function isSearchResultPage(url) {
  return /github\.com\/search|arxiv\.org\/search|bing\.com\/search|duckduckgo\.com|google\.[^/]+\/search/i.test(url || "");
}

function sameOrigin(a, b) {
  try {
    return new URL(a).origin === new URL(b).origin;
  } catch (_error) {
    return false;
  }
}

function isVideoPage(url) {
  return /youtube\.com\/watch|youtu\.be\/|bilibili\.com\/video\/|vimeo\.com\/|\/video\//i.test(url || "");
}

function isAccessBlockedPage(observation = {}) {
  const haystack = `${observation.title || ""} ${observation.text || ""} ${observation.url || ""}`.toLowerCase();
  return /403|access denied|forbidden|temporarily restricted|temporarily limit|需要登录|登录后|验证码|captch|访问异常|限制本次访问|私信知乎小管家/.test(haystack);
}

function linkRelevantToTask(goal, domain, url, text = "") {
  const haystack = `${goal} ${text} ${url}`.toLowerCase();
  if (/stock|finance|fund|quote|指数|股票|证券|基金|行情|成分股|corp\/go\.php|新浪财经/i.test(haystack)) {
    return false;
  }
  if (domain === "shopping") {
    const productSignals = /耳机|降噪|headphone|headphones|anc|sony|edifier|soundcore|space q45|wh-ch720n|w820nb/i;
    const evidenceSignals = /评测|review|reviews|对比|compare|comparison|price|价格|pros|cons|优点|缺点|recommend|推荐/i;
    const marketplaceSignals = /商品|参数|spec|official|官网|jd\.com|tmall\.com|taobao\.com|amazon\.com|bestbuy\.com|soundcore\.com|sony\.com|edifier\.com/i;
    return productSignals.test(haystack) && (evidenceSignals.test(haystack) || marketplaceSignals.test(haystack));
  }
  if (domain === "github") {
    return /github\.com\/[^/]+\/[^/]+|repository|repo|readme|开源|仓库/i.test(haystack);
  }
  if (domain === "video") {
    return /youtube|bilibili|video|watch|教程|讲解|字幕|review/i.test(haystack);
  }
  if (domain === "paper") {
    return /arxiv|paper|doi|openreview|semanticscholar|论文/i.test(haystack);
  }
  return true;
}

function isShoppingEvidencePage(goal, observation, hits) {
  const url = observation.url || "";
  if (isSearchResultPage(url)) return false;
  const text = `${observation.title} ${observation.text} ${url}`.toLowerCase();
  const wantsHeadphones = /耳机|降噪|headphone|anc|wh-ch720n|w820nb|space q45|q45/i.test(goal);
  const productSignals = [
    "耳机",
    "降噪",
    "headphone",
    "headphones",
    "anc",
    "wh-ch720n",
    "w820nb",
    "space q45",
    "soundcore",
    "edifier",
    "sony"
  ];
  const evidenceSignals = ["评测", "review", "reviews", "对比", "compare", "comparison", "price", "价格", "pros", "cons", "优点", "缺点"];
  const productHit = productSignals.some((token) => text.includes(token));
  const evidenceHit = evidenceSignals.some((token) => text.includes(token));
  return wantsHeadphones ? productHit && (evidenceHit || hits.length >= 2) : hits.length >= 2 && !isSearchResultPage(url);
}

function isVideoEvidencePage(goal, observation, hits) {
  const url = observation.url || "";
  const text = `${observation.title} ${observation.text} ${url}`.toLowerCase();
  const wantsVideo = /视频|b站|bilibili|youtube|字幕|关键帧|课程|教程|video/i.test(goal);
  const videoSignals = ["video", "watch", "bilibili", "youtube", "播放", "字幕", "简介", "transcript", "subscribe"];
  return wantsVideo && isVideoPage(url) && videoSignals.some((token) => text.includes(token)) && hits.length >= 1;
}

function requirementCoverageOk(result, domain) {
  const items = Array.isArray(result?.report?.requirement_progression) ? result.report.requirement_progression : [];
  if (!items.length) return domain === "general";
  const statusOf = (slot) => items.find((item) => item?.requirement_slot === slot)?.status || "missing";
  if (domain === "shopping") {
    const requiredSlots = ["candidate_pool", "comparative_reviews"];
    const satisfied = requiredSlots.filter((slot) => ["satisfied", "partial"].includes(statusOf(slot)));
    const optionalSignals = ["user_comments", "video_reviews", "marketplace_pages"].filter((slot) => ["satisfied", "partial"].includes(statusOf(slot)));
    return satisfied.length === requiredSlots.length && optionalSignals.length >= 1;
  }
  if (domain === "github") {
    return ["repo_candidates", "repo_metadata"].every((slot) => ["satisfied", "partial"].includes(statusOf(slot)));
  }
  if (domain === "video") {
    return ["video_candidates", "transcript_notes"].every((slot) => ["satisfied", "partial"].includes(statusOf(slot)));
  }
  if (domain === "paper") {
    return ["seed_papers", "related_work"].every((slot) => ["satisfied", "partial"].includes(statusOf(slot)));
  }
  return true;
}

function searchQueryFromGoal(goal) {
  return String(goal || "")
    .replace(/帮我|请|查询|搜索|整理|推荐|一下/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 120);
}

function derivePageActions(goal, observation, verdict, result = {}) {
  if (verdict?.ok) return [];
  const actions = [];
  const controls = Array.isArray(observation.controls) ? observation.controls : [];
  const links = Array.isArray(observation.links) ? observation.links : [];
  const currentUrl = observation.url || "";
  const query = searchQueryFromGoal(goal);
  const domain = inferTaskDomain(goal, result);
  const followUpUrls = collectFollowUpUrls(result);
  const accessBlocked = isAccessBlockedPage(observation);
  const searchBox = controls.find((control) => {
    const text = `${control.tag} ${control.type} ${control.role} ${control.label}`.toLowerCase();
    return (
      ["input", "textarea"].includes(control.tag) &&
      !/password|email|tel|number|checkbox|radio|file/i.test(control.type) &&
      /search|搜索|query|q|关键词|keyword|find/.test(text)
    );
  }) || controls.find((control) => {
    return ["input", "textarea"].includes(control.tag) && !/password|email|tel|number|checkbox|radio|file/i.test(control.type);
  });
  const pageLooksRecoverable =
    isSearchResultPage(currentUrl) ||
    /bing\.com\/?$|google\.[^/]+\/?$|duckduckgo\.com\/?$|github\.com\/?$|arxiv\.org\/?$/i.test(currentUrl) ||
    ["not_on_repository_page_yet", "not_on_video_page_yet", "shopping_search_page_needs_product_or_review_page", "insufficient_task_match", "zero_or_no_match_results"].includes(verdict?.reason || "");
  const onSearchResults = isSearchResultPage(currentUrl);
  const externalFollowUps = followUpUrls.filter((url) => {
    if (!/^https?:\/\//i.test(url || "")) return false;
    if (normalizeActionTarget(url) === normalizeActionTarget(currentUrl)) return false;
    if (sameOrigin(url, currentUrl) && isSearchResultPage(url)) return false;
    if (isLowQualityCandidateUrl(url)) return false;
    if (!linkRelevantToTask(goal, domain, url, "")) return false;
    return true;
  });
  for (const url of externalFollowUps.slice(0, 3)) {
    actions.push({
      type: "click_link",
      url,
      reason: "open_report_candidate",
    });
  }
  if (!onSearchResults) {
    if (accessBlocked && actions.length) {
      return actions.slice(0, 3);
    }
    if (query && searchBox && pageLooksRecoverable && actions.length === 0) {
      return [{
        type: "fill_and_submit",
        controlIndex: searchBox.index,
        value: query,
        reason: "fill_visible_search_box",
      }];
    }
    return actions.slice(0, 3);
  }
  const candidateLinks = links.filter((link) => {
    const targetUrl = String(link.url || "");
    if (!/^https?:\/\//i.test(targetUrl)) return false;
    if (normalizeActionTarget(targetUrl) === normalizeActionTarget(currentUrl)) return false;
    if (targetUrl.includes("#") && normalizeActionTarget(targetUrl) === normalizeActionTarget(currentUrl)) return false;
    if (onSearchResults && sameOrigin(targetUrl, currentUrl) && isSearchResultPage(targetUrl)) return false;
    if (isLowQualityCandidateUrl(targetUrl, link.text || "")) return false;
    if (!linkRelevantToTask(goal, domain, targetUrl, link.text || "")) return false;
    const text = `${link.text || ""} ${link.url || ""}`.toLowerCase();
    if (domain === "github") {
      return Boolean(githubRepoRoot(link.url));
    }
    if (domain === "video") {
      return isVideoPage(link.url);
    }
    if (domain === "shopping") {
      return /耳机|降噪|headphone|headphones|anc|wh-ch720n|w820nb|space q45|q45|sony|edifier|soundcore|评测|review|对比|compare/.test(text);
    }
    return /repository|repo|project|readme|docs|documentation|教程|视频|课程|paper|arxiv|review|compare|comparison/i.test(text);
  });
  const rankedCandidateLinks = candidateLinks.sort((left, right) => {
    const scoreDiff = candidateQualityScore(goal, domain, right.url, right.text || "") - candidateQualityScore(goal, domain, left.url, left.text || "");
    if (scoreDiff !== 0) return scoreDiff;
    const leftExternal = sameOrigin(left.url, currentUrl) ? 0 : 1;
    const rightExternal = sameOrigin(right.url, currentUrl) ? 0 : 1;
    return rightExternal - leftExternal;
  });
  for (const candidateLink of rankedCandidateLinks.slice(0, 3)) {
    actions.push({
      type: "click_link",
      linkIndex: candidateLink.index,
      url: githubRepoRoot(candidateLink.url) || candidateLink.url,
      reason: "open_visible_candidate",
    });
  }
  if (query && searchBox && pageLooksRecoverable && actions.length === 0) {
    actions.push({
      type: "fill_and_submit",
      controlIndex: searchBox.index,
      value: query,
      reason: "fill_visible_search_box",
    });
  }
  return actions.slice(0, 3);
}

async function fetchRunResult(apiBase, payload, currentObservation) {
  const response = await fetch(`${apiBase}/api/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...payload,
      current_page_observation: currentObservation
    })
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    throw new Error(data.error || "请求失败");
  }
  return data.result;
}

async function executePageAction(tabId, action) {
  if (!action || !action.type) return { ok: false, reason: "missing_action" };
  if (action.type === "click_link" && /^https?:\/\//i.test(action.url || "")) {
    const beforeTab = await chrome.tabs.get(tabId);
    const beforeUrl = beforeTab?.url || "";
    if (Number.isInteger(action.linkIndex)) {
      const [execution] = await chrome.scripting.executeScript({
        target: { tabId },
        args: [action.linkIndex, action.url],
        func: (linkIndex, expectedUrl) => {
          const links = Array.from(document.querySelectorAll("a[href]"));
          const target = links[linkIndex];
          if (!target) {
            return { ok: false, reason: "link_not_found_for_click", fallback_url: expectedUrl };
          }
          const rect = target.getBoundingClientRect();
          if (rect.width <= 0 || rect.height <= 0) {
            return { ok: false, reason: "link_not_visible_for_click", fallback_url: expectedUrl };
          }
          const href = target.href;
          if (expectedUrl && href && href !== expectedUrl) {
            const normalizedExpected = expectedUrl.replace(/#.*$/, "");
            const normalizedHref = href.replace(/#.*$/, "");
            if (normalizedExpected !== normalizedHref) {
              return { ok: false, reason: "link_href_mismatch", fallback_url: expectedUrl, actual_url: href };
            }
          }
          target.scrollIntoView({ block: "center", inline: "nearest" });
          target.click();
          return { ok: true, reason: "clicked_visible_link", clicked_url: href || expectedUrl };
        }
      });
      const clickResult = execution?.result || { ok: false, reason: "no_execution_result", fallback_url: action.url };
      if (clickResult.ok) {
        const normalizedBefore = normalizeActionTarget(beforeUrl);
        const normalizedTarget = normalizeActionTarget(clickResult.clicked_url || action.url);
        for (let attempt = 0; attempt < 6; attempt += 1) {
          await sleep(250);
          const currentTab = await chrome.tabs.get(tabId);
          const currentUrl = currentTab?.url || "";
          if (normalizeActionTarget(currentUrl) !== normalizedBefore) {
            return { ok: true, action, reason: clickResult.reason, clicked_url: currentUrl };
          }
        }
        await chrome.tabs.update(tabId, { url: normalizedTarget });
        return { ok: true, action, reason: `${clickResult.reason}_fallback_tab_update_after_no_navigation`, clicked_url: normalizedTarget };
      }
      await chrome.tabs.update(tabId, { url: action.url });
      return { ok: true, action, reason: `${clickResult.reason || "click_failed"}_fallback_tab_update` };
    }
    await chrome.tabs.update(tabId, { url: action.url });
    return { ok: true, action, reason: "tab_update_without_link_index" };
  }
  if (action.type !== "fill_and_submit") {
    return { ok: false, reason: "unsupported_action", action };
  }
  const [execution] = await chrome.scripting.executeScript({
    target: { tabId },
    args: [action.controlIndex, action.value],
    func: (controlIndex, value) => {
      const controls = Array.from(document.querySelectorAll("input, textarea, button, [role=button]"));
      const target = controls[controlIndex];
      if (!target || !("value" in target)) {
        return { ok: false, reason: "control_not_found_or_not_fillable" };
      }
      const rect = target.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0 || target.disabled || target.getAttribute("aria-disabled") === "true") {
        return { ok: false, reason: "control_not_visible_or_disabled" };
      }
      target.focus();
      target.value = value;
      target.dispatchEvent(new Event("input", { bubbles: true }));
      target.dispatchEvent(new Event("change", { bubbles: true }));
      const beforeUrl = location.href;
      const beforeTitle = document.title;
      const beforeText = (document.body?.innerText || "").replace(/\s+/g, " ").trim().slice(0, 500);
      const pageAdvanced = () => {
        const currentText = (document.body?.innerText || "").replace(/\s+/g, " ").trim().slice(0, 500);
        return location.href !== beforeUrl || document.title !== beforeTitle || currentText !== beforeText;
      };
      const form = target.closest("form");
      if (form) {
        form.requestSubmit ? form.requestSubmit() : form.submit();
        if (pageAdvanced()) {
          return { ok: true, reason: "submitted_form" };
        }
      }
      try {
        target.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", bubbles: true }));
        target.dispatchEvent(new KeyboardEvent("keypress", { key: "Enter", code: "Enter", bubbles: true }));
        target.dispatchEvent(new KeyboardEvent("keyup", { key: "Enter", code: "Enter", bubbles: true }));
        if (typeof target.form?.requestSubmit === "function") {
          target.form.requestSubmit();
        }
        if (pageAdvanced()) {
          return { ok: true, reason: "pressed_enter" };
        }
      } catch (_error) {
        // Continue to button click fallback.
      }
      const searchButton = controls.find((control) => {
        if (control === target) return false;
        const rect = control.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) return false;
        if (control.disabled || control.getAttribute("aria-disabled") === "true") return false;
        const label = `${control.getAttribute("aria-label") || ""} ${control.getAttribute("name") || ""} ${control.textContent || ""}`.toLowerCase();
        const tag = (control.tagName || "").toLowerCase();
        const type = (control.getAttribute("type") || "").toLowerCase();
        return tag === "button" || type === "submit" || /search|搜索|submit|go|查找/.test(label);
      });
      if (searchButton) {
        searchButton.click();
        if (pageAdvanced()) {
          return { ok: true, reason: "clicked_search_button" };
        }
      }
      return { ok: false, reason: "submit_not_triggered" };
    }
  });
  return execution?.result || { ok: false, reason: "no_execution_result" };
}

function scoreObservation(goal, result, observation) {
  const text = `${observation.title} ${observation.url} ${observation.text}`.toLowerCase();
  const query = result?.llm?.plan?.query || "";
  const tokens = `${goal} ${query}`
    .toLowerCase()
    .split(/[^a-z0-9\u4e00-\u9fa5]+/u)
    .filter((token) => token.length >= 3);
  const uniqueTokens = Array.from(new Set(tokens)).slice(0, 12);
  const hits = uniqueTokens.filter((token) => text.includes(token));
  const hasZeroResults = [
    "0 results",
    "did not match any repositories",
    "did not match any",
    "未找到",
    "没有找到",
    "无结果"
  ].some((pattern) => text.includes(pattern));
  const hasSearchResultPage = isSearchResultPage(observation.url);
  const isGithubRepoPage = Boolean(githubRepoRoot(observation.url));
  const hasGithubRepoChrome =
    /(^|\s)code(\s|$)/i.test(observation.text) &&
    /(issues|pull requests|readme|about|stars|forks|commits)/i.test(observation.text);
  const wantsGithubRepo = /github|仓库|开源|repo|repository|项目/i.test(goal.toLowerCase());
  const domain = inferTaskDomain(goal, result);
  const enoughContent = observation.text.length > 300;
  let domainOk = hits.length >= 2 || (hasSearchResultPage && domain === "general");
  if (domain === "github") {
    domainOk = wantsGithubRepo && isGithubRepoPage && hasGithubRepoChrome && hits.length >= 1;
  } else if (domain === "shopping") {
    domainOk = isShoppingEvidencePage(goal, observation, hits);
  } else if (domain === "video") {
    domainOk = isVideoEvidencePage(goal, observation, hits);
  } else if (domain === "paper") {
    domainOk = !hasSearchResultPage && (/arxiv\.org\/abs|arxiv\.org\/pdf|doi\.org|semanticscholar|openreview/i.test(observation.url) || hits.length >= 2);
  }
  const coverageOk = requirementCoverageOk(result, domain);
  const ok =
    enoughContent &&
    !hasZeroResults &&
    domainOk &&
    coverageOk;
  return {
    ok,
    reason: ok
      ? "page_matches_task"
      : hasZeroResults
        ? "zero_or_no_match_results"
        : domain === "github" && !isGithubRepoPage
          ? "not_on_repository_page_yet"
          : domain === "shopping" && hasSearchResultPage
            ? "shopping_search_page_needs_product_or_review_page"
            : domain === "shopping" && !coverageOk
              ? "shopping_requirement_coverage_incomplete"
            : domain === "video" && !isVideoPage(observation.url)
              ? "not_on_video_page_yet"
              : !coverageOk
                ? "requirement_coverage_incomplete"
          : "insufficient_task_match",
    hits,
    domain,
    coverageOk,
    hasZeroResults,
    hasSearchResultPage,
    isGithubRepoPage,
    hasGithubRepoChrome,
    isVideoPage: isVideoPage(observation.url),
    url: observation.url,
    title: observation.title
  };
}

async function monitorAndContinue(tabId, payload, result, apiBase = API_BASE) {
  const attemptedUrls = new Set();
  const blockedOrigins = new Set();
  let followUpUrls = collectFollowUpUrls(result);
  const observations = [];
  let replans = 0;
  let seedRecoveryUsed = false;

  for (let step = 1; step <= MAX_MONITOR_STEPS; step += 1) {
    await sleep(MONITOR_DELAY_MS);
    const observation = await observeTab(tabId);
    const verdict = scoreObservation(payload.goal, result, observation);
    observations.push({ step, verdict, url: observation.url, title: observation.title });
    await appendTimeline({
      level: verdict.ok ? "info" : "warn",
      text: `监视第 ${step} 步：${verdict.ok ? "页面已满足任务" : verdict.reason || "继续观察"}`
    });
    const currentState = await chrome.storage.local.get(["agentTimeline"]);
    await chrome.storage.local.set({
      lastResult: buildIntermediateResult(result, currentState.agentTimeline || [], `监视第 ${step} 步：${verdict.ok ? "页面已满足任务" : verdict.reason || "继续观察"}`, observations),
      monitorObservations: observations
    });
    if (verdict.ok) {
      return { ok: true, status: "satisfied", observations, finalUrl: observation.url };
    }
    if (isAccessBlockedPage(observation)) {
      try {
        blockedOrigins.add(new URL(observation.url).origin);
      } catch (_error) {
        // Ignore malformed URLs.
      }
      await appendTimeline({
        level: "warn",
        text: "当前候选页面存在访问限制，准备切换到其他候选来源。"
      });
    }

    const pageActions = derivePageActions(payload.goal, observation, verdict, result).filter((action) => {
      if (action?.type !== "click_link" || !action.url) {
        return true;
      }
      try {
        return !blockedOrigins.has(new URL(action.url).origin);
      } catch (_error) {
        return true;
      }
    });
    const nextAction = pageActions.find((action) => {
      const actionKey = action?.type === "click_link"
        ? `action:${action.type}:${normalizeActionTarget(action.url)}`
        : `action:${JSON.stringify(action)}`;
      return !attemptedUrls.has(actionKey);
    });
    if (nextAction) {
      const actionKey = nextAction?.type === "click_link"
        ? `action:${nextAction.type}:${normalizeActionTarget(nextAction.url)}`
        : `action:${JSON.stringify(nextAction)}`;
      attemptedUrls.add(actionKey);
      const actionResult = await executePageAction(tabId, nextAction);
      observations[observations.length - 1].pageAction = { action: nextAction, result: actionResult };
      await appendTimeline({
        level: actionResult?.ok ? "info" : "warn",
        text: `执行页面动作：${nextAction.reason} -> ${actionResult?.reason || actionResult?.ok || "unknown"}`
      });
      await chrome.storage.local.set({
        agentStatus: "monitoring",
        monitorMessage: `页面未满足任务，正在执行页面动作：${nextAction.reason}`,
        monitorObservations: observations,
        lastResult: buildIntermediateResult(result, (await chrome.storage.local.get(["agentTimeline"])).agentTimeline || [], `页面未满足任务，正在执行页面动作：${nextAction.reason}`, observations)
      });
      continue;
    }
    if (replans < 2) {
      replans += 1;
      await appendTimeline({ level: "info", text: `当前页仍未满足任务，基于当前页面重新规划（第 ${replans} 次）。` });
      result = await fetchRunResult(apiBase, { ...payload, resume_from_current_tab: true }, observation);
      followUpUrls = collectFollowUpUrls(result);
      for (const entry of buildTimelineFromResult(result)) {
        await appendTimeline(entry);
      }
      const replannedTimeline = (await chrome.storage.local.get(["agentTimeline"])).agentTimeline || [];
      await chrome.storage.local.set({
        agentStatus: "monitoring",
        monitorMessage: `当前页仍未满足任务，已基于当前页重新规划（第 ${replans} 次）`,
        monitorObservations: observations,
        lastResult: buildIntermediateResult(result, replannedTimeline, `当前页仍未满足任务，已基于当前页重新规划（第 ${replans} 次）`, observations)
      });
      const replannedUrl = findFinalUrl(result);
      if (replannedUrl && replannedUrl !== observation.url && !attemptedUrls.has(replannedUrl)) {
        attemptedUrls.add(replannedUrl);
        await appendTimeline({ level: "info", text: `根据新的当前页规划跳转：${replannedUrl}` });
        await chrome.tabs.update(tabId, { url: replannedUrl });
      }
      continue;
    }
    const candidates = [...followUpUrls];
    const nextUrl = candidates.find((url) => !attemptedUrls.has(url) && url !== observation.url);
    if (!nextUrl) {
      const seedUrl = normalizeUrl(payload.url || "");
      if (!seedRecoveryUsed && seedUrl && normalizeActionTarget(seedUrl) !== normalizeActionTarget(observation.url) && !isSearchResultPage(observation.url)) {
        seedRecoveryUsed = true;
        attemptedUrls.add(seedUrl);
        await appendTimeline({ level: "info", text: `当前候选页无法继续，返回初始结果页恢复：${seedUrl}` });
        await chrome.storage.local.set({
          agentStatus: "monitoring",
          monitorMessage: "当前候选页无法继续，正在返回初始结果页恢复",
          monitorObservations: observations,
          lastResult: buildIntermediateResult(result, (await chrome.storage.local.get(["agentTimeline"])).agentTimeline || [], "当前候选页无法继续，正在返回初始结果页恢复", observations)
        });
        await chrome.tabs.update(tabId, { url: seedUrl });
        continue;
      }
      return { ok: false, status: "needs_human_review", observations, finalUrl: observation.url };
    }

    attemptedUrls.add(nextUrl);
    await appendTimeline({ level: "info", text: `继续跳转：${nextUrl}` });
    await chrome.storage.local.set({
      agentStatus: "monitoring",
      monitorMessage: `页面未满足任务，继续打开：${nextUrl}`,
      monitorObservations: observations,
      lastResult: buildIntermediateResult(result, (await chrome.storage.local.get(["agentTimeline"])).agentTimeline || [], `页面未满足任务，继续打开：${nextUrl}`, observations)
    });
    await chrome.tabs.update(tabId, { url: nextUrl });
  }

  const lastObservation = observations[observations.length - 1];
  return { ok: false, status: "max_monitor_steps_reached", observations, finalUrl: lastObservation?.url || "" };
}

async function controlBrowser(tabId, payload, apiBase = API_BASE) {
  const resumeFromCurrentTab = Boolean(payload?.resume_from_current_tab);
  const currentObservation = await observeTab(tabId);
  const storagePatch = {
    agentStatus: "running",
    agentError: "",
    finalUrl: "",
    monitorMessage: "",
    monitorObservations: []
  };
  if (!resumeFromCurrentTab) {
    storagePatch.lastResult = null;
    storagePatch.agentTimeline = [];
  }
  await chrome.storage.local.set(storagePatch);
  if (resumeFromCurrentTab) {
    await appendTimeline({ level: "info", text: "从当前页面恢复执行，不刷新已有上下文。" });
  } else {
    await appendTimeline({ level: "info", text: `收到任务：${payload.goal}` });
    await appendTimeline({ level: "info", text: `打开起始页：${normalizeUrl(payload.url)}` });
  }
  if (!resumeFromCurrentTab) {
    await chrome.tabs.update(tabId, { url: normalizeUrl(payload.url) });
  }
  await appendTimeline({ level: "info", text: "等待后端进行多模态规划..." });

  const result = await fetchRunResult(apiBase, payload, currentObservation);
  for (const entry of buildTimelineFromResult(result)) {
    await appendTimeline(entry);
  }
  const currentTimeline = (await chrome.storage.local.get(["agentTimeline"])).agentTimeline || [];

  const finalUrl = findFinalUrl(result);
  if (finalUrl) {
    await appendTimeline({ level: "info", text: `根据规划跳转到目标页：${finalUrl}` });
    await chrome.tabs.update(tabId, { url: finalUrl });
  }

  await chrome.storage.local.set({
    agentStatus: "monitoring",
    monitorMessage: "正在监视页面是否满足任务要求",
    lastResult: buildIntermediateResult(result, currentTimeline, "正在监视页面是否满足任务要求", []),
    finalUrl: finalUrl || ""
  });
  const monitor = await monitorAndContinue(tabId, payload, result, apiBase);
  await appendTimeline({
    level: monitor.ok ? "info" : "warn",
    text: monitor.ok ? "监视结束：任务页面满足要求" : "监视结束：仍需人工复核"
  });

  await chrome.storage.local.set({
    agentStatus: monitor.ok ? "done" : "needs_review",
    agentError: "",
    lastResult: buildIntermediateResult(result, (await chrome.storage.local.get(["agentTimeline"])).agentTimeline || [], monitor.ok ? "任务页面已满足要求" : "监视后仍未确认满足任务要求", monitor.observations),
    finalUrl: monitor.finalUrl || finalUrl || "",
    monitorMessage: monitor.ok ? "任务页面已满足要求" : "监视后仍未确认满足任务要求",
    monitorObservations: monitor.observations
  });
}

if (typeof chrome !== "undefined" && chrome.runtime?.onMessage) {
  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type !== "RUN_AGENT") {
      return false;
    }

    controlBrowser(message.tabId, message.payload, message.apiBase || API_BASE).catch(async (error) => {
      await appendTimeline({ level: "error", text: `执行失败：${error.message || String(error)}` });
      await chrome.storage.local.set({
        agentStatus: "error",
        agentError: error.message || String(error)
      });
    });

    sendResponse({ ok: true });
    return false;
  });
}

if (typeof module !== "undefined") {
  module.exports = {
    collectFollowUpUrls,
    derivePageActions,
    fetchRunResult,
    inferTaskDomain,
    isSearchResultPage,
    isShoppingEvidencePage,
    isVideoEvidencePage,
    scoreObservation
  };
}
