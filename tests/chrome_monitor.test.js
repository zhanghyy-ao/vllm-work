const assert = require('assert');
const monitor = require('../chrome_extension/background.js');

function repeated(text) {
  return `${text} `.repeat(40);
}

const shoppingResult = {
  workflow: { domain: 'shopping' },
  report: {
    requirement_progression: [
      { requirement_slot: 'candidate_pool', status: 'satisfied' },
      { requirement_slot: 'comparative_reviews', status: 'partial' },
      { requirement_slot: 'user_comments', status: 'missing' },
      { requirement_slot: 'video_reviews', status: 'missing' },
      { requirement_slot: 'marketplace_pages', status: 'missing' }
    ],
    recommendations: [{ url: 'https://www.whathifi.com/reviews/sony-wh-ch720n' }],
    candidates: [{ url: 'https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-vs-sony-wh-ch720n-wireless/34852/38908' }],
    source_readings: [{ url: 'https://www.soundcore.com/products/space-q45-a3040011' }],
    comparison_matrix: [{ url: 'https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus' }]
  },
  llm: { plan: { query: 'WH-CH720N W820NB Space Q45 降噪耳机 对比 评测' } },
  events: [{ url: 'https://www.bing.com/search?q=headphones' }]
};

const shoppingSearch = monitor.scoreObservation('推荐降噪耳机', shoppingResult, {
  title: 'Bing Search',
  url: 'https://www.bing.com/search?q=headphones',
  text: repeated('Sony WH-CH720N 降噪耳机 评测'),
  links: []
});
assert.equal(shoppingSearch.ok, false);
assert.equal(shoppingSearch.reason, 'shopping_search_page_needs_product_or_review_page');

const shoppingReview = monitor.scoreObservation('推荐降噪耳机', shoppingResult, {
  title: 'Sony WH-CH720N review',
  url: 'https://www.whathifi.com/reviews/sony-wh-ch720n',
  text: repeated('Sony WH-CH720N headphones review ANC price comfort pros cons'),
  links: []
});
assert.equal(shoppingReview.ok, false);
assert.equal(shoppingReview.reason, 'shopping_requirement_coverage_incomplete');

const shoppingSatisfiedResult = {
  ...shoppingResult,
  report: {
    ...shoppingResult.report,
    requirement_progression: [
      { requirement_slot: 'candidate_pool', status: 'satisfied' },
      { requirement_slot: 'comparative_reviews', status: 'satisfied' },
      { requirement_slot: 'user_comments', status: 'partial' },
      { requirement_slot: 'video_reviews', status: 'missing' },
      { requirement_slot: 'marketplace_pages', status: 'partial' }
    ]
  }
};
const shoppingSatisfiedReview = monitor.scoreObservation('推荐降噪耳机', shoppingSatisfiedResult, {
  title: 'Sony WH-CH720N review',
  url: 'https://www.whathifi.com/reviews/sony-wh-ch720n',
  text: repeated('Sony WH-CH720N headphones review ANC price comfort pros cons'),
  links: []
});
assert.equal(shoppingSatisfiedReview.ok, true);

const shoppingFollowUps = monitor.collectFollowUpUrls(shoppingResult);
assert(shoppingFollowUps.includes('https://www.whathifi.com/reviews/sony-wh-ch720n'));
assert(shoppingFollowUps.includes('https://www.soundcore.com/products/space-q45-a3040011'));
assert.equal(shoppingFollowUps.includes('https://www.bing.com/search?q=headphones'), false);

const shoppingFollowUpsFilterLowQuality = monitor.collectFollowUpUrls({
  goal: '推荐降噪耳机',
  workflow: { domain: 'shopping' },
  report: {
    requirement_progression: [
      { requirement_slot: 'candidate_pool', status: 'satisfied' },
      { requirement_slot: 'comparative_reviews', status: 'satisfied' },
      { requirement_slot: 'marketplace_pages', status: 'missing' },
      { requirement_slot: 'user_comments', status: 'missing' }
    ],
    candidates: [
      { url: 'https://gitcode.csdn.net/6a0e707c10ee7a33f274126c.html', title: '耳机降噪推荐 AtomGit开源社区' },
      { url: 'https://www.soundguys.com/sony-wh-ch720n-review-12345/' },
      { url: 'https://www.soundcore.com/products/space-q45-a3040011' },
      { url: 'https://www.reddit.com/r/headphones/comments/abc123/space_q45/' }
    ]
  }
});
assert.equal(shoppingFollowUpsFilterLowQuality.includes('https://gitcode.csdn.net/6a0e707c10ee7a33f274126c.html'), false);
assert.equal(shoppingFollowUpsFilterLowQuality[0], 'https://www.soundcore.com/products/space-q45-a3040011');
assert.equal(shoppingFollowUpsFilterLowQuality[1], 'https://www.reddit.com/r/headphones/comments/abc123/space_q45/');

