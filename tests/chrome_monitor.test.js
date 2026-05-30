const assert = require('assert');
const monitor = require('../chrome_extension/background.js');

function repeated(text) {
  return `${text} `.repeat(40);
}

const shoppingResult = {
  workflow: { domain: 'shopping' },
  report: {
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
assert.equal(shoppingReview.ok, true);

const shoppingFollowUps = monitor.collectFollowUpUrls(shoppingResult);
assert(shoppingFollowUps.includes('https://www.whathifi.com/reviews/sony-wh-ch720n'));
assert(shoppingFollowUps.includes('https://www.soundcore.com/products/space-q45-a3040011'));

const videoResult = {
  workflow: { domain: 'video' },
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

const derivedVideoUrls = monitor.deriveFollowUpUrls('整理CLIP多模态教程视频', {
  title: 'Search',
  url: 'https://www.bing.com/videos/search?q=clip',
  text: repeated('CLIP 多模态'),
  links: [
    { text: 'CLIP 多模态模型入门教程 bilibili', url: 'https://www.bilibili.com/video/BV1XZR9ByEV2/' },
    { text: 'Unrelated article', url: 'https://example.com/article' }
  ]
}, videoSearch);
assert.deepEqual(derivedVideoUrls, ['https://www.bilibili.com/video/BV1XZR9ByEV2/']);

const searchBoxActions = monitor.derivePageActions('帮我搜索 browser-use GitHub 仓库', {
  title: 'Bing',
  url: 'https://www.bing.com/',
  text: repeated('Bing search homepage'),
  links: [],
  controls: [
    { index: 3, tag: 'input', type: 'search', role: '', label: '搜索', visible: true, disabled: false }
  ]
}, { ok: false, domain: 'general', reason: 'insufficient_task_match' });
assert.equal(searchBoxActions[0].type, 'fill_and_submit');
assert.equal(searchBoxActions[0].controlIndex, 3);
assert(searchBoxActions[0].value.includes('browser-use'));

const githubActions = monitor.derivePageActions('搜索 browser-use 开源项目', {
  title: 'GitHub Search',
  url: 'https://github.com/search?q=browser-use',
  text: repeated('repository search results'),
  links: [
    { text: 'browser-use/browser-use', url: 'https://github.com/browser-use/browser-use' }
  ],
  controls: []
}, { ok: false, domain: 'github', reason: 'not_on_repository_page_yet' });
assert.deepEqual(githubActions[0], {
  type: 'click_link',
  url: 'https://github.com/browser-use/browser-use',
  reason: 'open_repository_candidate'
});

console.log('chrome monitor tests passed');
