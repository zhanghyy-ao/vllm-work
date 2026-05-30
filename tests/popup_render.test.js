const assert = require('assert');
const popup = require('../chrome_extension/popup.js');

const html = popup.renderAgentResult(
  {
    ok: true,
    goal: '推荐降噪耳机',
    workflow: { domain: 'shopping' },
    memory: { evidence: [{}, {}, {}] },
    report: {
      summary: '完成耳机推荐调研',
      reasoning_outline: ['先看预算', '再看音质和降噪'],
      search_plan: [{ query: 'WH-CH720N W820NB 对比', purpose: '型号对比' }],
      recommendations: [{ name: 'Sony WH-CH720N', url: 'https://www.whathifi.com/reviews/sony-wh-ch720n', score: 53.6, reason: '价格和降噪均衡' }],
      comparison_matrix: [{ name: 'Sony WH-CH720N', url: 'https://www.whathifi.com/reviews/sony-wh-ch720n', score: 53.6, score_reasons: ['review evidence'], price_signal: '1000元以内', snippet: 'review ANC comfort' }],
      multimodal_notes: [{ provider: 'gemini', status: 'unavailable', reason: 'gemini_api_key_missing_or_provider_disabled' }],
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
  }]
);

assert(html.includes('任务摘要'));
assert(html.includes('可见规划'));
assert(html.includes('推荐与候选'));
assert(html.includes('对比证据'));
assert(html.includes('多模态状态'));
assert(html.includes('浏览器监视'));
assert(html.includes('页面动作'));
assert(html.includes('Score 53.6'));
assert(html.includes('review evidence'));
assert(html.includes('Sony WH-CH720N'));
assert(html.includes('gemini_api_key_missing_or_provider_disabled'));
assert(!html.includes('<script>'));
assert.equal(popup.normalizeUrl('example.com'), 'https://example.com');
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

console.log('popup render tests passed');