const videoResult = {
  workflow: { domain: 'video' },
  report: {
    requirement_progression: [
      { requirement_slot: 'video_candidates', status: 'satisfied' },
      { requirement_slot: 'transcript_notes', status: 'partial' }
    ]
  },
  llm: { plan: { query: 'CLIP 多模态 教程 视频' } }
};
const videoSearch = monitor.scoreObservation('整理CLIP多模态教程视频', videoResult, {
  title: 'Bing Videos',
  url: 'https://www.bing.com/videos/search?q=clip',
  text: repeated('CLIP 多模态 教程 视频'),
  links: []
});
assert.equal(videoSearch.ok, false);
assert.equal(videoSearch.reason, 'not_on_video_page_yet');

const videoPage = monitor.scoreObservation('整理CLIP多模态教程视频', videoResult, {
  title: 'CLIP tutorial - Bilibili',
  url: 'https://www.bilibili.com/video/BV1XZR9ByEV2/',
  text: repeated('CLIP 多模态 模型 教程 视频 简介 播放 字幕'),
  links: []
});
assert.equal(videoPage.ok, true);

const searchBoxActions = monitor.derivePageActions('帮我搜索 browser-use GitHub 仓库', {
  title: 'Bing',
  url: 'https://www.bing.com/',
  text: repeated('Bing search homepage'),
  links: [],
  controls: [
    { index: 3, tag: 'input', type: 'search', role: '', label: '搜索', visible: true, disabled: false }
  ]
}, { ok: false, domain: 'general', reason: 'insufficient_task_match' }, { workflow: { domain: 'general' } });
assert.equal(searchBoxActions[0].type, 'fill_and_submit');
assert.equal(searchBoxActions[0].controlIndex, 3);
assert(searchBoxActions[0].value.includes('browser-use'));

const githubActions = monitor.derivePageActions('搜索 browser-use 开源项目', {
  title: 'GitHub Search',
  url: 'https://github.com/search?q=browser-use',
  text: repeated('repository search results'),
  links: [
    { index: 0, text: 'browser-use/browser-use', url: 'https://github.com/browser-use/browser-use' }
  ],
  controls: []
}, { ok: false, domain: 'github', reason: 'not_on_repository_page_yet' }, { workflow: { domain: 'github' } });
assert.deepEqual(githubActions[0], {
  type: 'click_link',
  linkIndex: 0,
  url: 'https://github.com/browser-use/browser-use',
  reason: 'open_visible_candidate'
});

const shoppingActions = monitor.derivePageActions('推荐降噪耳机', {
  title: 'Search results',
  url: 'https://www.bing.com/search?q=headphones',
  text: repeated('headphone review search results'),
  links: [
    { index: 0, text: 'Sony WH-CH720N review', url: 'https://www.whathifi.com/reviews/sony-wh-ch720n' },
    { index: 1, text: 'Audio noise reduction utility', url: 'https://example.com/noise-removal' }
  ],
  controls: []
}, { ok: false, domain: 'shopping', reason: 'shopping_search_page_needs_product_or_review_page' }, { workflow: { domain: 'shopping' } });
assert.deepEqual(shoppingActions[0], {
  type: 'click_link',
  linkIndex: 0,
  url: 'https://www.whathifi.com/reviews/sony-wh-ch720n',
  reason: 'open_visible_candidate'
});

const shoppingSearchPrefersCandidate = monitor.derivePageActions('推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论', {
  title: 'Bing search',
  url: 'https://www.bing.com/search?q=headphones',
  text: repeated('Sony WH-CH720N review recommendation'),
  links: [
    { index: 0, text: '视频', url: 'https://www.bing.com/videos/search?q=headphones' },
    { index: 1, text: '中证1000指数', url: 'https://vip.stock.finance.sina.com.cn/corp/go.php/vII_NewestComponent/indexid/000852.phtml' },
    { index: 0, text: 'Sony WH-CH720N review', url: 'https://www.whathifi.com/reviews/sony-wh-ch720n' }
  ],
  controls: [
    { index: 3, tag: 'input', type: 'search', role: '', label: '搜索', visible: true, disabled: false }
  ]
}, { ok: false, domain: 'shopping', reason: 'shopping_search_page_needs_product_or_review_page' }, {
  workflow: { domain: 'shopping' },
  report: {
    candidates: [{ url: 'https://www.whathifi.com/reviews/sony-wh-ch720n' }]
  }
});
assert.equal(shoppingSearchPrefersCandidate[0].type, 'click_link');
assert.equal(shoppingSearchPrefersCandidate[0].url, 'https://www.whathifi.com/reviews/sony-wh-ch720n');
assert.equal(shoppingSearchPrefersCandidate[0].reason, 'open_report_candidate');

