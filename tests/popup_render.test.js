const assert = require('assert');
const popup = require('../chrome_extension/popup.js');

const html = popup.renderAgentResult(
  {
    ok: true,
    goal: '推荐降噪耳机',
    workflow: { domain: 'shopping' },
    memory: { evidence: [{}, {}, {}] },
    steps: [{
      action: 'type_text',
      ok: true,
      detail: {
        url: 'https://www.bing.com/search?q=WH-CH720N',
        fields: {
          evidence_stage: 'candidate_pool',
          submit_after_type: { ok: true, method: 'press_enter' }
        }
      }
    }, {
      action: 'collect_links',
      ok: false,
      failure_type: 'recognition_failure',
      detail: {
        url: 'https://github.com/search?q=browser+agent',
        error: 'no_links_collected',
        fields: {
          evidence_stage: 'repo_candidates'
        }
      }
    }],
    failure_analysis: [
      { failure_type: 'recognition_failure', count: 1, latest_example: { action: 'collect_links', error: 'no_links_collected' } }
    ],
    report: {
      summary: '完成耳机推荐调研',
      reasoning_outline: ['先看预算', '再看音质和降噪'],
      requirement_progression: [
        { requirement_slot: 'candidate_pool', status: 'satisfied', latest_action: 'collect_links', latest_url: 'https://www.bing.com/search?q=WH-CH720N', evidence_summary: 'collected 6 visible candidates' },
        { requirement_slot: 'comparative_reviews', status: 'partial', latest_action: 'type_text', evidence_summary: '准备进入评测页补充优缺点' }
      ],
      evidence_plan: [{ evidence_hint: 'WH-CH720N W820NB 对比', purpose: '型号对比', source: 'shopping' }],
      search_plan: [{ query: 'WH-CH720N W820NB 对比', purpose: '型号对比' }],
      recommendations: [{ name: 'Sony WH-CH720N', url: 'https://www.whathifi.com/reviews/sony-wh-ch720n', score: 53.6, reason: '价格和降噪均衡' }],
      comparison_matrix: [{ name: 'Sony WH-CH720N', url: 'https://www.whathifi.com/reviews/sony-wh-ch720n', score: 53.6, score_reasons: ['review evidence'], price_signal: '1000元以内', snippet: 'review ANC comfort' }],
      failure_analysis: [{ failure_type: 'recognition_failure', count: 1, latest_example: { action: 'collect_links', error: 'no_links_collected' } }],
      multimodal_notes: [{ provider: 'gemini', status: 'unavailable', reason: 'vision_api_key_missing_or_provider_disabled' }],
      uncertainties: ['价格会随平台促销波动'],
      next_actions: ['打开商品页确认实时价格']
    }
  },
  '任务页面已满足要求',
  [{
    url: 'https://www.whathifi.com/reviews/sony-wh-ch720n',
    title: 'Sony review',
    verdict: { ok: true, reason: 'page_matches_task' },
    pageAction: { action: { type: 'fill_and_submit', reason: 'fill_visible_search_box' }, result: { ok: true, reason: 'submitted_form' } }
  }],
  [
    { level: 'info', text: '任务理解：完成耳机推荐调研' },
    { level: 'info', text: '动作：type_text (candidate_pool)，自动提交：press_enter' }
  ]
);

assert(html.includes('任务摘要'));
assert(html.includes('Agent Streaming'));
assert(html.includes('任务理解：完成耳机推荐调研'));
assert(html.includes('动作依据'));
assert(html.includes('需求推进'));
assert(html.includes('证据提示'));
assert(html.includes('WH-CH720N W820NB 对比'));
assert(html.includes('失败分析'));
assert(html.includes('recognition_failure'));
assert(html.includes('candidate_pool'));
assert(html.includes('collect_links'));
assert(html.includes('推荐与候选'));
assert(html.includes('对比证据'));
assert(html.includes('多模态状态'));
assert(html.includes('浏览器监视'));
assert(html.includes('页面动作'));
assert(html.includes('自动提交'));
assert(html.includes('失败类型'));
assert(html.includes('press_enter'));
assert(html.includes('Score 53.6'));
assert(html.includes('review evidence'));
assert(html.includes('Sony WH-CH720N'));
assert(html.includes('vision_api_key_missing_or_provider_disabled'));
assert(!html.includes('<script>'));
assert.equal(popup.normalizeUrl('example.com'), 'https://example.com');
assert.equal(popup.normalizeApiBase('http://127.0.0.1:8000///'), 'http://127.0.0.1:8000');
assert.equal(popup.normalizeApiBase('127.0.0.1:8000'), 'http://127.0.0.1:8000');
assert.equal(popup.normalizeApiBase('api.example.com/v1'), 'https://api.example.com/v1');
assert.equal(popup.escapeHtml('<img src=x onerror=1>'), '&lt;img src=x onerror=1&gt;');
assert.equal(popup.scoreBadge({ score: 9 }), '<span class="score">Score 9</span>');

const videoHtml = popup.renderAgentResult({
  ok: true,
  workflow: { domain: 'video' },
  memory: { evidence: [] },
  report: {
    summary: '视频已整理',
    video_digest: {
      title: 'CLIP 多模态教程',
      url: 'https://www.bilibili.com/video/BV1XZR9ByEV2/',
      visible_transcript: 'CLIP 连接图像和文本表示',
      screenshot_path: 'runs/screenshots/n5.png'
    },
    multimodal_notes: [{ provider: 'gemini', status: 'planned', purpose: '截图视觉理解' }]
  }
});
assert(videoHtml.includes('视频整理'));
assert(videoHtml.includes('CLIP 多模态教程'));
assert(videoHtml.includes('runs/screenshots/n5.png'));

const needsReviewHtml = popup.renderAgentResult(
  {
    ok: false,
    workflow: { domain: 'github' },
    memory: { evidence: [] },
    report: {
      summary: '候选仓库抽取不足',
      next_actions: ['直接打开一个仓库候选，再继续比较 stars、README 和最近更新。'],
      uncertainties: ['当前搜索结果没有提供稳定的仓库候选。']
    }
  },
  '监视后仍未确认满足任务要求',
  [{
    url: 'https://github.com',
    title: 'GitHub',
    verdict: { ok: false, reason: 'not_on_repository_page_yet' }
  }]
);
assert(needsReviewHtml.includes('需要你接手一下'));
assert(needsReviewHtml.includes('not_on_repository_page_yet'));
assert(needsReviewHtml.includes('直接打开一个仓库候选'));
assert(needsReviewHtml.includes('当前停留页面'));

console.log('popup render tests passed');
