const API_BASE = "http://127.0.0.1:8000";
const MONITOR_DELAY_MS = 2500;
const MAX_MONITOR_STEPS = 4;

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

async function observeTab(tabId) {
  const [execution] = await chrome.scripting.executeScript({
    target: { tabId },
    func: () => {
      const text = (document.body?.innerText || "").replace(/\s+/g, " ").trim();
      const links = Array.from(document.querySelectorAll("a[href]"))
        .map((link) => ({
          text: (link.textContent || "").replace(/\s+/g, " ").trim().slice(0, 120),
          url: link.href
        }))
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
  const report = result?.report || {};
  const events = Array.isArray(result?.events) ? result.events : [];
  const items = [
    ...(Array.isArray(report.recommendations) ? report.recommendations : []),
    ...(Array.isArray(report.candidates) ? report.candidates : []),
    ...(Array.isArray(report.source_readings) ? report.source_readings : []),
    ...(Array.isArray(report.comparison_matrix) ? report.comparison_matrix : []),
    ...(Array.isArray(report.next_actions) ? report.next_actions : []),
    ...events.map((event) => event?.url)
  ];
  return Array.from(new Set(items
    .map((item) => (typeof item === "string" ? item : item?.url))
    .filter((url) => typeof url === "string" && /^https?:\/\//i.test(url))));
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

function isVideoPage(url) {
  return /youtube\.com\/watch|youtu\.be\/|bilibili\.com\/video\/|vimeo\.com\/|\/video\//i.test(url || "");
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

function deriveFollowUpUrls(goal, observation, verdict) {
  const links = Array.isArray(observation.links) ? observation.links : [];
  const urls = [];
  const currentUrl = observation.url || "";
  const goalText = goal.toLowerCase();
  const meaningfulTokens = goalText
    .split(/[^a-z0-9\u4e00-\u9fa5]+/u)
    .filter((token) => token.length >= 3)
    .filter((token) => !["github", "open", "source", "repo", "repository", "project", "搜索", "开源", "项目"].includes(token));
  const isGithubSearch = /^https:\/\/github\.com\/search/i.test(currentUrl);
  const wantsGithub = /github|仓库|开源|repo|repository|项目/i.test(goalText);
  const wantsVideo = /视频|b站|bilibili|youtube|字幕|关键帧|课程|教程|video/i.test(goalText);
  const wantsShopping = /购物|商品|价格|推荐买|耳机|键盘|手机|电脑|降噪|评测|对比/i.test(goalText);

  if (isGithubSearch && verdict.hasZeroResults) {
    const searchTabs = [
      "type=repositories",
      "type=issues",
      "type=pullrequests",
      "type=wikis",
      "type=code"
    ];
    for (const type of searchTabs) {
      const next = currentUrl.includes("type=")
        ? currentUrl.replace(/type=[^&]+/, type)
        : `${currentUrl}${currentUrl.includes("?") ? "&" : "?"}${type}`;
      urls.push(next);
    }
  }

  if (wantsGithub) {
    for (const link of links) {
      const text = `${link.text || ""} ${link.url || ""}`.toLowerCase();
      const repoRoot = githubRepoRoot(link.url);
      if (!repoRoot) continue;
      const hasGoalToken = meaningfulTokens.some((token) => text.includes(token));
      if (
        (isGithubSearch && hasGoalToken) ||
        /\/issues\/\d+|\/pull\/\d+|\/discussions\/\d+|\/wiki|\/blob\/|\/tree\//i.test(link.url) ||
        (/issue|pull request|wiki|code|repository|仓库|项目/.test(text) && hasGoalToken)
      ) {
        urls.push(repoRoot);
      }
    }
  }

  if (wantsVideo) {
    for (const link of links) {
      const text = `${link.text || ""} ${link.url || ""}`.toLowerCase();
      if (isVideoPage(link.url) || /youtube|bilibili|vimeo|视频|教程|watch|课程/.test(text)) {
        urls.push(link.url);
      }
    }
  }

  if (wantsShopping) {
    for (const link of links) {
      const text = `${link.text || ""} ${link.url || ""}`.toLowerCase();
      const hasProductSignal = /耳机|降噪|headphone|headphones|anc|wh-ch720n|w820nb|space q45|q45|sony|edifier|soundcore|评测|review|对比|compare/.test(text);
      const isBadUtility = /在线音频降噪|audio-noise-reduction|noise-removal|denoise|audio cleaner|股票|指数|finance/.test(text);
      if (hasProductSignal && !isBadUtility) {
        urls.push(link.url);
      }
    }
  }

  return Array.from(new Set(urls.filter((url) => url && url !== currentUrl)));
}

function searchQueryFromGoal(goal) {
  return String(goal || "")
    .replace(/帮我|请|查询|搜索|整理|推荐|一下/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 120);
}

function derivePageActions(goal, observation, verdict) {
  if (verdict?.ok) return [];
  const actions = [];
  const controls = Array.isArray(observation.controls) ? observation.controls : [];
  const links = Array.isArray(observation.links) ? observation.links : [];
  const currentUrl = observation.url || "";
  const query = searchQueryFromGoal(goal);
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
  if (query && searchBox && (isSearchResultPage(currentUrl) || /bing\.com\/?$|google\.[^/]+\/?$|duckduckgo\.com\/?$|github\.com\/?$|arxiv\.org\/?$/i.test(currentUrl))) {
    actions.push({
      type: "fill_and_submit",
      controlIndex: searchBox.index,
      value: query,
      reason: "fill_visible_search_box",
    });
  }
  if (verdict?.domain === "github" && verdict?.reason === "not_on_repository_page_yet") {
    const repoLink = links.find((link) => githubRepoRoot(link.url));
    if (repoLink) {
      actions.push({ type: "click_link", url: githubRepoRoot(repoLink.url), reason: "open_repository_candidate" });
    }
  }
  if (verdict?.domain === "video" && verdict?.reason === "not_on_video_page_yet") {
    const videoLink = links.find((link) => isVideoPage(link.url));
    if (videoLink) {
      actions.push({ type: "click_link", url: videoLink.url, reason: "open_video_candidate" });
    }
  }
  return actions.slice(0, 3);
}

async function executePageAction(tabId, action) {
  if (!action || !action.type) return { ok: false, reason: "missing_action" };
  if (action.type === "click_link" && /^https?:\/\//i.test(action.url || "")) {
    await chrome.tabs.update(tabId, { url: action.url });
    return { ok: true, action };
  }
  if (action.type !== "fill_and_submit") {
    return { ok: false, reason: "unsupported_action", action };
  }
  const [execution] = await chrome.scripting.executeScript({
    target: { tabId },
    args: [action.controlIndex, action.value],
    func: (controlIndex, value) => {
      const controls = Array.from(document.querySelectorAll("input, textarea, button, [role=button]"))
        .map((el, index) => ({ el, index }))
        .filter(({ el }) => {
          const rect = el.getBoundingClientRect();
          return rect.width > 0 && rect.height > 0 && !el.disabled && el.getAttribute("aria-disabled") !== "true";
        });
      const target = controls.find((item) => item.index === controlIndex)?.el;
      if (!target || !("value" in target)) {
        return { ok: false, reason: "control_not_found_or_not_fillable" };
      }
      target.focus();
      target.value = value;
      target.dispatchEvent(new Event("input", { bubbles: true }));
      target.dispatchEvent(new Event("change", { bubbles: true }));
      const form = target.closest("form");
      if (form) {
        form.requestSubmit ? form.requestSubmit() : form.submit();
        return { ok: true, reason: "submitted_form" };
      }
      target.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", bubbles: true }));
      target.dispatchEvent(new KeyboardEvent("keyup", { key: "Enter", code: "Enter", bubbles: true }));
      return { ok: true, reason: "pressed_enter" };
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
  const ok =
    enoughContent &&
    !hasZeroResults &&
    domainOk;
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
            : domain === "video" && !isVideoPage(observation.url)
              ? "not_on_video_page_yet"
          : "insufficient_task_match",
    hits,
    domain,
    hasZeroResults,
    hasSearchResultPage,
    isGithubRepoPage,
    hasGithubRepoChrome,
    isVideoPage: isVideoPage(observation.url),
    url: observation.url,
    title: observation.title
  };
}

async function monitorAndContinue(tabId, payload, result) {
  const attemptedUrls = new Set();
  const followUpUrls = collectFollowUpUrls(result);
  const observations = [];

  for (let step = 1; step <= MAX_MONITOR_STEPS; step += 1) {
    await sleep(MONITOR_DELAY_MS);
    const observation = await observeTab(tabId);
    const verdict = scoreObservation(payload.goal, result, observation);
    observations.push({ step, verdict, url: observation.url, title: observation.title });
    if (verdict.ok) {
      return { ok: true, status: "satisfied", observations, finalUrl: observation.url };
    }

    const dynamicUrls = deriveFollowUpUrls(payload.goal, observation, verdict);
    const pageActions = derivePageActions(payload.goal, observation, verdict);
    const nextAction = pageActions.find((action) => !attemptedUrls.has(`action:${JSON.stringify(action)}`));
    if (nextAction) {
      attemptedUrls.add(`action:${JSON.stringify(nextAction)}`);
      const actionResult = await executePageAction(tabId, nextAction);
      observations[observations.length - 1].pageAction = { action: nextAction, result: actionResult };
      await chrome.storage.local.set({
        agentStatus: "monitoring",
        monitorMessage: `页面未满足任务，正在执行页面动作：${nextAction.reason}`,
        monitorObservations: observations
      });
      continue;
    }
    const candidates = [...dynamicUrls, ...followUpUrls];
    const nextUrl = candidates.find((url) => !attemptedUrls.has(url) && url !== observation.url);
    if (!nextUrl) {
      return { ok: false, status: "needs_human_review", observations, finalUrl: observation.url };
    }

    attemptedUrls.add(nextUrl);
    await chrome.storage.local.set({
      agentStatus: "monitoring",
      monitorMessage: `页面未满足任务，继续打开：${nextUrl}`,
      monitorObservations: observations
    });
    await chrome.tabs.update(tabId, { url: nextUrl });
  }

  const lastObservation = observations[observations.length - 1];
  return { ok: false, status: "max_monitor_steps_reached", observations, finalUrl: lastObservation?.url || "" };
}

async function controlBrowser(tabId, payload) {
  await chrome.storage.local.set({
    agentStatus: "running",
    agentError: "",
    lastResult: null,
    finalUrl: "",
    monitorMessage: "",
    monitorObservations: []
  });

  await chrome.tabs.update(tabId, { url: normalizeUrl(payload.url) });

  const response = await fetch(`${API_BASE}/api/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    throw new Error(data.error || "请求失败");
  }

  const finalUrl = findFinalUrl(data.result);
  if (finalUrl) {
    await chrome.tabs.update(tabId, { url: finalUrl });
  }

  await chrome.storage.local.set({
    agentStatus: "monitoring",
    monitorMessage: "正在监视页面是否满足任务要求",
    lastResult: data.result,
    finalUrl: finalUrl || ""
  });
  const monitor = await monitorAndContinue(tabId, payload, data.result);

  await chrome.storage.local.set({
    agentStatus: monitor.ok ? "done" : "needs_review",
    agentError: "",
    lastResult: data.result,
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

    controlBrowser(message.tabId, message.payload).catch(async (error) => {
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
    deriveFollowUpUrls,
    derivePageActions,
    inferTaskDomain,
    isSearchResultPage,
    isShoppingEvidencePage,
    isVideoEvidencePage,
    scoreObservation
  };
}