const inPageReviewActions = monitor.derivePageActions('推荐降噪耳机', {
  title: 'Sony WH-CH720N review',
  url: 'https://www.whathifi.com/reviews/sony-wh-ch720n',
  text: repeated('Sony WH-CH720N headphones review ANC price comfort pros cons'),
  links: [
    { index: 0, text: 'next review', url: 'https://example.com/other-review' }
  ],
  controls: []
}, { ok: false, domain: 'shopping', reason: 'shopping_requirement_coverage_incomplete' }, { workflow: { domain: 'shopping' } });
assert.equal(inPageReviewActions.length, 0);

const inPageReviewWithSearchBox = monitor.derivePageActions('推荐降噪耳机', {
  title: '知乎专栏',
  url: 'https://zhuanlan.zhihu.com/p/1929856826205280133',
  text: repeated('Sony WH-CH720N 降噪耳机 推荐 对比'),
  links: [
    { index: 0, text: 'next review', url: 'https://example.com/other-review' }
  ],
  controls: [
    { index: 2, tag: 'input', type: 'search', role: '', label: '站内搜索', visible: true, disabled: false }
  ]
}, { ok: false, domain: 'shopping', reason: 'shopping_requirement_coverage_incomplete' }, { workflow: { domain: 'shopping' } });
assert.equal(inPageReviewWithSearchBox.length, 0);

const blockedReviewFallsBackToAlternativeCandidate = monitor.derivePageActions('推荐降噪耳机', {
  title: '知乎',
  url: 'https://zhuanlan.zhihu.com/p/1929856826205280133',
  text: repeated('您当前请求存在异常 暂时限制本次访问 登录后查看'),
  links: [],
  controls: []
}, { ok: false, domain: 'shopping', reason: 'shopping_requirement_coverage_incomplete' }, {
  workflow: { domain: 'shopping' },
  report: {
    candidates: [{ url: 'https://www.whathifi.com/reviews/sony-wh-ch720n' }]
  }
});
assert.equal(blockedReviewFallsBackToAlternativeCandidate[0].type, 'click_link');
assert.equal(blockedReviewFallsBackToAlternativeCandidate[0].reason, 'open_report_candidate');

const shoppingSearchReturnsMultipleCandidatesBeforeResearching = monitor.derivePageActions('推荐降噪耳机', {
  title: 'Search results',
  url: 'https://www.bing.com/search?q=headphones',
  text: repeated('headphone review search results'),
  links: [
    { index: 0, text: 'Sony WH-CH720N review', url: 'https://www.whathifi.com/reviews/sony-wh-ch720n' },
    { index: 1, text: 'Soundcore Space Q45 review', url: 'https://www.rtings.com/headphones/reviews/anker/soundcore-space-q45-wireless' },
    { index: 2, text: 'Edifier W820NB review', url: 'https://www.soundguys.com/edifier-w820nb-review-123456/' }
  ],
  controls: [
    { index: 3, tag: 'input', type: 'search', role: '', label: '搜索', visible: true, disabled: false }
  ]
}, { ok: false, domain: 'shopping', reason: 'shopping_search_page_needs_product_or_review_page' }, { workflow: { domain: 'shopping' } });
assert.equal(shoppingSearchReturnsMultipleCandidatesBeforeResearching[0].type, 'click_link');
assert.equal(shoppingSearchReturnsMultipleCandidatesBeforeResearching[1].type, 'click_link');
assert.equal(shoppingSearchReturnsMultipleCandidatesBeforeResearching.some((item) => item.reason === 'fill_visible_search_box'), false);

const lowQualitySearchResultIsSkipped = monitor.derivePageActions('推荐降噪耳机', {
  title: 'Search results',
  url: 'https://www.bing.com/search?q=headphones',
  text: repeated('headphone review search results'),
  links: [
    { index: 0, text: '耳机降噪推荐 AtomGit开源社区', url: 'https://gitcode.csdn.net/6a0e707c10ee7a33f274126c.html' },
    { index: 1, text: 'Sony WH-CH720N review', url: 'https://www.whathifi.com/reviews/sony-wh-ch720n' }
  ],
  controls: []
}, { ok: false, domain: 'shopping', reason: 'shopping_search_page_needs_product_or_review_page' }, { workflow: { domain: 'shopping' } });
assert.equal(lowQualitySearchResultIsSkipped[0].url, 'https://www.whathifi.com/reviews/sony-wh-ch720n');

console.log('chrome monitor tests passed');
