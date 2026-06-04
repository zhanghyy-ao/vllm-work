# Chrome Extension Real Browser Control Test - 2026-06-04

## Scope

Validate a visible Chrome extension session end to end: extension load, direct tab control, real shopping-task execution, screenshots, and a broader market comparison.

## Backend Config

- provider/model: `openai_compatible / gpt-5.5`
- api base: `https://synai996.space/v1`
- vision provider/model: `openai_compatible / gpt-5.5`
- vision api base: `https://synai996.space/v1`
- planner/report max tokens: `1000 / 1600`
- multimodal planning: `True`
- visual precheck: `False`
- key configured: `True`

## Certification Summary

- visible Chrome extension load: `PASS (jmcjmbaapknjfofpikfebojbgaemoafk)`
- direct tab control from extension background: `PASS`
- extension monitor loop and follow-up navigation: `PASS`
- full LLM planning and evidence extraction: `PASS`
- diagnostic: `none`

## Visible Flow Evidence

- extension id: `jmcjmbaapknjfofpikfebojbgaemoafk`
- background worker: `chrome-extension://jmcjmbaapknjfofpikfebojbgaemoafk/background.js`
- direct browser control observed URL: `https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=E69570FFC62B450684175A23CCC1D15A`
- direct browser control title: `1000元以内 降噪耳机 推荐 通勤 办公 - 搜索`
- agent storage status: `done`
- agent final URL: `https://cn.bing.com/videos/search?q=1000%e5%85%83%e4%bb%a5%e5%86%85%e9%80%82%e5%90%88%e9%80%9a%e5%8b%a4%e5%92%8c%e5%8a%9e%e5%85%ac%e7%9a%84%e9%99%8d%e5%99%aa%e8%80%b3%e6%9c%ba%ef%bc%8c%e9%9c%80%e8%a6%81%e6%af%94%e8%be%83%e5%95%86%e5%9f%8e%e5%95%86%e5%93%81%e9%a1%b5%e3%80%81%e4%b8%93%e4%b8%9a%e6%b5%8b%e8%af%84%e3%80%81%e7%94%a8%e6%88%b7%e8%af%84%e8%ae%ba%e5%b7%ae%e8%af%84%e3%80%81%e8%a7%86%e9%a2%91%e6%b5%8b%e8%af%84%e8%af%84%e8%ae%ba%e5%90%8e%e7%bb%99%e5%87%ba%e7%bb%93%e8%ae%ba&FORM=HDRSC3`
- current visible URL after agent run: `https://cn.bing.com/videos/search?q=1000%e5%85%83%e4%bb%a5%e5%86%85%e9%80%82%e5%90%88%e9%80%9a%e5%8b%a4%e5%92%8c%e5%8a%9e%e5%85%ac%e7%9a%84%e9%99%8d%e5%99%aa%e8%80%b3%e6%9c%ba%ef%bc%8c%e9%9c%80%e8%a6%81%e6%af%94%e8%be%83%e5%95%86%e5%9f%8e%e5%95%86%e5%93%81%e9%a1%b5%e3%80%81%e4%b8%93%e4%b8%9a%e6%b5%8b%e8%af%84%e3%80%81%e7%94%a8%e6%88%b7%e8%af%84%e8%ae%ba%e5%b7%ae%e8%af%84%e3%80%81%e8%a7%86%e9%a2%91%e6%b5%8b%e8%af%84%e8%af%84%e8%ae%ba%e5%90%8e%e7%bb%99%e5%87%ba%e7%bb%93%e8%ae%ba&FORM=HDRSC3`
- current visible title after agent run: `1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论 - 搜索 视频`
- latest run goal: `推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论`
- latest run summary: `Workflow 'shopping_workflow' completed for '推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论'. Collected 5 candidate links and 9 evidence items.`
- latest run events/steps: `3 / 3`
- latest run evidence items: `9`
- latest run recommendations: `3`

## Screenflow Screenshots

- 01-bing-home: `/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-01-bing-home.png`
- 02-direct-control-search-page: `/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-02-direct-control-search-page.png`
- 03-agent-launched: `/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-03-agent-launched.png`
- status-running-1: `/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-status-running-1.png`
- status-monitoring-37: `/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-status-monitoring-37.png`
- status-done-40: `/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-status-done-40.png`
- 04-agent-final-state: `/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-04-agent-final-state.png`

## Agent Poll History

- poll 1: status=`running` title=`Loading https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=E69570FFC62B450684175A23CCC1D15A` message=``
- poll 2: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 3: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 4: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 5: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 6: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 7: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 8: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 9: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 10: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 11: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 12: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 13: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 14: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 15: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 16: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 17: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 18: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 19: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 20: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 21: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 22: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 23: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 24: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 25: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 26: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 27: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 28: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 29: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 30: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 31: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 32: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 33: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 34: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 35: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 36: status=`running` title=`1000元以内 降噪耳机 推荐 通勤 办公 - 搜索` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=``
- poll 37: status=`monitoring` title=`Loading https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5` message=`正在监视页面是否满足任务要求`
- poll 38: status=`monitoring` title=`Loading https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85%E9%80%82%E5%90%88%E9%80%9A%E5%8B%A4%E5%92%8C%E5%8A%9E%E5%85%AC%E7%9A%84%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA%EF%BC%8C%E9%9C%80%E8%A6%81%E6%AF%94%E8%BE%83%E5%95%86%E5%9F%8E%E5%95%86%E5%93%81%E9%A1%B5%E3%80%81%E4%B8%93%E4%B8%9A%E6%B5%8B%E8%AF%84%E3%80%81%E7%94%A8%E6%88%B7%E8%AF%84%E8%AE%BA%E5%B7%AE%E8%AF%84%E3%80%81%E8%A7%86%E9%A2%91%E6%B5%8B%E8%AF%84%E8%AF%84%E8%AE%BA%E5%90%8E%E7%BB%99%E5%87%BA%E7%BB%93%E8%AE%BA&qs=n&form=QBRE&sp=-1&lq=0&pq=&sc=0-0&sk=&cvid=15938C2D9D4644FAA4F8C9417A67FFCB` url=`https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB&rdr=1&rdrig=749392FD78A94236BC144A23A9DFA12B` message=`页面未满足任务，正在执行页面动作：fill_visible_search_box`
- poll 39: status=`monitoring` title=`1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论 - 搜索 视频` url=`https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85%E9%80%82%E5%90%88%E9%80%9A%E5%8B%A4%E5%92%8C%E5%8A%9E%E5%85%AC%E7%9A%84%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA%EF%BC%8C%E9%9C%80%E8%A6%81%E6%AF%94%E8%BE%83%E5%95%86%E5%9F%8E%E5%95%86%E5%93%81%E9%A1%B5%E3%80%81%E4%B8%93%E4%B8%9A%E6%B5%8B%E8%AF%84%E3%80%81%E7%94%A8%E6%88%B7%E8%AF%84%E8%AE%BA%E5%B7%AE%E8%AF%84%E3%80%81%E8%A7%86%E9%A2%91%E6%B5%8B%E8%AF%84%E8%AF%84%E8%AE%BA%E5%90%8E%E7%BB%99%E5%87%BA%E7%BB%93%E8%AE%BA&qs=n&form=QBRE&sp=-1&lq=0&pq=&sc=0-0&sk=&cvid=15938C2D9D4644FAA4F8C9417A67FFCB` message=`页面未满足任务，继续打开：https://cn.bing.com/videos/search?q=1000%e5%85%83%e4%bb%a5%e5%86%85%e9%80%82%e5%90%88%e9%80%9a%e5%8b%a4%e5%92%8c%e5%8a%9e%e5%85%ac%e7%9a%84%e9%99%8d%e5%99%aa%e8%80%b3%e6%9c%ba%ef%bc%8c%e9%9c%80%e8%a6%81%e6%af%94%e8%be%83%e5%95%86%e5%9f%8e%e5%95%86%e5%93%81%e9%a1%b5%e3%80%81%e4%b8%93%e4%b8%9a%e6%b5%8b%e8%af%84%e3%80%81%e7%94%a8%e6%88%b7%e8%af%84%e8%ae%ba%e5%b7%ae%e8%af%84%e3%80%81%e8%a7%86%e9%a2%91%e6%b5%8b%e8%af%84%e8%af%84%e8%ae%ba%e5%90%8e%e7%bb%99%e5%87%ba%e7%bb%93%e8%ae%ba&FORM=HDRSC3`
- poll 40: status=`done` title=`1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论 - 搜索 视频` url=`https://cn.bing.com/videos/search?q=1000%e5%85%83%e4%bb%a5%e5%86%85%e9%80%82%e5%90%88%e9%80%9a%e5%8b%a4%e5%92%8c%e5%8a%9e%e5%85%ac%e7%9a%84%e9%99%8d%e5%99%aa%e8%80%b3%e6%9c%ba%ef%bc%8c%e9%9c%80%e8%a6%81%e6%af%94%e8%be%83%e5%95%86%e5%9f%8e%e5%95%86%e5%93%81%e9%a1%b5%e3%80%81%e4%b8%93%e4%b8%9a%e6%b5%8b%e8%af%84%e3%80%81%e7%94%a8%e6%88%b7%e8%af%84%e8%ae%ba%e5%b7%ae%e8%af%84%e3%80%81%e8%a7%86%e9%a2%91%e6%b5%8b%e8%af%84%e8%af%84%e8%ae%ba%e5%90%8e%e7%bb%99%e5%87%ba%e7%bb%93%e8%ae%ba&FORM=HDRSC3` message=`任务页面已满足要求`

## Diagnosis

- The extension is now verified as truly controlling a visible Chrome window, not only producing backend JSON.
- The browser side visibly moved from the Bing home page into a real shopping-search task page and then continued through the extension's monitor loop.
- The latest backend result shows the shopping workflow completed with candidate extraction and evidence collection, so the main blocker has shifted away from the old provider-access problem.
- The remaining work is product quality rather than basic connectivity: better live progress UX, more predictable long-task pacing, and richer cross-site coverage.

## Market Comparison

| Product | Browser Control | Observation | Planning | Reporting | Gap vs This Repo |
| --- | --- | --- | --- | --- | --- |
| This project | Visible Chrome for Testing with unpacked extension, direct tab update, monitor loop, DOM-aware follow-up actions. | URL/title/text/links/controls plus screenshots and multimodal planning hooks. | Observation-driven action loop with evidence checklist and safe action set. | Local latest-run JSON, markdown report, screenshots, traceable evidence. | Still needs tighter live-run progress UX and more predictable long-task convergence. |
| OpenAI Operator | Cloud/hosted browser interaction with strong UI execution and consumer task polish. | Rich multimodal observation with strong grounding. | Closed product loop with strong task completion heuristics. | Good user-facing outcome quality but less local inspectability. | Harder to self-host or inspect internal traces compared with this repo. |
| Anthropic Computer Use | Desktop-style computer control across apps, not only browser tabs. | Screenshot-centric perception with iterative action loop. | General-purpose step-by-step interaction. | Strong demo value, but app-specific audit artifacts depend on host integration. | This repo is narrower in control scope but stronger on local browser-specific artifacts. |
| Browser Use | Playwright/browser automation focused, developer-friendly and scriptable. | DOM-first with browser automation affordances. | Agent planning around browser tasks, usually developer oriented. | Good engineering ergonomics, lighter end-user certification packaging. | This repo now approaches similar explainability, but still needs broader site reliability. |
| Google Project Mariner | Consumer-facing multi-step browser assistance direction. | Strong product-layer UX and task continuity emphasis. | Task-level planning with product polish. | Less open implementation detail for local benchmarking. | This repo remains more inspectable, but less polished in user-facing continuity. |

## Raw Data

```json
{
  "backend_config": {
    "provider": "openai_compatible",
    "model": "gpt-5.5",
    "api_base_url": "https://synai996.space/v1",
    "vision_provider": "openai_compatible",
    "vision_model": "gpt-5.5",
    "vision_api_base_url": "https://synai996.space/v1",
    "planner_max_tokens": 1000,
    "report_max_tokens": 1600,
    "use_multimodal_planning": true,
    "use_visual_precheck": false,
    "api_key_configured": true,
    "vision_api_key_configured": true
  },
  "screenshots": [
    {
      "label": "01-bing-home",
      "path": "/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-01-bing-home.png",
      "url": "https://cn.bing.com/"
    },
    {
      "label": "02-direct-control-search-page",
      "path": "/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-02-direct-control-search-page.png",
      "url": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=E69570FFC62B450684175A23CCC1D15A"
    },
    {
      "label": "03-agent-launched",
      "path": "/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-03-agent-launched.png",
      "url": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=E69570FFC62B450684175A23CCC1D15A"
    },
    {
      "label": "status-running-1",
      "path": "/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-status-running-1.png",
      "url": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC"
    },
    {
      "label": "status-monitoring-37",
      "path": "/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-status-monitoring-37.png",
      "url": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB"
    },
    {
      "label": "status-done-40",
      "path": "/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-status-done-40.png",
      "url": "https://cn.bing.com/videos/search?q=1000%e5%85%83%e4%bb%a5%e5%86%85%e9%80%82%e5%90%88%e9%80%9a%e5%8b%a4%e5%92%8c%e5%8a%9e%e5%85%ac%e7%9a%84%e9%99%8d%e5%99%aa%e8%80%b3%e6%9c%ba%ef%bc%8c%e9%9c%80%e8%a6%81%e6%af%94%e8%be%83%e5%95%86%e5%9f%8e%e5%95%86%e5%93%81%e9%a1%b5%e3%80%81%e4%b8%93%e4%b8%9a%e6%b5%8b%e8%af%84%e3%80%81%e7%94%a8%e6%88%b7%e8%af%84%e8%ae%ba%e5%b7%ae%e8%af%84%e3%80%81%e8%a7%86%e9%a2%91%e6%b5%8b%e8%af%84%e8%af%84%e8%ae%ba%e5%90%8e%e7%bb%99%e5%87%ba%e7%bb%93%e8%ae%ba&FORM=HDRSC3"
    },
    {
      "label": "04-agent-final-state",
      "path": "/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-04-agent-final-state.png",
      "url": "https://cn.bing.com/videos/search?q=1000%e5%85%83%e4%bb%a5%e5%86%85%e9%80%82%e5%90%88%e9%80%9a%e5%8b%a4%e5%92%8c%e5%8a%9e%e5%85%ac%e7%9a%84%e9%99%8d%e5%99%aa%e8%80%b3%e6%9c%ba%ef%bc%8c%e9%9c%80%e8%a6%81%e6%af%94%e8%be%83%e5%95%86%e5%9f%8e%e5%95%86%e5%93%81%e9%a1%b5%e3%80%81%e4%b8%93%e4%b8%9a%e6%b5%8b%e8%af%84%e3%80%81%e7%94%a8%e6%88%b7%e8%af%84%e8%ae%ba%e5%b7%ae%e8%af%84%e3%80%81%e8%a7%86%e9%a2%91%e6%b5%8b%e8%af%84%e8%af%84%e8%ae%ba%e5%90%8e%e7%bb%99%e5%87%ba%e7%bb%93%e8%ae%ba&FORM=HDRSC3"
    }
  ],
  "extension_id": "jmcjmbaapknjfofpikfebojbgaemoafk",
  "background_url": "chrome-extension://jmcjmbaapknjfofpikfebojbgaemoafk/background.js",
  "direct_control": {
    "tabId": 947616177,
    "requestedUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC",
    "extensionId": "jmcjmbaapknjfofpikfebojbgaemoafk",
    "observed_url": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=E69570FFC62B450684175A23CCC1D15A",
    "title": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索",
    "screenshot": "/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-02-direct-control-search-page.png"
  },
  "agent_control": {
    "launch_info": {
      "started": true,
      "tabId": 947616177
    },
    "storage_state": {
      "agentError": "",
      "agentStatus": "done",
      "finalUrl": "https://cn.bing.com/videos/search?q=1000%e5%85%83%e4%bb%a5%e5%86%85%e9%80%82%e5%90%88%e9%80%9a%e5%8b%a4%e5%92%8c%e5%8a%9e%e5%85%ac%e7%9a%84%e9%99%8d%e5%99%aa%e8%80%b3%e6%9c%ba%ef%bc%8c%e9%9c%80%e8%a6%81%e6%af%94%e8%be%83%e5%95%86%e5%9f%8e%e5%95%86%e5%93%81%e9%a1%b5%e3%80%81%e4%b8%93%e4%b8%9a%e6%b5%8b%e8%af%84%e3%80%81%e7%94%a8%e6%88%b7%e8%af%84%e8%ae%ba%e5%b7%ae%e8%af%84%e3%80%81%e8%a7%86%e9%a2%91%e6%b5%8b%e8%af%84%e8%af%84%e8%ae%ba%e5%90%8e%e7%bb%99%e5%87%ba%e7%bb%93%e8%ae%ba&FORM=HDRSC3",
      "lastResult": {
        "agent": {
          "agent_name": "browser-workflow-agent",
          "api_base_url": "https://synai996.space/v1",
          "api_key_configured": true,
          "http_user_agent": "codex-browser-agent/1.0",
          "llm_timeout_sec": 30,
          "model": "gpt-5.5",
          "model_fallbacks": [
            "gpt-5.4",
            "gpt-5.4-mini"
          ],
          "planner_max_tokens": 1000,
          "provider": "openai_compatible",
          "report_max_tokens": 1600,
          "report_retry_max_tokens": 900,
          "use_llm": true,
          "use_multimodal_planning": true,
          "use_visual_precheck": false,
          "vision_api_base_url": "https://synai996.space/v1",
          "vision_api_key_configured": true,
          "vision_model": "gpt-5.5",
          "vision_model_fallbacks": [
            "gpt-5.4",
            "gpt-5.4-mini"
          ],
          "vision_provider": "openai_compatible",
          "vision_timeout_sec": 30
        },
        "events": [
          {
            "input": {
              "attempt": 1,
              "node": {
                "action": "collect_links",
                "depends_on": [],
                "id": "d1",
                "inputs": {
                  "checklist_status": [
                    {
                      "evidence": "尚未收集预算内主流型号和价格线索。",
                      "stage": "candidate_pool",
                      "status": "missing"
                    },
                    {
                      "evidence": "尚未核对商城商品页价格、参数和评价入口。",
                      "stage": "marketplace_pages",
                      "status": "missing"
                    },
                    {
                      "evidence": "尚未收集专业对比评测。",
                      "stage": "comparative_reviews",
                      "status": "missing"
                    },
                    {
                      "evidence": "尚未收集用户差评和佩戴/故障反馈。",
                      "stage": "user_comments",
                      "status": "missing"
                    },
                    {
                      "evidence": "尚未收集视频测评及评论区线索。",
                      "stage": "video_reviews",
                      "status": "missing"
                    }
                  ],
                  "dynamic": true,
                  "evidence_stage": "candidate_pool",
                  "multimodal_planning_used": false,
                  "planner_suggested_action": "search_web",
                  "planner_suggested_rationale": "当前搜索页没有可用结果摘要或可交互元素，需要先用更聚焦的购物/推荐查询建立候选型号池。",
                  "query": "1000元以内 降噪耳机 推荐 通勤 办公 头戴式 入耳式 型号 价格",
                  "rationale": "Progress guard: current page is already a results/search page, so collect visible candidates before issuing another search or wait.",
                  "source": "shopping"
                },
                "instruction": "当前已经到达搜索/结果页，先抽取候选链接或启用垂直候选恢复。",
                "retry_policy": {
                  "max_retries": 2
                },
                "success_criteria": [
                  "action_ok",
                  "evidence_or_fields"
                ],
                "type": "agent_dynamic_guarded"
              }
            },
            "latency_ms": 85,
            "output": {
              "result": {
                "action": "collect_links",
                "error": null,
                "evidence": [
                  {
                    "claim": "Candidate link: RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
                    "confidence": 0.72,
                    "evidence_id": "7a65de7d-fc1c-4652-be3a-550201a657f8",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
                    "support": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison"
                  },
                  {
                    "claim": "Candidate link: What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
                    "confidence": 0.72,
                    "evidence_id": "b44facc5-a624-4354-9e8f-fbee54211cf9",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.whathifi.com/reviews/sony-wh-ch720n",
                    "support": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review"
                  },
                  {
                    "claim": "Candidate link: Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
                    "confidence": 0.72,
                    "evidence_id": "d726928c-df65-4bde-9fae-707f3013374e",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
                    "support": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page"
                  },
                  {
                    "claim": "Candidate link: Soundcore Space Q45 adaptive noise cancelling headphones product page",
                    "confidence": 0.72,
                    "evidence_id": "60900630-ff06-4d65-8570-14034f4307f3",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.soundcore.com/products/space-q45-a3040011",
                    "support": "Soundcore Space Q45 adaptive noise cancelling headphones product page"
                  },
                  {
                    "claim": "Candidate link: Sony WH-CH720N headphone official product page",
                    "confidence": 0.72,
                    "evidence_id": "47db36bc-e449-4756-a9dd-377c752f7cd0",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.sony.jp/headphone/products/WH-CH720N/",
                    "support": "Sony WH-CH720N headphone official product page"
                  }
                ],
                "fallback_used": null,
                "fields": {
                  "accessibility_tree": [],
                  "dynamic": true,
                  "evidence_stage": "candidate_pool",
                  "form_fields": [],
                  "interactable_elements": [],
                  "links": [
                    {
                      "href": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
                      "text": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison"
                    },
                    {
                      "href": "https://www.whathifi.com/reviews/sony-wh-ch720n",
                      "text": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review"
                    },
                    {
                      "href": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
                      "text": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page"
                    },
                    {
                      "href": "https://www.soundcore.com/products/space-q45-a3040011",
                      "text": "Soundcore Space Q45 adaptive noise cancelling headphones product page"
                    },
                    {
                      "href": "https://www.sony.jp/headphone/products/WH-CH720N/",
                      "text": "Sony WH-CH720N headphone official product page"
                    }
                  ],
                  "query": "1000元以内 降噪耳机 推荐 通勤 办公 头戴式 入耳式 型号 价格",
                  "screenshot_path": "runs/screenshots/d1-3f8c8c2d.png",
                  "source": "shopping",
                  "visible_buttons": [],
                  "visual_summary": "Screenshot captured for multimodal grounding; use provider analysis when configured."
                },
                "human_review_required": false,
                "ok": true,
                "text": "",
                "title": "",
                "url": "about:blank"
              },
              "verdict": {
                "checks": [
                  {
                    "detail": "ok",
                    "name": "action_ok",
                    "pass": true
                  },
                  {
                    "detail": "about:blank",
                    "name": "page_reachable",
                    "pass": true
                  },
                  {
                    "detail": "evidence=5 fields=11",
                    "name": "evidence_or_fields",
                    "pass": true
                  },
                  {
                    "detail": "content extracted",
                    "name": "content_non_empty",
                    "pass": true
                  }
                ],
                "ok": true,
                "retry_hint": null,
                "score": 1
              }
            },
            "phase": "execute_verify",
            "run_id": "f27fa595-c466-4bdb-b42f-c2cfec482cfe",
            "step_id": 1,
            "tool": "collect_links",
            "ts": 1780545072.887705,
            "url": "about:blank"
          },
          {
            "input": {
              "attempt": 1,
              "node": {
                "action": "deep_read_candidates",
                "depends_on": [
                  "d1"
                ],
                "id": "d2",
                "inputs": {
                  "checklist_status": [
                    {
                      "evidence": "已有 Sony WH-CH720N、Soundcore Space Q45、Edifier W820NB Plus 等候选链接。",
                      "stage": "candidate_pool",
                      "status": "partial"
                    },
                    {
                      "evidence": "已有官方商品页线索，但还缺少商城价格、销量和用户评价入口。",
                      "stage": "marketplace_pages",
                      "status": "partial"
                    },
                    {
                      "evidence": "已有 RTINGS 对比和 What Hi-Fi 评测链接，尚需提取具体结论。",
                      "stage": "comparative_reviews",
                      "status": "partial"
                    },
                    {
                      "evidence": "尚未收集差评、佩戴疲劳、底噪、故障等用户反馈。",
                      "stage": "user_comments",
                      "status": "missing"
                    },
                    {
                      "evidence": "尚未收集视频测评和评论区线索。",
                      "stage": "video_reviews",
                      "status": "missing"
                    }
                  ],
                  "dynamic": true,
                  "evidence_stage": "comparative_reviews",
                  "limit": 3,
                  "multimodal_planning_used": true,
                  "rationale": "已有候选商品页和专业评测链接，下一步应先深入读取商品与测评证据，补齐价格参数和对比信息。",
                  "source": "shopping"
                },
                "instruction": "深入读取当前候选链接中的商品页和专业评测，提取型号参数、价格定位、降噪/舒适度/办公通勤表现和主要短板。",
                "retry_policy": {
                  "max_retries": 2
                },
                "success_criteria": [
                  "action_ok",
                  "evidence_or_fields"
                ],
                "type": "agent_dynamic"
              }
            },
            "latency_ms": 26615,
            "output": {
              "result": {
                "action": "deep_read_candidates",
                "error": null,
                "evidence": [
                  {
                    "claim": "Deep candidate read: RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
                    "confidence": 0.78,
                    "evidence_id": "3af9d0bb-a2a3-4988-abc2-3141f8dea08f",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
                    "support": "Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless: Which Headphones Are Better? - RTINGS.com The Anker Soundcore Space Q45 Wireless are better headphones than the Sony WH-CH720N Wireless. Both headphones are comfortable, and the Anker come with a carrying case to protect the headphones when not in use. They also offer significantly better noise isolation performance and support LDAC for higher-resolution audio. Headphones Products In The Lab Forums Newsletters LOGIN JOIN NOW BEST Headphones N"
                  },
                  {
                    "claim": "Deep candidate read: What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
                    "confidence": 0.78,
                    "evidence_id": "072aebca-7320-456a-9d64-e471f2583e11",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.whathifi.com/reviews/sony-wh-ch720n",
                    "support": "Sony WH-CH720N review: supremely affordable over-ears with punchy sound and decent ANC | What Hi-Fi? What Hi-Fi? reviews the Sony WH-CH720N noise-cancelling headphones: expert testing and our verdict on sound quality, comfort, features and value – plus our star rating and alternatives to consider Skip to main content What Hi-Fi? THE WORLD'S #1 TECH BUYER'S GUIDE UK Edition RSS SUBSCRIBE Sign in News Reviews Best Buys Features Awards Hi-Fi Headphones TV & Home Cinema More Jump To: Price Build qua"
                  },
                  {
                    "claim": "Deep candidate read: Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
                    "confidence": 0.78,
                    "evidence_id": "9499b412-36b8-4e14-87bb-cca1aae90a3d",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
                    "support": "Wireless Noise Cancellation Over-Ear Headphones | W820NB Plus - Edifier USA Hassle-free phone calls with DNN noise cancellation technology Experience the upgraded noise cancellation with ANC depth of up to -43dB Up to 49 hours continuous playback when ANC off Personalize your listening experience with customizable EQ , soothing sounds via Edifier Connect APP"
                  }
                ],
                "fallback_used": null,
                "fields": {
                  "accessibility_tree": [],
                  "deep_reads": [
                    {
                      "description": "The Anker Soundcore Space Q45 Wireless are better headphones than the Sony WH-CH720N Wireless. Both headphones are comfortable, and the Anker come with a carrying case to protect the headphones when not in use. They also offer significantly better noise isolation performance and support LDAC for higher-resolution audio.",
                      "name": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
                      "ok": true,
                      "price_signal": "",
                      "rank": 1,
                      "source": "shopping",
                      "status": 200,
                      "text": "Headphones Products In The Lab Forums Newsletters LOGIN JOIN NOW BEST Headphones Noise Cancelling Wireless Earbuds Gaming Over-Ear Noise Cancelling Earbuds Running PC Gaming Apple Wireless Bone Conduction And Open-Ear Wireless Gaming Wired Wireless Earbuds Under $100 On-Ear In-Ears Xbox Series X/S Wireless Earbuds For Android Small Ear Earbuds Music TOOLS Compare Results Table Tool Review List Review Index Graph Review Pipeline Vote Custom Ratings POPULAR Sony WH-1000XM6 Sony WF-1000XM6 Audeze Maxwell 2 Razer BlackShark V3 Pro Bose QuietComfort Ultra Headphones (2nd Gen) Anker Soundcore Space A40 Truly Wireless Samsung Galaxy Buds4 Pro Technics EAH-AZ100 Apple AirPods Pro 3 Anker Soundcore Space Q45 Wireless Sennheiser HDB 630 Sony WH-1000XM4 Wireless Sony WF-1000XM5 Truly Wireless Sennheiser MOMENTUM 4 Wireless SteelSeries Arctis Nova 7 Wireless [7, 7P, 7X] Bose QuietComfort Ultra Earbuds (2nd Gen) CMF Buds Pro 2 Nothing Ear Sony WH-1000XM5 Wireless Anker Soundcore Life Q20 2024 889 HEADPHONES BOUGHT AND TESTED Supported by you via membership, and when you purchase through links on our site, we may earn an affiliate commission. Home Headphones Compare Notice: We've revamped our membership program. FEEDBACK Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless Which Headphones Are Better? Top Main Differences Sound Sound Profile Frequency Response Consistency Raw Frequency Response Bass Profile: Target Compliance Mid-Range Profile: Target Compliance Treble Profile: Target Compliance Peaks/Dips Stereo Mismatch Cumulative Spectral Decay PRTF Harmonic Distortion Electrical Aspects Virtual Soundstage Test Settings Design Style Comfort Controls Portability Case Build Quality Stability Headshots 1 Headshots 2 Top In The Box Isolation Noise Isolation - Full Range Noise Isolation - Common Scenarios Noise Isolation - Voice Handling ANC Wind Handling Leakage Microphone Microphone Style Recording Quality Noise Handling Active Features Battery App Support Connectivity Wired Connection Bluetooth Connection Wireless Connection (Dongle) PC Compatibility PlayStation Compatibility Xbox Compatibility Base/Dock Comments PRODUCTS Anker Soundcore Space Q45 Wireless Sony WH-CH720N Wireless Tested using Methodology v2.2 Updated May 28, 2026 01:56 AM SearchingFinding store Tested using Methodology v2.2 Updated Apr 16, 2026 02:29 AM SearchingFinding store Type Over-ear Noise Cancelling Yes Enclosure Closed-Back Bass Amount Emphasized (3 dB) Wireless Yes Treble Amount Balanced (0 dB",
                      "title": "Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless: Which Headphones Are Better? - RTINGS.com",
                      "url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-vs-sony-wh-ch720n-wireless/34852/38908"
                    },
                    {
                      "description": "What Hi-Fi? reviews the Sony WH-CH720N noise-cancelling headphones: expert testing and our verdict on sound quality, comfort, features and value – plus our star rating and alternatives to consider",
                      "name": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
                      "ok": true,
                      "price_signal": "",
                      "rank": 2,
                      "source": "shopping",
                      "status": 200,
                      "text": "Skip to main content What Hi-Fi? THE WORLD'S #1 TECH BUYER'S GUIDE UK Edition RSS SUBSCRIBE Sign in News Reviews Best Buys Features Awards Hi-Fi Headphones TV & Home Cinema More Jump To: Price Build quality & comfort Features Sound Verdict Tester's notes Also consider TRENDING Best Buys 50th Anniversary Best wireless earbuds Best soundbars Best speakers Headphones Wireless Headphones Sony WH-CH720N review What Hi-Fi? Awards 2025 winner. A truly affordable pair of over-ear headphones that delivers great noise-cancelling Tested at £99 / $129 / AU$259 Reviews By What Hi-Fi? last updated 16 October 2025 2 Comments When you purchase through links on our site, we may earn an affiliate commission. Here’s how it works. (Image credit: © What Hi-Fi?) What Hi-Fi? Verdict Sony has done it again. With their pleasing build quality and punchy sound, the WH-CH720N offers a truly budget bargain for those looking for a great pair of affordable ANC headphones £65 at Amazon £69 at Currys £74.99 at Sony UK £75 at Smart Home Sounds Pros + Forceful, robust sound presentation + Decent ANC for the price + Solid build quality Cons - A little over-enthusiastic in the bass - No case or foldability Best picks for you Best cheap noise-cancelling headphones 2026: expert-tested recommendations Best over-ear headphones 2026: wired and wireless pairs tested by our in-house experts Best noise-cancelling headphones 2026 – tested by our in-house review experts Why you can trust What Hi-Fi? Our expert team reviews products in dedicated test rooms, to help you make the best choice for your budget. Find out more about how we test. We've said this last year and we'll say it again: Sony is, at the moment, the Manchester City of the wireless headphones world, dominating the competition over the past few years with hit after five-star hit. From the budget WF-C500 wireless earbuds to the exceptional WH-1000XM5 over-ears, Sony has been hoovering up Awards and five-star ratings like the Sky Blues monopolise Premier League titles. We know how good Sony can be on the premium side, but the WH-CH720N – which retains its What Hi-Fi? Award as the best budget wireless headphones – fill a gap in the market by offering active noise-cancellation (ANC), good build quality and even better sound at a reasonable price. These are designed as a pair of cans for those who aren’t keen on forking out a few hundred quid for a premium pair of over-ears, but equally don’t want to miss out on features such as ANC or suffer a",
                      "title": "Sony WH-CH720N review: supremely affordable over-ears with punchy sound and decent ANC | What Hi-Fi?",
                      "url": "https://www.whathifi.com/reviews/sony-wh-ch720n"
                    },
                    {
                      "description": "Hassle-free phone calls with DNN noise cancellation technology\nExperience the upgraded noise cancellation with ANC depth of up to -43dB\nUp to 49 hours continuous playback when ANC off\nPersonalize your listening experience with customizable EQ , soothing sounds via Edifier Connect APP",
                      "name": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
                      "ok": true,
                      "price_signal": "",
                      "rank": 3,
                      "source": "shopping",
                      "status": 200,
                      "text": "",
                      "title": "Wireless Noise Cancellation Over-Ear Headphones | W820NB Plus - Edifier USA",
                      "url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus"
                    }
                  ],
                  "dynamic": true,
                  "evidence_stage": "comparative_reviews",
                  "form_fields": [],
                  "interactable_elements": [],
                  "links": [
                    {
                      "href": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
                      "text": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison"
                    },
                    {
                      "href": "https://www.whathifi.com/reviews/sony-wh-ch720n",
                      "text": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review"
                    },
                    {
                      "href": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
                      "text": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page"
                    },
                    {
                      "href": "https://www.soundcore.com/products/space-q45-a3040011",
                      "text": "Soundcore Space Q45 adaptive noise cancelling headphones product page"
                    },
                    {
                      "href": "https://www.sony.jp/headphone/products/WH-CH720N/",
                      "text": "Sony WH-CH720N headphone official product page"
                    }
                  ],
                  "screenshot_path": "runs/screenshots/d2-39306bee.png",
                  "source": "shopping",
                  "visible_buttons": [],
                  "visual_summary": "Screenshot captured for multimodal grounding; use provider analysis when configured."
                },
                "human_review_required": false,
                "ok": true,
                "text": "Headphones Products In The Lab Forums Newsletters LOGIN JOIN NOW BEST Headphones Noise Cancelling Wireless Earbuds Gaming Over-Ear Noise Cancelling Earbuds Running PC Gaming Apple Wireless Bone Conduction And Open-Ear Wireless Gaming Wired Wireless Earbuds Under $100 On-Ear In-Ears Xbox Series X/S Wireless Earbuds For Android Small Ear Earbuds Music TOOLS Compare Results Table Tool Review List Review Index Graph Review Pipeline Vote Custom Ratings POPULAR Sony WH-1000XM6 Sony WF-1000XM6 Audeze Maxwell 2 Razer BlackShark V3 Pro Bose QuietComfort Ultra Headphones (2nd Gen) Anker Soundcore Space A40 Truly Wireless Samsung Galaxy Buds4 Pro Technics EAH-AZ100 Apple AirPods Pro 3 Anker Soundcore Space Q45 Wireless Sennheiser HDB 630 Sony WH-1000XM4 Wireless Sony WF-1000XM5 Truly Wireless Sennheiser MOMENTUM 4 Wireless SteelSeries Arctis Nova 7 Wireless [7, 7P, 7X] Bose QuietComfort Ultra Earbuds (2nd Gen) CMF Buds Pro 2 Nothing Ear Sony WH-1000XM5 Wireless Anker Soundcore Life Q20 2024 889 HEADPHONES BOUGHT AND TESTED Supported by you via membership, and when you purchase through links on our site, we may earn an affiliate commission. Home Headphones Compare Notice: We've revamped our membership program. FEEDBACK Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless Which Headphones Are Better? Top Main Differences Sound Sound Profile Frequency Response Consistency Raw Frequency Response Bass Profile: Target Compliance Mid-Range Profile: Target Compliance Treble Profile: Target Compliance Peaks/Dips Stereo Mismatch Cumulative Spectral Decay PRTF Harmonic Distortion Electrical Aspects Virtual Soundstage Test Settings Design Style Comfort Controls Portability Case Build Quality Stability Headshots 1 Headshots 2 Top In The Box Isolation Noise Isolation - Full Range Noise Isolation - Common Scenarios Noise Isolation - Voice Handling ANC Wind Handling Leakage Microphone Microphone Style Recording Quality Noise Handling Active Features Battery App Support Connectivity Wired Connection Bluetooth Connection Wireless Connection (Dongle) PC Compatibility PlayStation Compatibility Xbox Compatibility Base/Dock Comments PRODUCTS Anker Soundcore Space Q45 Wireless Sony WH-CH720N Wireless Tested using Methodology v2.2 Updated May 28, 2026 01:56 AM SearchingFinding store Tested using Methodology v2.2 Updated Apr 16, 2026 02:29 AM SearchingFinding store Type Over-ear Noise Cancelling Yes Enclosure Closed-Back Bass Amount Emphasized (3 dB) Wireless Yes Treble Amount Balanced (0 dB Skip to main content What Hi-Fi? THE WORLD'S #1 TECH BUYER'S GUIDE UK Edition RSS SUBSCRIBE Sign in News Reviews Best Buys Features Awards Hi-Fi Headphones TV & Home Cinema More Jump To: Price Build quality & comfort Features Sound Verdict Tester's notes Also consider TRENDING Best Buys 50th Anniversary Best wireless earbuds Best soundbars Best speakers Headphones Wireless Headphones Sony WH-CH720N review What Hi-Fi? Awards 2025 winner. A truly affordable pair of over-ear headphones that delive",
                "title": "",
                "url": "about:blank"
              },
              "verdict": {
                "checks": [
                  {
                    "detail": "ok",
                    "name": "action_ok",
                    "pass": true
                  },
                  {
                    "detail": "about:blank",
                    "name": "page_reachable",
                    "pass": true
                  },
                  {
                    "detail": "evidence=3 fields=11",
                    "name": "evidence_or_fields",
                    "pass": true
                  },
                  {
                    "detail": "content extracted",
                    "name": "content_non_empty",
                    "pass": true
                  }
                ],
                "ok": true,
                "retry_hint": null,
                "score": 1
              }
            },
            "phase": "execute_verify",
            "run_id": "f27fa595-c466-4bdb-b42f-c2cfec482cfe",
            "step_id": 2,
            "tool": "deep_read_candidates",
            "ts": 1780545108.6494231,
            "url": "about:blank"
          },
          {
            "input": {
              "attempt": 1,
              "node": {
                "action": "search_web",
                "depends_on": [
                  "d2"
                ],
                "id": "d3",
                "inputs": {
                  "checklist_status": [
                    {
                      "evidence": "已覆盖 Space Q45、WH-CH720N、W820NB Plus 等候选，但国内价格/渠道仍需核对。",
                      "stage": "candidate_pool",
                      "status": "partial"
                    },
                    {
                      "evidence": "已有官方商品页参数，缺少京东/天猫等商城价格、销量和评价入口证据。",
                      "stage": "marketplace_pages",
                      "status": "partial"
                    },
                    {
                      "evidence": "已有 RTINGS 对比和 What Hi-Fi 专业评测，支持降噪、音质、舒适度初判。",
                      "stage": "comparative_reviews",
                      "status": "partial"
                    },
                    {
                      "evidence": "尚未收集用户评论、差评、佩戴疲劳、底噪、夹头或故障反馈。",
                      "stage": "user_comments",
                      "status": "missing"
                    },
                    {
                      "evidence": "尚未收集视频测评及评论区线索。",
                      "stage": "video_reviews",
                      "status": "missing"
                    }
                  ],
                  "dynamic": true,
                  "evidence_stage": "user_comments",
                  "multimodal_planning_used": true,
                  "query": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫",
                  "rationale": "已有候选型号和部分专业/商品页证据，下一步需要补齐真实用户差评与佩戴/故障反馈。",
                  "source": "general"
                },
                "instruction": "搜索具体候选型号的用户评价和差评，重点关注通勤办公场景下的佩戴舒适度、降噪、底噪、夹头、连接稳定性和常见故障。",
                "retry_policy": {
                  "max_retries": 2
                },
                "success_criteria": [
                  "action_ok",
                  "evidence_or_fields"
                ],
                "type": "agent_dynamic"
              }
            },
            "latency_ms": 562,
            "output": {
              "result": {
                "action": "search_web",
                "error": null,
                "evidence": [
                  {
                    "claim": "Search results for Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫",
                    "confidence": 0.65,
                    "evidence_id": "a390587b-84aa-41ba-8602-6210b05b9212",
                    "metadata": {},
                    "source_type": "general",
                    "source_url": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB",
                    "support": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫 - 搜索"
                  }
                ],
                "fallback_used": null,
                "fields": {
                  "accessibility_tree": [
                    {
                      "bbox": {
                        "height": 32,
                        "width": 86,
                        "x": 0,
                        "y": 46
                      },
                      "disabled": false,
                      "element_id": 0,
                      "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                      "index": 0,
                      "label": "跳至内容",
                      "name": "跳至内容",
                      "role": "button",
                      "selector": "[data-agent-idx=\"0\"]",
                      "tag": "a",
                      "text": "跳至内容",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 32,
                        "width": 112,
                        "x": 0,
                        "y": 46
                      },
                      "disabled": false,
                      "element_id": 1,
                      "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                      "index": 1,
                      "label": "辅助功能反馈",
                      "name": "辅助功能反馈",
                      "role": "button",
                      "selector": "[data-agent-idx=\"1\"]",
                      "tag": "a",
                      "text": "辅助功能反馈",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 40,
                        "width": 154,
                        "x": 0,
                        "y": 48
                      },
                      "disabled": false,
                      "element_id": 2,
                      "href": "https://cn.bing.com/?FORM=Z9FD1",
                      "index": 2,
                      "label": "",
                      "name": "",
                      "role": "link",
                      "selector": "[data-agent-idx=\"2\"]",
                      "tag": "a",
                      "text": "",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 40,
                        "width": 40,
                        "x": 164,
                        "y": 52
                      },
                      "disabled": false,
                      "element_id": 3,
                      "href": "",
                      "index": 3,
                      "label": "搜索",
                      "name": "搜索",
                      "role": "button",
                      "selector": "[data-agent-idx=\"3\"]",
                      "tag": "input",
                      "text": "搜索",
                      "type": "submit",
                      "value": "搜索"
                    },
                    {
                      "bbox": {
                        "height": 44,
                        "width": 571,
                        "x": 193,
                        "y": 50
                      },
                      "disabled": false,
                      "element_id": 4,
                      "href": "",
                      "index": 4,
                      "label": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "name": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "role": "searchbox",
                      "selector": "[data-agent-idx=\"4\"]",
                      "tag": "input",
                      "text": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "type": "search",
                      "value": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫"
                    },
                    {
                      "bbox": {
                        "height": 50,
                        "width": 50,
                        "x": 1198,
                        "y": 48
                      },
                      "disabled": false,
                      "element_id": 5,
                      "href": "javascript:void(0)",
                      "index": 5,
                      "label": "",
                      "name": "",
                      "role": "link",
                      "selector": "[data-agent-idx=\"5\"]",
                      "tag": "a",
                      "text": "",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 26,
                        "width": 59,
                        "x": 227,
                        "y": 18
                      },
                      "disabled": false,
                      "element_id": 6,
                      "href": "",
                      "index": 6,
                      "label": "国际版",
                      "name": "国际版",
                      "role": "div",
                      "selector": "[data-agent-idx=\"6\"]",
                      "tag": "div",
                      "text": "国际版",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 160,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 7,
                      "href": "https://cn.bing.com/?scope=web&FORM=HDRSC1",
                      "index": 7,
                      "label": "网页",
                      "name": "网页",
                      "role": "link",
                      "selector": "[data-agent-idx=\"7\"]",
                      "tag": "a",
                      "text": "网页",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 222,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 8,
                      "href": "https://cn.bing.com/images/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC2",
                      "index": 8,
                      "label": "图片",
                      "name": "图片",
                      "role": "link",
                      "selector": "[data-agent-idx=\"8\"]",
                      "tag": "a",
                      "text": "图片",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 284,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 9,
                      "href": "https://cn.bing.com/videos/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC3",
                      "index": 9,
                      "label": "视频",
                      "name": "视频",
                      "role": "link",
                      "selector": "[data-agent-idx=\"9\"]",
                      "tag": "a",
                      "text": "视频",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 346,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 10,
                      "href": "https://cn.bing.com/academic/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC4",
                      "index": 10,
                      "label": "学术",
                      "name": "学术",
                      "role": "link",
                      "selector": "[data-agent-idx=\"10\"]",
                      "tag": "a",
                      "text": "学术",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 408,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 11,
                      "href": "https://cn.bing.com/dict/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC6",
                      "index": 11,
                      "label": "词典",
                      "name": "词典",
                      "role": "link",
                      "selector": "[data-agent-idx=\"11\"]",
                      "tag": "a",
                      "text": "词典",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 470,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 12,
                      "href": "https://cn.bing.com/maps?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC7",
                      "index": 12,
                      "label": "地图",
                      "name": "地图",
                      "role": "link",
                      "selector": "[data-agent-idx=\"12\"]",
                      "tag": "a",
                      "text": "地图",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 54,
                        "x": 532,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 13,
                      "href": "javascript:void(0);",
                      "index": 13,
                      "label": "更多",
                      "name": "更多",
                      "role": "button",
                      "selector": "[data-agent-idx=\"13\"]",
                      "tag": "a",
                      "text": "更多",
                      "type": "",
                      "value": ""
                    }
                  ],
                  "dynamic": true,
                  "evidence_stage": "user_comments",
                  "form_fields": [
                    {
                      "bbox": {
                        "height": 44,
                        "width": 571,
                        "x": 193,
                        "y": 50
                      },
                      "disabled": false,
                      "element_id": 4,
                      "href": "",
                      "index": 4,
                      "label": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "name": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "role": "searchbox",
                      "selector": "[data-agent-idx=\"4\"]",
                      "tag": "input",
                      "text": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "type": "search",
                      "value": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫"
                    }
                  ],
                  "interactable_elements": [
                    {
                      "bbox": {
                        "height": 32,
                        "width": 86,
                        "x": 0,
                        "y": 46
                      },
                      "disabled": false,
                      "element_id": 0,
                      "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                      "index": 0,
                      "label": "跳至内容",
                      "name": "跳至内容",
                      "role": "button",
                      "selector": "[data-agent-idx=\"0\"]",
                      "tag": "a",
                      "text": "跳至内容",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 32,
                        "width": 112,
                        "x": 0,
                        "y": 46
                      },
                      "disabled": false,
                      "element_id": 1,
                      "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                      "index": 1,
                      "label": "辅助功能反馈",
                      "name": "辅助功能反馈",
                      "role": "button",
                      "selector": "[data-agent-idx=\"1\"]",
                      "tag": "a",
                      "text": "辅助功能反馈",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 40,
                        "width": 154,
                        "x": 0,
                        "y": 48
                      },
                      "disabled": false,
                      "element_id": 2,
                      "href": "https://cn.bing.com/?FORM=Z9FD1",
                      "index": 2,
                      "label": "",
                      "name": "",
                      "role": "link",
                      "selector": "[data-agent-idx=\"2\"]",
                      "tag": "a",
                      "text": "",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 40,
                        "width": 40,
                        "x": 164,
                        "y": 52
                      },
                      "disabled": false,
                      "element_id": 3,
                      "href": "",
                      "index": 3,
                      "label": "搜索",
                      "name": "搜索",
                      "role": "button",
                      "selector": "[data-agent-idx=\"3\"]",
                      "tag": "input",
                      "text": "搜索",
                      "type": "submit",
                      "value": "搜索"
                    },
                    {
                      "bbox": {
                        "height": 44,
                        "width": 571,
                        "x": 193,
                        "y": 50
                      },
                      "disabled": false,
                      "element_id": 4,
                      "href": "",
                      "index": 4,
                      "label": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "name": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "role": "searchbox",
                      "selector": "[data-agent-idx=\"4\"]",
                      "tag": "input",
                      "text": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "type": "search",
                      "value": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫"
                    },
                    {
                      "bbox": {
                        "height": 50,
                        "width": 50,
                        "x": 1198,
                        "y": 48
                      },
                      "disabled": false,
                      "element_id": 5,
                      "href": "javascript:void(0)",
                      "index": 5,
                      "label": "",
                      "name": "",
                      "role": "link",
                      "selector": "[data-agent-idx=\"5\"]",
                      "tag": "a",
                      "text": "",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 26,
                        "width": 59,
                        "x": 227,
                        "y": 18
                      },
                      "disabled": false,
                      "element_id": 6,
                      "href": "",
                      "index": 6,
                      "label": "国际版",
                      "name": "国际版",
                      "role": "div",
                      "selector": "[data-agent-idx=\"6\"]",
                      "tag": "div",
                      "text": "国际版",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 160,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 7,
                      "href": "https://cn.bing.com/?scope=web&FORM=HDRSC1",
                      "index": 7,
                      "label": "网页",
                      "name": "网页",
                      "role": "link",
                      "selector": "[data-agent-idx=\"7\"]",
                      "tag": "a",
                      "text": "网页",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 222,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 8,
                      "href": "https://cn.bing.com/images/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC2",
                      "index": 8,
                      "label": "图片",
                      "name": "图片",
                      "role": "link",
                      "selector": "[data-agent-idx=\"8\"]",
                      "tag": "a",
                      "text": "图片",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 284,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 9,
                      "href": "https://cn.bing.com/videos/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC3",
                      "index": 9,
                      "label": "视频",
                      "name": "视频",
                      "role": "link",
                      "selector": "[data-agent-idx=\"9\"]",
                      "tag": "a",
                      "text": "视频",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 346,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 10,
                      "href": "https://cn.bing.com/academic/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC4",
                      "index": 10,
                      "label": "学术",
                      "name": "学术",
                      "role": "link",
                      "selector": "[data-agent-idx=\"10\"]",
                      "tag": "a",
                      "text": "学术",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 408,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 11,
                      "href": "https://cn.bing.com/dict/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC6",
                      "index": 11,
                      "label": "词典",
                      "name": "词典",
                      "role": "link",
                      "selector": "[data-agent-idx=\"11\"]",
                      "tag": "a",
                      "text": "词典",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 470,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 12,
                      "href": "https://cn.bing.com/maps?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC7",
                      "index": 12,
                      "label": "地图",
                      "name": "地图",
                      "role": "link",
                      "selector": "[data-agent-idx=\"12\"]",
                      "tag": "a",
                      "text": "地图",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 54,
                        "x": 532,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 13,
                      "href": "javascript:void(0);",
                      "index": 13,
                      "label": "更多",
                      "name": "更多",
                      "role": "button",
                      "selector": "[data-agent-idx=\"13\"]",
                      "tag": "a",
                      "text": "更多",
                      "type": "",
                      "value": ""
                    }
                  ],
                  "screenshot_path": "runs/screenshots/d3-ec5539de.png",
                  "source": "general",
                  "status": 200,
                  "visible_buttons": [
                    {
                      "bbox": {
                        "height": 32,
                        "width": 86,
                        "x": 0,
                        "y": 46
                      },
                      "disabled": false,
                      "element_id": 0,
                      "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                      "index": 0,
                      "label": "跳至内容",
                      "name": "跳至内容",
                      "role": "button",
                      "selector": "[data-agent-idx=\"0\"]",
                      "tag": "a",
                      "text": "跳至内容",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 32,
                        "width": 112,
                        "x": 0,
                        "y": 46
                      },
                      "disabled": false,
                      "element_id": 1,
                      "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                      "index": 1,
                      "label": "辅助功能反馈",
                      "name": "辅助功能反馈",
                      "role": "button",
                      "selector": "[data-agent-idx=\"1\"]",
                      "tag": "a",
                      "text": "辅助功能反馈",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 40,
                        "width": 40,
                        "x": 164,
                        "y": 52
                      },
                      "disabled": false,
                      "element_id": 3,
                      "href": "",
                      "index": 3,
                      "label": "搜索",
                      "name": "搜索",
                      "role": "button",
                      "selector": "[data-agent-idx=\"3\"]",
                      "tag": "input",
                      "text": "搜索",
                      "type": "submit",
                      "value": "搜索"
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 54,
                        "x": 532,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 13,
                      "href": "javascript:void(0);",
                      "index": 13,
                      "label": "更多",
                      "name": "更多",
                      "role": "button",
                      "selector": "[data-agent-idx=\"13\"]",
                      "tag": "a",
                      "text": "更多",
                      "type": "",
                      "value": ""
                    }
                  ],
                  "visual_summary": "Screenshot captured for multimodal grounding; use provider analysis when configured."
                },
                "human_review_required": false,
                "ok": true,
                "text": "跳至内容 辅助功能反馈 国内版国际版 网页图片视频学术词典地图 更多",
                "title": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫 - 搜索",
                "url": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB"
              },
              "verdict": {
                "checks": [
                  {
                    "detail": "ok",
                    "name": "action_ok",
                    "pass": true
                  },
                  {
                    "detail": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB",
                    "name": "page_reachable",
                    "pass": true
                  },
                  {
                    "detail": "evidence=1 fields=10",
                    "name": "evidence_or_fields",
                    "pass": true
                  }
                ],
                "ok": true,
                "retry_hint": null,
                "score": 1
              }
            },
            "phase": "execute_verify",
            "run_id": "f27fa595-c466-4bdb-b42f-c2cfec482cfe",
            "step_id": 3,
            "tool": "search_web",
            "ts": 1780545119.591792,
            "url": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB"
          }
        ],
        "goal": "推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论",
        "llm": {
          "dynamic_agent_loop": {
            "evidence_checklist": [
              {
                "evidence_stage": "candidate_pool",
                "purpose": "建立预算内主流品牌/型号候选池和初步价格范围",
                "query": "site:post.smzdm.com 1000元以内 头戴式 降噪耳机 推荐 评测 通勤 办公",
                "source": "shopping"
              },
              {
                "evidence_stage": "marketplace_pages",
                "purpose": "进入商城/商品页线索，核对价格、参数、销量和评价入口",
                "query": "1000元以内 降噪耳机 京东 天猫 官方 商品页 参数 价格 用户评价",
                "source": "shopping"
              },
              {
                "evidence_stage": "comparative_reviews",
                "purpose": "围绕具体型号比较音质、降噪、舒适度和短板",
                "query": "WH-CH720N W820NB Space Q45 降噪耳机 对比 评测 缺点",
                "source": "shopping"
              },
              {
                "evidence_stage": "user_comments",
                "purpose": "收集用户评论、差评、佩戴疲劳和常见故障",
                "query": "WH-CH720N W820NB Space Q45 京东 天猫 用户评价 差评 佩戴 舒适度 底噪 夹头",
                "source": "general"
              },
              {
                "evidence_stage": "video_reviews",
                "purpose": "观察专业视频测评、可见字幕/简介和评论区线索",
                "query": "WH-CH720N W820NB Space Q45 降噪耳机 测评 视频 B站 YouTube 用户评论",
                "source": "video"
              }
            ],
            "fixed_templates_removed": true,
            "mode": "observe_plan_act_verify",
            "used": true
          },
          "enabled": true,
          "plan": {
            "evidence_checklist": [
              {
                "evidence_stage": "candidate_pool",
                "purpose": "建立预算内主流品牌/型号候选池和初步价格范围",
                "query": "site:post.smzdm.com 1000元以内 头戴式 降噪耳机 推荐 评测 通勤 办公",
                "source": "shopping"
              },
              {
                "evidence_stage": "marketplace_pages",
                "purpose": "进入商城/商品页线索，核对价格、参数、销量和评价入口",
                "query": "1000元以内 降噪耳机 京东 天猫 官方 商品页 参数 价格 用户评价",
                "source": "shopping"
              },
              {
                "evidence_stage": "comparative_reviews",
                "purpose": "围绕具体型号比较音质、降噪、舒适度和短板",
                "query": "WH-CH720N W820NB Space Q45 降噪耳机 对比 评测 缺点",
                "source": "shopping"
              },
              {
                "evidence_stage": "user_comments",
                "purpose": "收集用户评论、差评、佩戴疲劳和常见故障",
                "query": "WH-CH720N W820NB Space Q45 京东 天猫 用户评价 差评 佩戴 舒适度 底噪 夹头",
                "source": "general"
              },
              {
                "evidence_stage": "video_reviews",
                "purpose": "观察专业视频测评、可见字幕/简介和评论区线索",
                "query": "WH-CH720N W820NB Space Q45 降噪耳机 测评 视频 B站 YouTube 用户评论",
                "source": "video"
              }
            ],
            "mode": "dynamic_agent_loop",
            "used": true
          },
          "report": {
            "reason": "HTTPSConnectionPool(host='synai996.space', port=443): Read timed out. (read timeout=14)",
            "used": false
          }
        },
        "markdown_report_path": "runs/latest-report.md",
        "memory": {
          "evidence": [
            {
              "claim": "Candidate link: RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
              "confidence": 0.72,
              "evidence_id": "7a65de7d-fc1c-4652-be3a-550201a657f8",
              "metadata": {},
              "source_type": "shopping",
              "source_url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
              "support": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison"
            },
            {
              "claim": "Candidate link: What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
              "confidence": 0.72,
              "evidence_id": "b44facc5-a624-4354-9e8f-fbee54211cf9",
              "metadata": {},
              "source_type": "shopping",
              "source_url": "https://www.whathifi.com/reviews/sony-wh-ch720n",
              "support": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review"
            },
            {
              "claim": "Candidate link: Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
              "confidence": 0.72,
              "evidence_id": "d726928c-df65-4bde-9fae-707f3013374e",
              "metadata": {},
              "source_type": "shopping",
              "source_url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
              "support": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page"
            },
            {
              "claim": "Candidate link: Soundcore Space Q45 adaptive noise cancelling headphones product page",
              "confidence": 0.72,
              "evidence_id": "60900630-ff06-4d65-8570-14034f4307f3",
              "metadata": {},
              "source_type": "shopping",
              "source_url": "https://www.soundcore.com/products/space-q45-a3040011",
              "support": "Soundcore Space Q45 adaptive noise cancelling headphones product page"
            },
            {
              "claim": "Candidate link: Sony WH-CH720N headphone official product page",
              "confidence": 0.72,
              "evidence_id": "47db36bc-e449-4756-a9dd-377c752f7cd0",
              "metadata": {},
              "source_type": "shopping",
              "source_url": "https://www.sony.jp/headphone/products/WH-CH720N/",
              "support": "Sony WH-CH720N headphone official product page"
            },
            {
              "claim": "Deep candidate read: RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
              "confidence": 0.78,
              "evidence_id": "3af9d0bb-a2a3-4988-abc2-3141f8dea08f",
              "metadata": {},
              "source_type": "shopping",
              "source_url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
              "support": "Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless: Which Headphones Are Better? - RTINGS.com The Anker Soundcore Space Q45 Wireless are better headphones than the Sony WH-CH720N Wireless. Both headphones are comfortable, and the Anker come with a carrying case to protect the headphones when not in use. They also offer significantly better noise isolation performance and support LDAC for higher-resolution audio. Headphones Products In The Lab Forums Newsletters LOGIN JOIN NOW BEST Headphones N"
            },
            {
              "claim": "Deep candidate read: What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
              "confidence": 0.78,
              "evidence_id": "072aebca-7320-456a-9d64-e471f2583e11",
              "metadata": {},
              "source_type": "shopping",
              "source_url": "https://www.whathifi.com/reviews/sony-wh-ch720n",
              "support": "Sony WH-CH720N review: supremely affordable over-ears with punchy sound and decent ANC | What Hi-Fi? What Hi-Fi? reviews the Sony WH-CH720N noise-cancelling headphones: expert testing and our verdict on sound quality, comfort, features and value – plus our star rating and alternatives to consider Skip to main content What Hi-Fi? THE WORLD'S #1 TECH BUYER'S GUIDE UK Edition RSS SUBSCRIBE Sign in News Reviews Best Buys Features Awards Hi-Fi Headphones TV & Home Cinema More Jump To: Price Build qua"
            },
            {
              "claim": "Deep candidate read: Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
              "confidence": 0.78,
              "evidence_id": "9499b412-36b8-4e14-87bb-cca1aae90a3d",
              "metadata": {},
              "source_type": "shopping",
              "source_url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
              "support": "Wireless Noise Cancellation Over-Ear Headphones | W820NB Plus - Edifier USA Hassle-free phone calls with DNN noise cancellation technology Experience the upgraded noise cancellation with ANC depth of up to -43dB Up to 49 hours continuous playback when ANC off Personalize your listening experience with customizable EQ , soothing sounds via Edifier Connect APP"
            },
            {
              "claim": "Search results for Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫",
              "confidence": 0.65,
              "evidence_id": "a390587b-84aa-41ba-8602-6210b05b9212",
              "metadata": {},
              "source_type": "general",
              "source_url": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB",
              "support": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫 - 搜索"
            }
          ],
          "goal": "推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论",
          "traces": [
            {
              "node": {
                "action": "collect_links",
                "depends_on": [],
                "id": "d1",
                "inputs": {
                  "checklist_status": [
                    {
                      "evidence": "尚未收集预算内主流型号和价格线索。",
                      "stage": "candidate_pool",
                      "status": "missing"
                    },
                    {
                      "evidence": "尚未核对商城商品页价格、参数和评价入口。",
                      "stage": "marketplace_pages",
                      "status": "missing"
                    },
                    {
                      "evidence": "尚未收集专业对比评测。",
                      "stage": "comparative_reviews",
                      "status": "missing"
                    },
                    {
                      "evidence": "尚未收集用户差评和佩戴/故障反馈。",
                      "stage": "user_comments",
                      "status": "missing"
                    },
                    {
                      "evidence": "尚未收集视频测评及评论区线索。",
                      "stage": "video_reviews",
                      "status": "missing"
                    }
                  ],
                  "dynamic": true,
                  "evidence_stage": "candidate_pool",
                  "multimodal_planning_used": false,
                  "planner_suggested_action": "search_web",
                  "planner_suggested_rationale": "当前搜索页没有可用结果摘要或可交互元素，需要先用更聚焦的购物/推荐查询建立候选型号池。",
                  "query": "1000元以内 降噪耳机 推荐 通勤 办公 头戴式 入耳式 型号 价格",
                  "rationale": "Progress guard: current page is already a results/search page, so collect visible candidates before issuing another search or wait.",
                  "source": "shopping"
                },
                "instruction": "当前已经到达搜索/结果页，先抽取候选链接或启用垂直候选恢复。",
                "retry_policy": {
                  "max_retries": 2
                },
                "success_criteria": [
                  "action_ok",
                  "evidence_or_fields"
                ],
                "type": "agent_dynamic_guarded"
              },
              "output": {
                "action": "collect_links",
                "error": null,
                "evidence": [
                  {
                    "claim": "Candidate link: RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
                    "confidence": 0.72,
                    "evidence_id": "7a65de7d-fc1c-4652-be3a-550201a657f8",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
                    "support": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison"
                  },
                  {
                    "claim": "Candidate link: What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
                    "confidence": 0.72,
                    "evidence_id": "b44facc5-a624-4354-9e8f-fbee54211cf9",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.whathifi.com/reviews/sony-wh-ch720n",
                    "support": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review"
                  },
                  {
                    "claim": "Candidate link: Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
                    "confidence": 0.72,
                    "evidence_id": "d726928c-df65-4bde-9fae-707f3013374e",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
                    "support": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page"
                  },
                  {
                    "claim": "Candidate link: Soundcore Space Q45 adaptive noise cancelling headphones product page",
                    "confidence": 0.72,
                    "evidence_id": "60900630-ff06-4d65-8570-14034f4307f3",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.soundcore.com/products/space-q45-a3040011",
                    "support": "Soundcore Space Q45 adaptive noise cancelling headphones product page"
                  },
                  {
                    "claim": "Candidate link: Sony WH-CH720N headphone official product page",
                    "confidence": 0.72,
                    "evidence_id": "47db36bc-e449-4756-a9dd-377c752f7cd0",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.sony.jp/headphone/products/WH-CH720N/",
                    "support": "Sony WH-CH720N headphone official product page"
                  }
                ],
                "fallback_used": null,
                "fields": {
                  "accessibility_tree": [],
                  "dynamic": true,
                  "evidence_stage": "candidate_pool",
                  "form_fields": [],
                  "interactable_elements": [],
                  "links": [
                    {
                      "href": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
                      "text": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison"
                    },
                    {
                      "href": "https://www.whathifi.com/reviews/sony-wh-ch720n",
                      "text": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review"
                    },
                    {
                      "href": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
                      "text": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page"
                    },
                    {
                      "href": "https://www.soundcore.com/products/space-q45-a3040011",
                      "text": "Soundcore Space Q45 adaptive noise cancelling headphones product page"
                    },
                    {
                      "href": "https://www.sony.jp/headphone/products/WH-CH720N/",
                      "text": "Sony WH-CH720N headphone official product page"
                    }
                  ],
                  "query": "1000元以内 降噪耳机 推荐 通勤 办公 头戴式 入耳式 型号 价格",
                  "screenshot_path": "runs/screenshots/d1-3f8c8c2d.png",
                  "source": "shopping",
                  "visible_buttons": [],
                  "visual_summary": "Screenshot captured for multimodal grounding; use provider analysis when configured."
                },
                "human_review_required": false,
                "ok": true,
                "text": "",
                "title": "",
                "url": "about:blank"
              },
              "verdict": {
                "checks": [
                  {
                    "detail": "ok",
                    "name": "action_ok",
                    "pass": true
                  },
                  {
                    "detail": "about:blank",
                    "name": "page_reachable",
                    "pass": true
                  },
                  {
                    "detail": "evidence=5 fields=11",
                    "name": "evidence_or_fields",
                    "pass": true
                  },
                  {
                    "detail": "content extracted",
                    "name": "content_non_empty",
                    "pass": true
                  }
                ],
                "ok": true,
                "retry_hint": null,
                "score": 1
              }
            },
            {
              "node": {
                "action": "deep_read_candidates",
                "depends_on": [
                  "d1"
                ],
                "id": "d2",
                "inputs": {
                  "checklist_status": [
                    {
                      "evidence": "已有 Sony WH-CH720N、Soundcore Space Q45、Edifier W820NB Plus 等候选链接。",
                      "stage": "candidate_pool",
                      "status": "partial"
                    },
                    {
                      "evidence": "已有官方商品页线索，但还缺少商城价格、销量和用户评价入口。",
                      "stage": "marketplace_pages",
                      "status": "partial"
                    },
                    {
                      "evidence": "已有 RTINGS 对比和 What Hi-Fi 评测链接，尚需提取具体结论。",
                      "stage": "comparative_reviews",
                      "status": "partial"
                    },
                    {
                      "evidence": "尚未收集差评、佩戴疲劳、底噪、故障等用户反馈。",
                      "stage": "user_comments",
                      "status": "missing"
                    },
                    {
                      "evidence": "尚未收集视频测评和评论区线索。",
                      "stage": "video_reviews",
                      "status": "missing"
                    }
                  ],
                  "dynamic": true,
                  "evidence_stage": "comparative_reviews",
                  "limit": 3,
                  "multimodal_planning_used": true,
                  "rationale": "已有候选商品页和专业评测链接，下一步应先深入读取商品与测评证据，补齐价格参数和对比信息。",
                  "source": "shopping"
                },
                "instruction": "深入读取当前候选链接中的商品页和专业评测，提取型号参数、价格定位、降噪/舒适度/办公通勤表现和主要短板。",
                "retry_policy": {
                  "max_retries": 2
                },
                "success_criteria": [
                  "action_ok",
                  "evidence_or_fields"
                ],
                "type": "agent_dynamic"
              },
              "output": {
                "action": "deep_read_candidates",
                "error": null,
                "evidence": [
                  {
                    "claim": "Deep candidate read: RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
                    "confidence": 0.78,
                    "evidence_id": "3af9d0bb-a2a3-4988-abc2-3141f8dea08f",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
                    "support": "Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless: Which Headphones Are Better? - RTINGS.com The Anker Soundcore Space Q45 Wireless are better headphones than the Sony WH-CH720N Wireless. Both headphones are comfortable, and the Anker come with a carrying case to protect the headphones when not in use. They also offer significantly better noise isolation performance and support LDAC for higher-resolution audio. Headphones Products In The Lab Forums Newsletters LOGIN JOIN NOW BEST Headphones N"
                  },
                  {
                    "claim": "Deep candidate read: What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
                    "confidence": 0.78,
                    "evidence_id": "072aebca-7320-456a-9d64-e471f2583e11",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.whathifi.com/reviews/sony-wh-ch720n",
                    "support": "Sony WH-CH720N review: supremely affordable over-ears with punchy sound and decent ANC | What Hi-Fi? What Hi-Fi? reviews the Sony WH-CH720N noise-cancelling headphones: expert testing and our verdict on sound quality, comfort, features and value – plus our star rating and alternatives to consider Skip to main content What Hi-Fi? THE WORLD'S #1 TECH BUYER'S GUIDE UK Edition RSS SUBSCRIBE Sign in News Reviews Best Buys Features Awards Hi-Fi Headphones TV & Home Cinema More Jump To: Price Build qua"
                  },
                  {
                    "claim": "Deep candidate read: Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
                    "confidence": 0.78,
                    "evidence_id": "9499b412-36b8-4e14-87bb-cca1aae90a3d",
                    "metadata": {},
                    "source_type": "shopping",
                    "source_url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
                    "support": "Wireless Noise Cancellation Over-Ear Headphones | W820NB Plus - Edifier USA Hassle-free phone calls with DNN noise cancellation technology Experience the upgraded noise cancellation with ANC depth of up to -43dB Up to 49 hours continuous playback when ANC off Personalize your listening experience with customizable EQ , soothing sounds via Edifier Connect APP"
                  }
                ],
                "fallback_used": null,
                "fields": {
                  "accessibility_tree": [],
                  "deep_reads": [
                    {
                      "description": "The Anker Soundcore Space Q45 Wireless are better headphones than the Sony WH-CH720N Wireless. Both headphones are comfortable, and the Anker come with a carrying case to protect the headphones when not in use. They also offer significantly better noise isolation performance and support LDAC for higher-resolution audio.",
                      "name": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
                      "ok": true,
                      "price_signal": "",
                      "rank": 1,
                      "source": "shopping",
                      "status": 200,
                      "text": "Headphones Products In The Lab Forums Newsletters LOGIN JOIN NOW BEST Headphones Noise Cancelling Wireless Earbuds Gaming Over-Ear Noise Cancelling Earbuds Running PC Gaming Apple Wireless Bone Conduction And Open-Ear Wireless Gaming Wired Wireless Earbuds Under $100 On-Ear In-Ears Xbox Series X/S Wireless Earbuds For Android Small Ear Earbuds Music TOOLS Compare Results Table Tool Review List Review Index Graph Review Pipeline Vote Custom Ratings POPULAR Sony WH-1000XM6 Sony WF-1000XM6 Audeze Maxwell 2 Razer BlackShark V3 Pro Bose QuietComfort Ultra Headphones (2nd Gen) Anker Soundcore Space A40 Truly Wireless Samsung Galaxy Buds4 Pro Technics EAH-AZ100 Apple AirPods Pro 3 Anker Soundcore Space Q45 Wireless Sennheiser HDB 630 Sony WH-1000XM4 Wireless Sony WF-1000XM5 Truly Wireless Sennheiser MOMENTUM 4 Wireless SteelSeries Arctis Nova 7 Wireless [7, 7P, 7X] Bose QuietComfort Ultra Earbuds (2nd Gen) CMF Buds Pro 2 Nothing Ear Sony WH-1000XM5 Wireless Anker Soundcore Life Q20 2024 889 HEADPHONES BOUGHT AND TESTED Supported by you via membership, and when you purchase through links on our site, we may earn an affiliate commission. Home Headphones Compare Notice: We've revamped our membership program. FEEDBACK Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless Which Headphones Are Better? Top Main Differences Sound Sound Profile Frequency Response Consistency Raw Frequency Response Bass Profile: Target Compliance Mid-Range Profile: Target Compliance Treble Profile: Target Compliance Peaks/Dips Stereo Mismatch Cumulative Spectral Decay PRTF Harmonic Distortion Electrical Aspects Virtual Soundstage Test Settings Design Style Comfort Controls Portability Case Build Quality Stability Headshots 1 Headshots 2 Top In The Box Isolation Noise Isolation - Full Range Noise Isolation - Common Scenarios Noise Isolation - Voice Handling ANC Wind Handling Leakage Microphone Microphone Style Recording Quality Noise Handling Active Features Battery App Support Connectivity Wired Connection Bluetooth Connection Wireless Connection (Dongle) PC Compatibility PlayStation Compatibility Xbox Compatibility Base/Dock Comments PRODUCTS Anker Soundcore Space Q45 Wireless Sony WH-CH720N Wireless Tested using Methodology v2.2 Updated May 28, 2026 01:56 AM SearchingFinding store Tested using Methodology v2.2 Updated Apr 16, 2026 02:29 AM SearchingFinding store Type Over-ear Noise Cancelling Yes Enclosure Closed-Back Bass Amount Emphasized (3 dB) Wireless Yes Treble Amount Balanced (0 dB",
                      "title": "Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless: Which Headphones Are Better? - RTINGS.com",
                      "url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-vs-sony-wh-ch720n-wireless/34852/38908"
                    },
                    {
                      "description": "What Hi-Fi? reviews the Sony WH-CH720N noise-cancelling headphones: expert testing and our verdict on sound quality, comfort, features and value – plus our star rating and alternatives to consider",
                      "name": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
                      "ok": true,
                      "price_signal": "",
                      "rank": 2,
                      "source": "shopping",
                      "status": 200,
                      "text": "Skip to main content What Hi-Fi? THE WORLD'S #1 TECH BUYER'S GUIDE UK Edition RSS SUBSCRIBE Sign in News Reviews Best Buys Features Awards Hi-Fi Headphones TV & Home Cinema More Jump To: Price Build quality & comfort Features Sound Verdict Tester's notes Also consider TRENDING Best Buys 50th Anniversary Best wireless earbuds Best soundbars Best speakers Headphones Wireless Headphones Sony WH-CH720N review What Hi-Fi? Awards 2025 winner. A truly affordable pair of over-ear headphones that delivers great noise-cancelling Tested at £99 / $129 / AU$259 Reviews By What Hi-Fi? last updated 16 October 2025 2 Comments When you purchase through links on our site, we may earn an affiliate commission. Here’s how it works. (Image credit: © What Hi-Fi?) What Hi-Fi? Verdict Sony has done it again. With their pleasing build quality and punchy sound, the WH-CH720N offers a truly budget bargain for those looking for a great pair of affordable ANC headphones £65 at Amazon £69 at Currys £74.99 at Sony UK £75 at Smart Home Sounds Pros + Forceful, robust sound presentation + Decent ANC for the price + Solid build quality Cons - A little over-enthusiastic in the bass - No case or foldability Best picks for you Best cheap noise-cancelling headphones 2026: expert-tested recommendations Best over-ear headphones 2026: wired and wireless pairs tested by our in-house experts Best noise-cancelling headphones 2026 – tested by our in-house review experts Why you can trust What Hi-Fi? Our expert team reviews products in dedicated test rooms, to help you make the best choice for your budget. Find out more about how we test. We've said this last year and we'll say it again: Sony is, at the moment, the Manchester City of the wireless headphones world, dominating the competition over the past few years with hit after five-star hit. From the budget WF-C500 wireless earbuds to the exceptional WH-1000XM5 over-ears, Sony has been hoovering up Awards and five-star ratings like the Sky Blues monopolise Premier League titles. We know how good Sony can be on the premium side, but the WH-CH720N – which retains its What Hi-Fi? Award as the best budget wireless headphones – fill a gap in the market by offering active noise-cancellation (ANC), good build quality and even better sound at a reasonable price. These are designed as a pair of cans for those who aren’t keen on forking out a few hundred quid for a premium pair of over-ears, but equally don’t want to miss out on features such as ANC or suffer a",
                      "title": "Sony WH-CH720N review: supremely affordable over-ears with punchy sound and decent ANC | What Hi-Fi?",
                      "url": "https://www.whathifi.com/reviews/sony-wh-ch720n"
                    },
                    {
                      "description": "Hassle-free phone calls with DNN noise cancellation technology\nExperience the upgraded noise cancellation with ANC depth of up to -43dB\nUp to 49 hours continuous playback when ANC off\nPersonalize your listening experience with customizable EQ , soothing sounds via Edifier Connect APP",
                      "name": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
                      "ok": true,
                      "price_signal": "",
                      "rank": 3,
                      "source": "shopping",
                      "status": 200,
                      "text": "",
                      "title": "Wireless Noise Cancellation Over-Ear Headphones | W820NB Plus - Edifier USA",
                      "url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus"
                    }
                  ],
                  "dynamic": true,
                  "evidence_stage": "comparative_reviews",
                  "form_fields": [],
                  "interactable_elements": [],
                  "links": [
                    {
                      "href": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
                      "text": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison"
                    },
                    {
                      "href": "https://www.whathifi.com/reviews/sony-wh-ch720n",
                      "text": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review"
                    },
                    {
                      "href": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
                      "text": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page"
                    },
                    {
                      "href": "https://www.soundcore.com/products/space-q45-a3040011",
                      "text": "Soundcore Space Q45 adaptive noise cancelling headphones product page"
                    },
                    {
                      "href": "https://www.sony.jp/headphone/products/WH-CH720N/",
                      "text": "Sony WH-CH720N headphone official product page"
                    }
                  ],
                  "screenshot_path": "runs/screenshots/d2-39306bee.png",
                  "source": "shopping",
                  "visible_buttons": [],
                  "visual_summary": "Screenshot captured for multimodal grounding; use provider analysis when configured."
                },
                "human_review_required": false,
                "ok": true,
                "text": "Headphones Products In The Lab Forums Newsletters LOGIN JOIN NOW BEST Headphones Noise Cancelling Wireless Earbuds Gaming Over-Ear Noise Cancelling Earbuds Running PC Gaming Apple Wireless Bone Conduction And Open-Ear Wireless Gaming Wired Wireless Earbuds Under $100 On-Ear In-Ears Xbox Series X/S Wireless Earbuds For Android Small Ear Earbuds Music TOOLS Compare Results Table Tool Review List Review Index Graph Review Pipeline Vote Custom Ratings POPULAR Sony WH-1000XM6 Sony WF-1000XM6 Audeze Maxwell 2 Razer BlackShark V3 Pro Bose QuietComfort Ultra Headphones (2nd Gen) Anker Soundcore Space A40 Truly Wireless Samsung Galaxy Buds4 Pro Technics EAH-AZ100 Apple AirPods Pro 3 Anker Soundcore Space Q45 Wireless Sennheiser HDB 630 Sony WH-1000XM4 Wireless Sony WF-1000XM5 Truly Wireless Sennheiser MOMENTUM 4 Wireless SteelSeries Arctis Nova 7 Wireless [7, 7P, 7X] Bose QuietComfort Ultra Earbuds (2nd Gen) CMF Buds Pro 2 Nothing Ear Sony WH-1000XM5 Wireless Anker Soundcore Life Q20 2024 889 HEADPHONES BOUGHT AND TESTED Supported by you via membership, and when you purchase through links on our site, we may earn an affiliate commission. Home Headphones Compare Notice: We've revamped our membership program. FEEDBACK Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless Which Headphones Are Better? Top Main Differences Sound Sound Profile Frequency Response Consistency Raw Frequency Response Bass Profile: Target Compliance Mid-Range Profile: Target Compliance Treble Profile: Target Compliance Peaks/Dips Stereo Mismatch Cumulative Spectral Decay PRTF Harmonic Distortion Electrical Aspects Virtual Soundstage Test Settings Design Style Comfort Controls Portability Case Build Quality Stability Headshots 1 Headshots 2 Top In The Box Isolation Noise Isolation - Full Range Noise Isolation - Common Scenarios Noise Isolation - Voice Handling ANC Wind Handling Leakage Microphone Microphone Style Recording Quality Noise Handling Active Features Battery App Support Connectivity Wired Connection Bluetooth Connection Wireless Connection (Dongle) PC Compatibility PlayStation Compatibility Xbox Compatibility Base/Dock Comments PRODUCTS Anker Soundcore Space Q45 Wireless Sony WH-CH720N Wireless Tested using Methodology v2.2 Updated May 28, 2026 01:56 AM SearchingFinding store Tested using Methodology v2.2 Updated Apr 16, 2026 02:29 AM SearchingFinding store Type Over-ear Noise Cancelling Yes Enclosure Closed-Back Bass Amount Emphasized (3 dB) Wireless Yes Treble Amount Balanced (0 dB Skip to main content What Hi-Fi? THE WORLD'S #1 TECH BUYER'S GUIDE UK Edition RSS SUBSCRIBE Sign in News Reviews Best Buys Features Awards Hi-Fi Headphones TV & Home Cinema More Jump To: Price Build quality & comfort Features Sound Verdict Tester's notes Also consider TRENDING Best Buys 50th Anniversary Best wireless earbuds Best soundbars Best speakers Headphones Wireless Headphones Sony WH-CH720N review What Hi-Fi? Awards 2025 winner. A truly affordable pair of over-ear headphones that delive",
                "title": "",
                "url": "about:blank"
              },
              "verdict": {
                "checks": [
                  {
                    "detail": "ok",
                    "name": "action_ok",
                    "pass": true
                  },
                  {
                    "detail": "about:blank",
                    "name": "page_reachable",
                    "pass": true
                  },
                  {
                    "detail": "evidence=3 fields=11",
                    "name": "evidence_or_fields",
                    "pass": true
                  },
                  {
                    "detail": "content extracted",
                    "name": "content_non_empty",
                    "pass": true
                  }
                ],
                "ok": true,
                "retry_hint": null,
                "score": 1
              }
            },
            {
              "node": {
                "action": "search_web",
                "depends_on": [
                  "d2"
                ],
                "id": "d3",
                "inputs": {
                  "checklist_status": [
                    {
                      "evidence": "已覆盖 Space Q45、WH-CH720N、W820NB Plus 等候选，但国内价格/渠道仍需核对。",
                      "stage": "candidate_pool",
                      "status": "partial"
                    },
                    {
                      "evidence": "已有官方商品页参数，缺少京东/天猫等商城价格、销量和评价入口证据。",
                      "stage": "marketplace_pages",
                      "status": "partial"
                    },
                    {
                      "evidence": "已有 RTINGS 对比和 What Hi-Fi 专业评测，支持降噪、音质、舒适度初判。",
                      "stage": "comparative_reviews",
                      "status": "partial"
                    },
                    {
                      "evidence": "尚未收集用户评论、差评、佩戴疲劳、底噪、夹头或故障反馈。",
                      "stage": "user_comments",
                      "status": "missing"
                    },
                    {
                      "evidence": "尚未收集视频测评及评论区线索。",
                      "stage": "video_reviews",
                      "status": "missing"
                    }
                  ],
                  "dynamic": true,
                  "evidence_stage": "user_comments",
                  "multimodal_planning_used": true,
                  "query": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫",
                  "rationale": "已有候选型号和部分专业/商品页证据，下一步需要补齐真实用户差评与佩戴/故障反馈。",
                  "source": "general"
                },
                "instruction": "搜索具体候选型号的用户评价和差评，重点关注通勤办公场景下的佩戴舒适度、降噪、底噪、夹头、连接稳定性和常见故障。",
                "retry_policy": {
                  "max_retries": 2
                },
                "success_criteria": [
                  "action_ok",
                  "evidence_or_fields"
                ],
                "type": "agent_dynamic"
              },
              "output": {
                "action": "search_web",
                "error": null,
                "evidence": [
                  {
                    "claim": "Search results for Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫",
                    "confidence": 0.65,
                    "evidence_id": "a390587b-84aa-41ba-8602-6210b05b9212",
                    "metadata": {},
                    "source_type": "general",
                    "source_url": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB",
                    "support": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫 - 搜索"
                  }
                ],
                "fallback_used": null,
                "fields": {
                  "accessibility_tree": [
                    {
                      "bbox": {
                        "height": 32,
                        "width": 86,
                        "x": 0,
                        "y": 46
                      },
                      "disabled": false,
                      "element_id": 0,
                      "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                      "index": 0,
                      "label": "跳至内容",
                      "name": "跳至内容",
                      "role": "button",
                      "selector": "[data-agent-idx=\"0\"]",
                      "tag": "a",
                      "text": "跳至内容",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 32,
                        "width": 112,
                        "x": 0,
                        "y": 46
                      },
                      "disabled": false,
                      "element_id": 1,
                      "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                      "index": 1,
                      "label": "辅助功能反馈",
                      "name": "辅助功能反馈",
                      "role": "button",
                      "selector": "[data-agent-idx=\"1\"]",
                      "tag": "a",
                      "text": "辅助功能反馈",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 40,
                        "width": 154,
                        "x": 0,
                        "y": 48
                      },
                      "disabled": false,
                      "element_id": 2,
                      "href": "https://cn.bing.com/?FORM=Z9FD1",
                      "index": 2,
                      "label": "",
                      "name": "",
                      "role": "link",
                      "selector": "[data-agent-idx=\"2\"]",
                      "tag": "a",
                      "text": "",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 40,
                        "width": 40,
                        "x": 164,
                        "y": 52
                      },
                      "disabled": false,
                      "element_id": 3,
                      "href": "",
                      "index": 3,
                      "label": "搜索",
                      "name": "搜索",
                      "role": "button",
                      "selector": "[data-agent-idx=\"3\"]",
                      "tag": "input",
                      "text": "搜索",
                      "type": "submit",
                      "value": "搜索"
                    },
                    {
                      "bbox": {
                        "height": 44,
                        "width": 571,
                        "x": 193,
                        "y": 50
                      },
                      "disabled": false,
                      "element_id": 4,
                      "href": "",
                      "index": 4,
                      "label": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "name": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "role": "searchbox",
                      "selector": "[data-agent-idx=\"4\"]",
                      "tag": "input",
                      "text": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "type": "search",
                      "value": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫"
                    },
                    {
                      "bbox": {
                        "height": 50,
                        "width": 50,
                        "x": 1198,
                        "y": 48
                      },
                      "disabled": false,
                      "element_id": 5,
                      "href": "javascript:void(0)",
                      "index": 5,
                      "label": "",
                      "name": "",
                      "role": "link",
                      "selector": "[data-agent-idx=\"5\"]",
                      "tag": "a",
                      "text": "",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 26,
                        "width": 59,
                        "x": 227,
                        "y": 18
                      },
                      "disabled": false,
                      "element_id": 6,
                      "href": "",
                      "index": 6,
                      "label": "国际版",
                      "name": "国际版",
                      "role": "div",
                      "selector": "[data-agent-idx=\"6\"]",
                      "tag": "div",
                      "text": "国际版",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 160,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 7,
                      "href": "https://cn.bing.com/?scope=web&FORM=HDRSC1",
                      "index": 7,
                      "label": "网页",
                      "name": "网页",
                      "role": "link",
                      "selector": "[data-agent-idx=\"7\"]",
                      "tag": "a",
                      "text": "网页",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 222,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 8,
                      "href": "https://cn.bing.com/images/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC2",
                      "index": 8,
                      "label": "图片",
                      "name": "图片",
                      "role": "link",
                      "selector": "[data-agent-idx=\"8\"]",
                      "tag": "a",
                      "text": "图片",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 284,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 9,
                      "href": "https://cn.bing.com/videos/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC3",
                      "index": 9,
                      "label": "视频",
                      "name": "视频",
                      "role": "link",
                      "selector": "[data-agent-idx=\"9\"]",
                      "tag": "a",
                      "text": "视频",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 346,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 10,
                      "href": "https://cn.bing.com/academic/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC4",
                      "index": 10,
                      "label": "学术",
                      "name": "学术",
                      "role": "link",
                      "selector": "[data-agent-idx=\"10\"]",
                      "tag": "a",
                      "text": "学术",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 408,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 11,
                      "href": "https://cn.bing.com/dict/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC6",
                      "index": 11,
                      "label": "词典",
                      "name": "词典",
                      "role": "link",
                      "selector": "[data-agent-idx=\"11\"]",
                      "tag": "a",
                      "text": "词典",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 470,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 12,
                      "href": "https://cn.bing.com/maps?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC7",
                      "index": 12,
                      "label": "地图",
                      "name": "地图",
                      "role": "link",
                      "selector": "[data-agent-idx=\"12\"]",
                      "tag": "a",
                      "text": "地图",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 54,
                        "x": 532,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 13,
                      "href": "javascript:void(0);",
                      "index": 13,
                      "label": "更多",
                      "name": "更多",
                      "role": "button",
                      "selector": "[data-agent-idx=\"13\"]",
                      "tag": "a",
                      "text": "更多",
                      "type": "",
                      "value": ""
                    }
                  ],
                  "dynamic": true,
                  "evidence_stage": "user_comments",
                  "form_fields": [
                    {
                      "bbox": {
                        "height": 44,
                        "width": 571,
                        "x": 193,
                        "y": 50
                      },
                      "disabled": false,
                      "element_id": 4,
                      "href": "",
                      "index": 4,
                      "label": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "name": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "role": "searchbox",
                      "selector": "[data-agent-idx=\"4\"]",
                      "tag": "input",
                      "text": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "type": "search",
                      "value": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫"
                    }
                  ],
                  "interactable_elements": [
                    {
                      "bbox": {
                        "height": 32,
                        "width": 86,
                        "x": 0,
                        "y": 46
                      },
                      "disabled": false,
                      "element_id": 0,
                      "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                      "index": 0,
                      "label": "跳至内容",
                      "name": "跳至内容",
                      "role": "button",
                      "selector": "[data-agent-idx=\"0\"]",
                      "tag": "a",
                      "text": "跳至内容",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 32,
                        "width": 112,
                        "x": 0,
                        "y": 46
                      },
                      "disabled": false,
                      "element_id": 1,
                      "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                      "index": 1,
                      "label": "辅助功能反馈",
                      "name": "辅助功能反馈",
                      "role": "button",
                      "selector": "[data-agent-idx=\"1\"]",
                      "tag": "a",
                      "text": "辅助功能反馈",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 40,
                        "width": 154,
                        "x": 0,
                        "y": 48
                      },
                      "disabled": false,
                      "element_id": 2,
                      "href": "https://cn.bing.com/?FORM=Z9FD1",
                      "index": 2,
                      "label": "",
                      "name": "",
                      "role": "link",
                      "selector": "[data-agent-idx=\"2\"]",
                      "tag": "a",
                      "text": "",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 40,
                        "width": 40,
                        "x": 164,
                        "y": 52
                      },
                      "disabled": false,
                      "element_id": 3,
                      "href": "",
                      "index": 3,
                      "label": "搜索",
                      "name": "搜索",
                      "role": "button",
                      "selector": "[data-agent-idx=\"3\"]",
                      "tag": "input",
                      "text": "搜索",
                      "type": "submit",
                      "value": "搜索"
                    },
                    {
                      "bbox": {
                        "height": 44,
                        "width": 571,
                        "x": 193,
                        "y": 50
                      },
                      "disabled": false,
                      "element_id": 4,
                      "href": "",
                      "index": 4,
                      "label": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "name": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "role": "searchbox",
                      "selector": "[data-agent-idx=\"4\"]",
                      "tag": "input",
                      "text": "在此处输入你的搜索 — 输入时会显示搜索建议",
                      "type": "search",
                      "value": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫"
                    },
                    {
                      "bbox": {
                        "height": 50,
                        "width": 50,
                        "x": 1198,
                        "y": 48
                      },
                      "disabled": false,
                      "element_id": 5,
                      "href": "javascript:void(0)",
                      "index": 5,
                      "label": "",
                      "name": "",
                      "role": "link",
                      "selector": "[data-agent-idx=\"5\"]",
                      "tag": "a",
                      "text": "",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 26,
                        "width": 59,
                        "x": 227,
                        "y": 18
                      },
                      "disabled": false,
                      "element_id": 6,
                      "href": "",
                      "index": 6,
                      "label": "国际版",
                      "name": "国际版",
                      "role": "div",
                      "selector": "[data-agent-idx=\"6\"]",
                      "tag": "div",
                      "text": "国际版",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 160,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 7,
                      "href": "https://cn.bing.com/?scope=web&FORM=HDRSC1",
                      "index": 7,
                      "label": "网页",
                      "name": "网页",
                      "role": "link",
                      "selector": "[data-agent-idx=\"7\"]",
                      "tag": "a",
                      "text": "网页",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 222,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 8,
                      "href": "https://cn.bing.com/images/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC2",
                      "index": 8,
                      "label": "图片",
                      "name": "图片",
                      "role": "link",
                      "selector": "[data-agent-idx=\"8\"]",
                      "tag": "a",
                      "text": "图片",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 284,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 9,
                      "href": "https://cn.bing.com/videos/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC3",
                      "index": 9,
                      "label": "视频",
                      "name": "视频",
                      "role": "link",
                      "selector": "[data-agent-idx=\"9\"]",
                      "tag": "a",
                      "text": "视频",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 346,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 10,
                      "href": "https://cn.bing.com/academic/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC4",
                      "index": 10,
                      "label": "学术",
                      "name": "学术",
                      "role": "link",
                      "selector": "[data-agent-idx=\"10\"]",
                      "tag": "a",
                      "text": "学术",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 408,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 11,
                      "href": "https://cn.bing.com/dict/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC6",
                      "index": 11,
                      "label": "词典",
                      "name": "词典",
                      "role": "link",
                      "selector": "[data-agent-idx=\"11\"]",
                      "tag": "a",
                      "text": "词典",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 38,
                        "x": 470,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 12,
                      "href": "https://cn.bing.com/maps?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC7",
                      "index": 12,
                      "label": "地图",
                      "name": "地图",
                      "role": "link",
                      "selector": "[data-agent-idx=\"12\"]",
                      "tag": "a",
                      "text": "地图",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 54,
                        "x": 532,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 13,
                      "href": "javascript:void(0);",
                      "index": 13,
                      "label": "更多",
                      "name": "更多",
                      "role": "button",
                      "selector": "[data-agent-idx=\"13\"]",
                      "tag": "a",
                      "text": "更多",
                      "type": "",
                      "value": ""
                    }
                  ],
                  "screenshot_path": "runs/screenshots/d3-ec5539de.png",
                  "source": "general",
                  "status": 200,
                  "visible_buttons": [
                    {
                      "bbox": {
                        "height": 32,
                        "width": 86,
                        "x": 0,
                        "y": 46
                      },
                      "disabled": false,
                      "element_id": 0,
                      "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                      "index": 0,
                      "label": "跳至内容",
                      "name": "跳至内容",
                      "role": "button",
                      "selector": "[data-agent-idx=\"0\"]",
                      "tag": "a",
                      "text": "跳至内容",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 32,
                        "width": 112,
                        "x": 0,
                        "y": 46
                      },
                      "disabled": false,
                      "element_id": 1,
                      "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                      "index": 1,
                      "label": "辅助功能反馈",
                      "name": "辅助功能反馈",
                      "role": "button",
                      "selector": "[data-agent-idx=\"1\"]",
                      "tag": "a",
                      "text": "辅助功能反馈",
                      "type": "",
                      "value": ""
                    },
                    {
                      "bbox": {
                        "height": 40,
                        "width": 40,
                        "x": 164,
                        "y": 52
                      },
                      "disabled": false,
                      "element_id": 3,
                      "href": "",
                      "index": 3,
                      "label": "搜索",
                      "name": "搜索",
                      "role": "button",
                      "selector": "[data-agent-idx=\"3\"]",
                      "tag": "input",
                      "text": "搜索",
                      "type": "submit",
                      "value": "搜索"
                    },
                    {
                      "bbox": {
                        "height": 30,
                        "width": 54,
                        "x": 532,
                        "y": 110
                      },
                      "disabled": false,
                      "element_id": 13,
                      "href": "javascript:void(0);",
                      "index": 13,
                      "label": "更多",
                      "name": "更多",
                      "role": "button",
                      "selector": "[data-agent-idx=\"13\"]",
                      "tag": "a",
                      "text": "更多",
                      "type": "",
                      "value": ""
                    }
                  ],
                  "visual_summary": "Screenshot captured for multimodal grounding; use provider analysis when configured."
                },
                "human_review_required": false,
                "ok": true,
                "text": "跳至内容 辅助功能反馈 国内版国际版 网页图片视频学术词典地图 更多",
                "title": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫 - 搜索",
                "url": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB"
              },
              "verdict": {
                "checks": [
                  {
                    "detail": "ok",
                    "name": "action_ok",
                    "pass": true
                  },
                  {
                    "detail": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB",
                    "name": "page_reachable",
                    "pass": true
                  },
                  {
                    "detail": "evidence=1 fields=10",
                    "name": "evidence_or_fields",
                    "pass": true
                  }
                ],
                "ok": true,
                "retry_hint": null,
                "score": 1
              }
            }
          ]
        },
        "metrics": {
          "browser_state_goal_match": 0,
          "checklist_coverage": 0.6,
          "final_answer_groundedness": 1,
          "source_citation_correctness": 1,
          "step_accuracy": 1,
          "task_success": 1
        },
        "ok": true,
        "plan": {
          "actions": [
            {
              "reason": "当前已经到达搜索/结果页，先抽取候选链接或启用垂直候选恢复。",
              "sensitive": false,
              "target": "",
              "tool": "collect_links",
              "value": "1000元以内 降噪耳机 推荐 通勤 办公 头戴式 入耳式 型号 价格"
            },
            {
              "reason": "深入读取当前候选链接中的商品页和专业评测，提取型号参数、价格定位、降噪/舒适度/办公通勤表现和主要短板。",
              "sensitive": false,
              "target": "",
              "tool": "deep_read_candidates",
              "value": ""
            },
            {
              "reason": "搜索具体候选型号的用户评价和差评，重点关注通勤办公场景下的佩戴舒适度、降噪、底噪、夹头、连接稳定性和常见故障。",
              "sensitive": false,
              "target": "",
              "tool": "search_web",
              "value": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫"
            }
          ],
          "confidence": 0.68,
          "summary": "shopping workflow for: 推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论"
        },
        "report": {
          "candidates": [
            {
              "confidence": 0.72,
              "name": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
              "support": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
              "url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908"
            },
            {
              "confidence": 0.72,
              "name": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
              "support": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
              "url": "https://www.whathifi.com/reviews/sony-wh-ch720n"
            },
            {
              "confidence": 0.72,
              "name": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
              "support": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
              "url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus"
            },
            {
              "confidence": 0.72,
              "name": "Soundcore Space Q45 adaptive noise cancelling headphones product page",
              "support": "Soundcore Space Q45 adaptive noise cancelling headphones product page",
              "url": "https://www.soundcore.com/products/space-q45-a3040011"
            },
            {
              "confidence": 0.72,
              "name": "Sony WH-CH720N headphone official product page",
              "support": "Sony WH-CH720N headphone official product page",
              "url": "https://www.sony.jp/headphone/products/WH-CH720N/"
            }
          ],
          "citations": [
            {
              "claim": "Candidate link: RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
              "confidence": 0.72,
              "source_url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908"
            },
            {
              "claim": "Candidate link: What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
              "confidence": 0.72,
              "source_url": "https://www.whathifi.com/reviews/sony-wh-ch720n"
            },
            {
              "claim": "Candidate link: Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
              "confidence": 0.72,
              "source_url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus"
            },
            {
              "claim": "Candidate link: Soundcore Space Q45 adaptive noise cancelling headphones product page",
              "confidence": 0.72,
              "source_url": "https://www.soundcore.com/products/space-q45-a3040011"
            },
            {
              "claim": "Candidate link: Sony WH-CH720N headphone official product page",
              "confidence": 0.72,
              "source_url": "https://www.sony.jp/headphone/products/WH-CH720N/"
            },
            {
              "claim": "Deep candidate read: RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
              "confidence": 0.78,
              "source_url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908"
            },
            {
              "claim": "Deep candidate read: What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
              "confidence": 0.78,
              "source_url": "https://www.whathifi.com/reviews/sony-wh-ch720n"
            },
            {
              "claim": "Deep candidate read: Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
              "confidence": 0.78,
              "source_url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus"
            },
            {
              "claim": "Search results for Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫",
              "confidence": 0.65,
              "source_url": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB"
            }
          ],
          "comparison_matrix": [
            {
              "description": "What Hi-Fi? reviews the Sony WH-CH720N noise-cancelling headphones: expert testing and our verdict on sound quality, comfort, features and value – plus our star rating and alternatives to consider",
              "evidence_strength": 0.78,
              "fit_notes": "derived_from_deep_candidate_page",
              "name": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
              "price_signal": "not_found",
              "review_signal": "Skip to main content What Hi-Fi? THE WORLD'S #1 TECH BUYER'S GUIDE UK Edition RSS SUBSCRIBE Sign in News Reviews Best Buys Features Awards Hi-Fi Headphones TV & Home Cinema More Ju",
              "score": 53.6,
              "score_reasons": [
                "review evidence",
                "ANC/noise evidence",
                "comfort evidence"
              ],
              "snippet": "Skip to main content What Hi-Fi? THE WORLD'S #1 TECH BUYER'S GUIDE UK Edition RSS SUBSCRIBE Sign in News Reviews Best Buys Features Awards Hi-Fi Headphones TV & Home Cinema More Jump To: Price Build quality & comfort Fea",
              "source_status": 200,
              "title": "Sony WH-CH720N review: supremely affordable over-ears with punchy sound and decent ANC | What Hi-Fi?",
              "url": "https://www.whathifi.com/reviews/sony-wh-ch720n"
            },
            {
              "description": "The Anker Soundcore Space Q45 Wireless are better headphones than the Sony WH-CH720N Wireless. Both headphones are comfortable, and the Anker come with a carrying case to protect the headphones when not in use. They also offer significantly better noise isolation performance and support LDAC for higher-resolution audio.",
              "evidence_strength": 0.78,
              "fit_notes": "derived_from_deep_candidate_page",
              "name": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
              "price_signal": "not_found",
              "review_signal": "Headphones Products In The Lab Forums Newsletters LOGIN JOIN NOW BEST Headphones Noise Cancelling Wireless Earbuds Gaming Over-Ear Noise Cancelling Earbuds Running PC Gaming Apple ",
              "score": 43.6,
              "score_reasons": [
                "ANC/noise evidence",
                "comfort evidence",
                "comparison evidence"
              ],
              "snippet": "Headphones Products In The Lab Forums Newsletters LOGIN JOIN NOW BEST Headphones Noise Cancelling Wireless Earbuds Gaming Over-Ear Noise Cancelling Earbuds Running PC Gaming Apple Wireless Bone Conduction And Open-Ear Wi",
              "source_status": 200,
              "title": "Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless: Which Headphones Are Better? - RTINGS.com",
              "url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-vs-sony-wh-ch720n-wireless/34852/38908"
            },
            {
              "description": "Hassle-free phone calls with DNN noise cancellation technology\nExperience the upgraded noise cancellation with ANC depth of up to -43dB\nUp to 49 hours continuous playback when ANC off\nPersonalize your listening experience with customizable EQ , soothing sounds via Edifier Connect APP",
              "evidence_strength": 0.78,
              "fit_notes": "derived_from_deep_candidate_page",
              "name": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
              "price_signal": "not_found",
              "review_signal": "",
              "score": 27.6,
              "score_reasons": [
                "ANC/noise evidence"
              ],
              "snippet": "",
              "source_status": 200,
              "title": "Wireless Noise Cancellation Over-Ear Headphones | W820NB Plus - Edifier USA",
              "url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus"
            }
          ],
          "decision_criteria": [
            {
              "evidence_to_collect": "价格区间、促销和保修",
              "name": "价格",
              "why_it_matters": "控制预算并比较性价比"
            },
            {
              "evidence_to_collect": "佩戴形态和使用场景",
              "name": "类型",
              "why_it_matters": "入耳式、头戴式、开放式适合不同场景"
            },
            {
              "evidence_to_collect": "评测结论和用户反馈",
              "name": "核心体验",
              "why_it_matters": "音质、降噪、舒适度决定长期满意度"
            }
          ],
          "multimodal_notes": [],
          "next_actions": [
            "Review the top candidates and run a deeper extraction workflow on the best matches."
          ],
          "reasoning_outline": [
            "先把推荐问题拆成预算、类型/场景、品牌型号、核心体验、风险点五类证据。",
            "先用榜单/评测搜索建立候选池，再用具体型号对比搜索交叉验证。",
            "深读候选页面，优先抽取价格、专业评测、用户反馈和缺点。",
            "最终按证据强弱而不是关键词命中顺序给出推荐。"
          ],
          "recommendations": [
            {
              "name": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
              "rank": 1,
              "reason": "Prioritize products with repeated review evidence and clear specs. Evidence score 53.6: review evidence, ANC/noise evidence, comfort evidence",
              "score": 53.6,
              "url": "https://www.whathifi.com/reviews/sony-wh-ch720n"
            },
            {
              "name": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
              "rank": 2,
              "reason": "Prioritize products with repeated review evidence and clear specs. Evidence score 43.6: ANC/noise evidence, comfort evidence, comparison evidence",
              "score": 43.6,
              "url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-vs-sony-wh-ch720n-wireless/34852/38908"
            },
            {
              "name": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
              "rank": 3,
              "reason": "Prioritize products with repeated review evidence and clear specs. Evidence score 27.6: ANC/noise evidence",
              "score": 27.6,
              "url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus"
            }
          ],
          "search_plan": [
            {
              "evidence_stage": "user_comments",
              "purpose": "搜索具体候选型号的用户评价和差评，重点关注通勤办公场景下的佩戴舒适度、降噪、底噪、夹头、连接稳定性和常见故障。",
              "query": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫",
              "source": "general"
            }
          ],
          "source_readings": [
            {
              "description": "The Anker Soundcore Space Q45 Wireless are better headphones than the Sony WH-CH720N Wireless. Both headphones are comfortable, and the Anker come with a carrying case to protect the headphones when not in use. They also offer significantly better noise isolation performance and support LDAC for higher-resolution audio.",
              "name": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
              "ok": true,
              "price_signal": "",
              "rank": 1,
              "source": "shopping",
              "status": 200,
              "text": "Headphones Products In The Lab Forums Newsletters LOGIN JOIN NOW BEST Headphones Noise Cancelling Wireless Earbuds Gaming Over-Ear Noise Cancelling Earbuds Running PC Gaming Apple Wireless Bone Conduction And Open-Ear Wireless Gaming Wired Wireless Earbuds Under $100 On-Ear In-Ears Xbox Series X/S Wireless Earbuds For Android Small Ear Earbuds Music TOOLS Compare Results Table Tool Review List Review Index Graph Review Pipeline Vote Custom Ratings POPULAR Sony WH-1000XM6 Sony WF-1000XM6 Audeze Maxwell 2 Razer BlackShark V3 Pro Bose QuietComfort Ultra Headphones (2nd Gen) Anker Soundcore Space A40 Truly Wireless Samsung Galaxy Buds4 Pro Technics EAH-AZ100 Apple AirPods Pro 3 Anker Soundcore Space Q45 Wireless Sennheiser HDB 630 Sony WH-1000XM4 Wireless Sony WF-1000XM5 Truly Wireless Sennheiser MOMENTUM 4 Wireless SteelSeries Arctis Nova 7 Wireless [7, 7P, 7X] Bose QuietComfort Ultra Earbuds (2nd Gen) CMF Buds Pro 2 Nothing Ear Sony WH-1000XM5 Wireless Anker Soundcore Life Q20 2024 889 HEADPHONES BOUGHT AND TESTED Supported by you via membership, and when you purchase through links on our site, we may earn an affiliate commission. Home Headphones Compare Notice: We've revamped our membership program. FEEDBACK Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless Which Headphones Are Better? Top Main Differences Sound Sound Profile Frequency Response Consistency Raw Frequency Response Bass Profile: Target Compliance Mid-Range Profile: Target Compliance Treble Profile: Target Compliance Peaks/Dips Stereo Mismatch Cumulative Spectral Decay PRTF Harmonic Distortion Electrical Aspects Virtual Soundstage Test Settings Design Style Comfort Controls Portability Case Build Quality Stability Headshots 1 Headshots 2 Top In The Box Isolation Noise Isolation - Full Range Noise Isolation - Common Scenarios Noise Isolation - Voice Handling ANC Wind Handling Leakage Microphone Microphone Style Recording Quality Noise Handling Active Features Battery App Support Connectivity Wired Connection Bluetooth Connection Wireless Connection (Dongle) PC Compatibility PlayStation Compatibility Xbox Compatibility Base/Dock Comments PRODUCTS Anker Soundcore Space Q45 Wireless Sony WH-CH720N Wireless Tested using Methodology v2.2 Updated May 28, 2026 01:56 AM SearchingFinding store Tested using Methodology v2.2 Updated Apr 16, 2026 02:29 AM SearchingFinding store Type Over-ear Noise Cancelling Yes Enclosure Closed-Back Bass Amount Emphasized (3 dB) Wireless Yes Treble Amount Balanced (0 dB",
              "title": "Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless: Which Headphones Are Better? - RTINGS.com",
              "url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-vs-sony-wh-ch720n-wireless/34852/38908"
            },
            {
              "description": "What Hi-Fi? reviews the Sony WH-CH720N noise-cancelling headphones: expert testing and our verdict on sound quality, comfort, features and value – plus our star rating and alternatives to consider",
              "name": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
              "ok": true,
              "price_signal": "",
              "rank": 2,
              "source": "shopping",
              "status": 200,
              "text": "Skip to main content What Hi-Fi? THE WORLD'S #1 TECH BUYER'S GUIDE UK Edition RSS SUBSCRIBE Sign in News Reviews Best Buys Features Awards Hi-Fi Headphones TV & Home Cinema More Jump To: Price Build quality & comfort Features Sound Verdict Tester's notes Also consider TRENDING Best Buys 50th Anniversary Best wireless earbuds Best soundbars Best speakers Headphones Wireless Headphones Sony WH-CH720N review What Hi-Fi? Awards 2025 winner. A truly affordable pair of over-ear headphones that delivers great noise-cancelling Tested at £99 / $129 / AU$259 Reviews By What Hi-Fi? last updated 16 October 2025 2 Comments When you purchase through links on our site, we may earn an affiliate commission. Here’s how it works. (Image credit: © What Hi-Fi?) What Hi-Fi? Verdict Sony has done it again. With their pleasing build quality and punchy sound, the WH-CH720N offers a truly budget bargain for those looking for a great pair of affordable ANC headphones £65 at Amazon £69 at Currys £74.99 at Sony UK £75 at Smart Home Sounds Pros + Forceful, robust sound presentation + Decent ANC for the price + Solid build quality Cons - A little over-enthusiastic in the bass - No case or foldability Best picks for you Best cheap noise-cancelling headphones 2026: expert-tested recommendations Best over-ear headphones 2026: wired and wireless pairs tested by our in-house experts Best noise-cancelling headphones 2026 – tested by our in-house review experts Why you can trust What Hi-Fi? Our expert team reviews products in dedicated test rooms, to help you make the best choice for your budget. Find out more about how we test. We've said this last year and we'll say it again: Sony is, at the moment, the Manchester City of the wireless headphones world, dominating the competition over the past few years with hit after five-star hit. From the budget WF-C500 wireless earbuds to the exceptional WH-1000XM5 over-ears, Sony has been hoovering up Awards and five-star ratings like the Sky Blues monopolise Premier League titles. We know how good Sony can be on the premium side, but the WH-CH720N – which retains its What Hi-Fi? Award as the best budget wireless headphones – fill a gap in the market by offering active noise-cancellation (ANC), good build quality and even better sound at a reasonable price. These are designed as a pair of cans for those who aren’t keen on forking out a few hundred quid for a premium pair of over-ears, but equally don’t want to miss out on features such as ANC or suffer a",
              "title": "Sony WH-CH720N review: supremely affordable over-ears with punchy sound and decent ANC | What Hi-Fi?",
              "url": "https://www.whathifi.com/reviews/sony-wh-ch720n"
            },
            {
              "description": "Hassle-free phone calls with DNN noise cancellation technology\nExperience the upgraded noise cancellation with ANC depth of up to -43dB\nUp to 49 hours continuous playback when ANC off\nPersonalize your listening experience with customizable EQ , soothing sounds via Edifier Connect APP",
              "name": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
              "ok": true,
              "price_signal": "",
              "rank": 3,
              "source": "shopping",
              "status": 200,
              "text": "",
              "title": "Wireless Noise Cancellation Over-Ear Headphones | W820NB Plus - Edifier USA",
              "url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus"
            }
          ],
          "subquestions": [
            "预算内有哪些主流品牌和型号反复出现在评测/榜单中？",
            "这些型号分别属于什么类型，是否适合通勤和办公室？",
            "价格、音质、降噪、舒适度和用户评价有哪些可验证线索？",
            "每个候选的主要短板和购买风险是什么？"
          ],
          "summary": "Workflow 'shopping_workflow' completed for '推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论'. Collected 5 candidate links and 9 evidence items.",
          "uncertainties": [
            "This MVP uses rule-based extraction, so ranking quality should be manually reviewed."
          ],
          "video_digest": {}
        },
        "run_id": "f27fa595-c466-4bdb-b42f-c2cfec482cfe",
        "start_url": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC",
        "steps": [
          {
            "action": "collect_links",
            "detail": {
              "action": "collect_links",
              "error": null,
              "evidence": [
                {
                  "claim": "Candidate link: RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
                  "confidence": 0.72,
                  "evidence_id": "7a65de7d-fc1c-4652-be3a-550201a657f8",
                  "metadata": {},
                  "source_type": "shopping",
                  "source_url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
                  "support": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison"
                },
                {
                  "claim": "Candidate link: What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
                  "confidence": 0.72,
                  "evidence_id": "b44facc5-a624-4354-9e8f-fbee54211cf9",
                  "metadata": {},
                  "source_type": "shopping",
                  "source_url": "https://www.whathifi.com/reviews/sony-wh-ch720n",
                  "support": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review"
                },
                {
                  "claim": "Candidate link: Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
                  "confidence": 0.72,
                  "evidence_id": "d726928c-df65-4bde-9fae-707f3013374e",
                  "metadata": {},
                  "source_type": "shopping",
                  "source_url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
                  "support": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page"
                },
                {
                  "claim": "Candidate link: Soundcore Space Q45 adaptive noise cancelling headphones product page",
                  "confidence": 0.72,
                  "evidence_id": "60900630-ff06-4d65-8570-14034f4307f3",
                  "metadata": {},
                  "source_type": "shopping",
                  "source_url": "https://www.soundcore.com/products/space-q45-a3040011",
                  "support": "Soundcore Space Q45 adaptive noise cancelling headphones product page"
                },
                {
                  "claim": "Candidate link: Sony WH-CH720N headphone official product page",
                  "confidence": 0.72,
                  "evidence_id": "47db36bc-e449-4756-a9dd-377c752f7cd0",
                  "metadata": {},
                  "source_type": "shopping",
                  "source_url": "https://www.sony.jp/headphone/products/WH-CH720N/",
                  "support": "Sony WH-CH720N headphone official product page"
                }
              ],
              "fallback_used": null,
              "fields": {
                "accessibility_tree": [],
                "dynamic": true,
                "evidence_stage": "candidate_pool",
                "form_fields": [],
                "interactable_elements": [],
                "links": [
                  {
                    "href": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
                    "text": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison"
                  },
                  {
                    "href": "https://www.whathifi.com/reviews/sony-wh-ch720n",
                    "text": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review"
                  },
                  {
                    "href": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
                    "text": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page"
                  },
                  {
                    "href": "https://www.soundcore.com/products/space-q45-a3040011",
                    "text": "Soundcore Space Q45 adaptive noise cancelling headphones product page"
                  },
                  {
                    "href": "https://www.sony.jp/headphone/products/WH-CH720N/",
                    "text": "Sony WH-CH720N headphone official product page"
                  }
                ],
                "query": "1000元以内 降噪耳机 推荐 通勤 办公 头戴式 入耳式 型号 价格",
                "screenshot_path": "runs/screenshots/d1-3f8c8c2d.png",
                "source": "shopping",
                "visible_buttons": [],
                "visual_summary": "Screenshot captured for multimodal grounding; use provider analysis when configured."
              },
              "human_review_required": false,
              "ok": true,
              "text": "",
              "title": "",
              "url": "about:blank"
            },
            "fallback_used": null,
            "node_id": "d1",
            "ok": true,
            "score": 1
          },
          {
            "action": "deep_read_candidates",
            "detail": {
              "action": "deep_read_candidates",
              "error": null,
              "evidence": [
                {
                  "claim": "Deep candidate read: RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
                  "confidence": 0.78,
                  "evidence_id": "3af9d0bb-a2a3-4988-abc2-3141f8dea08f",
                  "metadata": {},
                  "source_type": "shopping",
                  "source_url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
                  "support": "Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless: Which Headphones Are Better? - RTINGS.com The Anker Soundcore Space Q45 Wireless are better headphones than the Sony WH-CH720N Wireless. Both headphones are comfortable, and the Anker come with a carrying case to protect the headphones when not in use. They also offer significantly better noise isolation performance and support LDAC for higher-resolution audio. Headphones Products In The Lab Forums Newsletters LOGIN JOIN NOW BEST Headphones N"
                },
                {
                  "claim": "Deep candidate read: What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
                  "confidence": 0.78,
                  "evidence_id": "072aebca-7320-456a-9d64-e471f2583e11",
                  "metadata": {},
                  "source_type": "shopping",
                  "source_url": "https://www.whathifi.com/reviews/sony-wh-ch720n",
                  "support": "Sony WH-CH720N review: supremely affordable over-ears with punchy sound and decent ANC | What Hi-Fi? What Hi-Fi? reviews the Sony WH-CH720N noise-cancelling headphones: expert testing and our verdict on sound quality, comfort, features and value – plus our star rating and alternatives to consider Skip to main content What Hi-Fi? THE WORLD'S #1 TECH BUYER'S GUIDE UK Edition RSS SUBSCRIBE Sign in News Reviews Best Buys Features Awards Hi-Fi Headphones TV & Home Cinema More Jump To: Price Build qua"
                },
                {
                  "claim": "Deep candidate read: Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
                  "confidence": 0.78,
                  "evidence_id": "9499b412-36b8-4e14-87bb-cca1aae90a3d",
                  "metadata": {},
                  "source_type": "shopping",
                  "source_url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
                  "support": "Wireless Noise Cancellation Over-Ear Headphones | W820NB Plus - Edifier USA Hassle-free phone calls with DNN noise cancellation technology Experience the upgraded noise cancellation with ANC depth of up to -43dB Up to 49 hours continuous playback when ANC off Personalize your listening experience with customizable EQ , soothing sounds via Edifier Connect APP"
                }
              ],
              "fallback_used": null,
              "fields": {
                "accessibility_tree": [],
                "deep_reads": [
                  {
                    "description": "The Anker Soundcore Space Q45 Wireless are better headphones than the Sony WH-CH720N Wireless. Both headphones are comfortable, and the Anker come with a carrying case to protect the headphones when not in use. They also offer significantly better noise isolation performance and support LDAC for higher-resolution audio.",
                    "name": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
                    "ok": true,
                    "price_signal": "",
                    "rank": 1,
                    "source": "shopping",
                    "status": 200,
                    "text": "Headphones Products In The Lab Forums Newsletters LOGIN JOIN NOW BEST Headphones Noise Cancelling Wireless Earbuds Gaming Over-Ear Noise Cancelling Earbuds Running PC Gaming Apple Wireless Bone Conduction And Open-Ear Wireless Gaming Wired Wireless Earbuds Under $100 On-Ear In-Ears Xbox Series X/S Wireless Earbuds For Android Small Ear Earbuds Music TOOLS Compare Results Table Tool Review List Review Index Graph Review Pipeline Vote Custom Ratings POPULAR Sony WH-1000XM6 Sony WF-1000XM6 Audeze Maxwell 2 Razer BlackShark V3 Pro Bose QuietComfort Ultra Headphones (2nd Gen) Anker Soundcore Space A40 Truly Wireless Samsung Galaxy Buds4 Pro Technics EAH-AZ100 Apple AirPods Pro 3 Anker Soundcore Space Q45 Wireless Sennheiser HDB 630 Sony WH-1000XM4 Wireless Sony WF-1000XM5 Truly Wireless Sennheiser MOMENTUM 4 Wireless SteelSeries Arctis Nova 7 Wireless [7, 7P, 7X] Bose QuietComfort Ultra Earbuds (2nd Gen) CMF Buds Pro 2 Nothing Ear Sony WH-1000XM5 Wireless Anker Soundcore Life Q20 2024 889 HEADPHONES BOUGHT AND TESTED Supported by you via membership, and when you purchase through links on our site, we may earn an affiliate commission. Home Headphones Compare Notice: We've revamped our membership program. FEEDBACK Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless Which Headphones Are Better? Top Main Differences Sound Sound Profile Frequency Response Consistency Raw Frequency Response Bass Profile: Target Compliance Mid-Range Profile: Target Compliance Treble Profile: Target Compliance Peaks/Dips Stereo Mismatch Cumulative Spectral Decay PRTF Harmonic Distortion Electrical Aspects Virtual Soundstage Test Settings Design Style Comfort Controls Portability Case Build Quality Stability Headshots 1 Headshots 2 Top In The Box Isolation Noise Isolation - Full Range Noise Isolation - Common Scenarios Noise Isolation - Voice Handling ANC Wind Handling Leakage Microphone Microphone Style Recording Quality Noise Handling Active Features Battery App Support Connectivity Wired Connection Bluetooth Connection Wireless Connection (Dongle) PC Compatibility PlayStation Compatibility Xbox Compatibility Base/Dock Comments PRODUCTS Anker Soundcore Space Q45 Wireless Sony WH-CH720N Wireless Tested using Methodology v2.2 Updated May 28, 2026 01:56 AM SearchingFinding store Tested using Methodology v2.2 Updated Apr 16, 2026 02:29 AM SearchingFinding store Type Over-ear Noise Cancelling Yes Enclosure Closed-Back Bass Amount Emphasized (3 dB) Wireless Yes Treble Amount Balanced (0 dB",
                    "title": "Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless: Which Headphones Are Better? - RTINGS.com",
                    "url": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-vs-sony-wh-ch720n-wireless/34852/38908"
                  },
                  {
                    "description": "What Hi-Fi? reviews the Sony WH-CH720N noise-cancelling headphones: expert testing and our verdict on sound quality, comfort, features and value – plus our star rating and alternatives to consider",
                    "name": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
                    "ok": true,
                    "price_signal": "",
                    "rank": 2,
                    "source": "shopping",
                    "status": 200,
                    "text": "Skip to main content What Hi-Fi? THE WORLD'S #1 TECH BUYER'S GUIDE UK Edition RSS SUBSCRIBE Sign in News Reviews Best Buys Features Awards Hi-Fi Headphones TV & Home Cinema More Jump To: Price Build quality & comfort Features Sound Verdict Tester's notes Also consider TRENDING Best Buys 50th Anniversary Best wireless earbuds Best soundbars Best speakers Headphones Wireless Headphones Sony WH-CH720N review What Hi-Fi? Awards 2025 winner. A truly affordable pair of over-ear headphones that delivers great noise-cancelling Tested at £99 / $129 / AU$259 Reviews By What Hi-Fi? last updated 16 October 2025 2 Comments When you purchase through links on our site, we may earn an affiliate commission. Here’s how it works. (Image credit: © What Hi-Fi?) What Hi-Fi? Verdict Sony has done it again. With their pleasing build quality and punchy sound, the WH-CH720N offers a truly budget bargain for those looking for a great pair of affordable ANC headphones £65 at Amazon £69 at Currys £74.99 at Sony UK £75 at Smart Home Sounds Pros + Forceful, robust sound presentation + Decent ANC for the price + Solid build quality Cons - A little over-enthusiastic in the bass - No case or foldability Best picks for you Best cheap noise-cancelling headphones 2026: expert-tested recommendations Best over-ear headphones 2026: wired and wireless pairs tested by our in-house experts Best noise-cancelling headphones 2026 – tested by our in-house review experts Why you can trust What Hi-Fi? Our expert team reviews products in dedicated test rooms, to help you make the best choice for your budget. Find out more about how we test. We've said this last year and we'll say it again: Sony is, at the moment, the Manchester City of the wireless headphones world, dominating the competition over the past few years with hit after five-star hit. From the budget WF-C500 wireless earbuds to the exceptional WH-1000XM5 over-ears, Sony has been hoovering up Awards and five-star ratings like the Sky Blues monopolise Premier League titles. We know how good Sony can be on the premium side, but the WH-CH720N – which retains its What Hi-Fi? Award as the best budget wireless headphones – fill a gap in the market by offering active noise-cancellation (ANC), good build quality and even better sound at a reasonable price. These are designed as a pair of cans for those who aren’t keen on forking out a few hundred quid for a premium pair of over-ears, but equally don’t want to miss out on features such as ANC or suffer a",
                    "title": "Sony WH-CH720N review: supremely affordable over-ears with punchy sound and decent ANC | What Hi-Fi?",
                    "url": "https://www.whathifi.com/reviews/sony-wh-ch720n"
                  },
                  {
                    "description": "Hassle-free phone calls with DNN noise cancellation technology\nExperience the upgraded noise cancellation with ANC depth of up to -43dB\nUp to 49 hours continuous playback when ANC off\nPersonalize your listening experience with customizable EQ , soothing sounds via Edifier Connect APP",
                    "name": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
                    "ok": true,
                    "price_signal": "",
                    "rank": 3,
                    "source": "shopping",
                    "status": 200,
                    "text": "",
                    "title": "Wireless Noise Cancellation Over-Ear Headphones | W820NB Plus - Edifier USA",
                    "url": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus"
                  }
                ],
                "dynamic": true,
                "evidence_stage": "comparative_reviews",
                "form_fields": [],
                "interactable_elements": [],
                "links": [
                  {
                    "href": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
                    "text": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison"
                  },
                  {
                    "href": "https://www.whathifi.com/reviews/sony-wh-ch720n",
                    "text": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review"
                  },
                  {
                    "href": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
                    "text": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page"
                  },
                  {
                    "href": "https://www.soundcore.com/products/space-q45-a3040011",
                    "text": "Soundcore Space Q45 adaptive noise cancelling headphones product page"
                  },
                  {
                    "href": "https://www.sony.jp/headphone/products/WH-CH720N/",
                    "text": "Sony WH-CH720N headphone official product page"
                  }
                ],
                "screenshot_path": "runs/screenshots/d2-39306bee.png",
                "source": "shopping",
                "visible_buttons": [],
                "visual_summary": "Screenshot captured for multimodal grounding; use provider analysis when configured."
              },
              "human_review_required": false,
              "ok": true,
              "text": "Headphones Products In The Lab Forums Newsletters LOGIN JOIN NOW BEST Headphones Noise Cancelling Wireless Earbuds Gaming Over-Ear Noise Cancelling Earbuds Running PC Gaming Apple Wireless Bone Conduction And Open-Ear Wireless Gaming Wired Wireless Earbuds Under $100 On-Ear In-Ears Xbox Series X/S Wireless Earbuds For Android Small Ear Earbuds Music TOOLS Compare Results Table Tool Review List Review Index Graph Review Pipeline Vote Custom Ratings POPULAR Sony WH-1000XM6 Sony WF-1000XM6 Audeze Maxwell 2 Razer BlackShark V3 Pro Bose QuietComfort Ultra Headphones (2nd Gen) Anker Soundcore Space A40 Truly Wireless Samsung Galaxy Buds4 Pro Technics EAH-AZ100 Apple AirPods Pro 3 Anker Soundcore Space Q45 Wireless Sennheiser HDB 630 Sony WH-1000XM4 Wireless Sony WF-1000XM5 Truly Wireless Sennheiser MOMENTUM 4 Wireless SteelSeries Arctis Nova 7 Wireless [7, 7P, 7X] Bose QuietComfort Ultra Earbuds (2nd Gen) CMF Buds Pro 2 Nothing Ear Sony WH-1000XM5 Wireless Anker Soundcore Life Q20 2024 889 HEADPHONES BOUGHT AND TESTED Supported by you via membership, and when you purchase through links on our site, we may earn an affiliate commission. Home Headphones Compare Notice: We've revamped our membership program. FEEDBACK Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless Which Headphones Are Better? Top Main Differences Sound Sound Profile Frequency Response Consistency Raw Frequency Response Bass Profile: Target Compliance Mid-Range Profile: Target Compliance Treble Profile: Target Compliance Peaks/Dips Stereo Mismatch Cumulative Spectral Decay PRTF Harmonic Distortion Electrical Aspects Virtual Soundstage Test Settings Design Style Comfort Controls Portability Case Build Quality Stability Headshots 1 Headshots 2 Top In The Box Isolation Noise Isolation - Full Range Noise Isolation - Common Scenarios Noise Isolation - Voice Handling ANC Wind Handling Leakage Microphone Microphone Style Recording Quality Noise Handling Active Features Battery App Support Connectivity Wired Connection Bluetooth Connection Wireless Connection (Dongle) PC Compatibility PlayStation Compatibility Xbox Compatibility Base/Dock Comments PRODUCTS Anker Soundcore Space Q45 Wireless Sony WH-CH720N Wireless Tested using Methodology v2.2 Updated May 28, 2026 01:56 AM SearchingFinding store Tested using Methodology v2.2 Updated Apr 16, 2026 02:29 AM SearchingFinding store Type Over-ear Noise Cancelling Yes Enclosure Closed-Back Bass Amount Emphasized (3 dB) Wireless Yes Treble Amount Balanced (0 dB Skip to main content What Hi-Fi? THE WORLD'S #1 TECH BUYER'S GUIDE UK Edition RSS SUBSCRIBE Sign in News Reviews Best Buys Features Awards Hi-Fi Headphones TV & Home Cinema More Jump To: Price Build quality & comfort Features Sound Verdict Tester's notes Also consider TRENDING Best Buys 50th Anniversary Best wireless earbuds Best soundbars Best speakers Headphones Wireless Headphones Sony WH-CH720N review What Hi-Fi? Awards 2025 winner. A truly affordable pair of over-ear headphones that delive",
              "title": "",
              "url": "about:blank"
            },
            "fallback_used": null,
            "node_id": "d2",
            "ok": true,
            "score": 1
          },
          {
            "action": "search_web",
            "detail": {
              "action": "search_web",
              "error": null,
              "evidence": [
                {
                  "claim": "Search results for Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫",
                  "confidence": 0.65,
                  "evidence_id": "a390587b-84aa-41ba-8602-6210b05b9212",
                  "metadata": {},
                  "source_type": "general",
                  "source_url": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB",
                  "support": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫 - 搜索"
                }
              ],
              "fallback_used": null,
              "fields": {
                "accessibility_tree": [
                  {
                    "bbox": {
                      "height": 32,
                      "width": 86,
                      "x": 0,
                      "y": 46
                    },
                    "disabled": false,
                    "element_id": 0,
                    "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                    "index": 0,
                    "label": "跳至内容",
                    "name": "跳至内容",
                    "role": "button",
                    "selector": "[data-agent-idx=\"0\"]",
                    "tag": "a",
                    "text": "跳至内容",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 32,
                      "width": 112,
                      "x": 0,
                      "y": 46
                    },
                    "disabled": false,
                    "element_id": 1,
                    "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                    "index": 1,
                    "label": "辅助功能反馈",
                    "name": "辅助功能反馈",
                    "role": "button",
                    "selector": "[data-agent-idx=\"1\"]",
                    "tag": "a",
                    "text": "辅助功能反馈",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 40,
                      "width": 154,
                      "x": 0,
                      "y": 48
                    },
                    "disabled": false,
                    "element_id": 2,
                    "href": "https://cn.bing.com/?FORM=Z9FD1",
                    "index": 2,
                    "label": "",
                    "name": "",
                    "role": "link",
                    "selector": "[data-agent-idx=\"2\"]",
                    "tag": "a",
                    "text": "",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 40,
                      "width": 40,
                      "x": 164,
                      "y": 52
                    },
                    "disabled": false,
                    "element_id": 3,
                    "href": "",
                    "index": 3,
                    "label": "搜索",
                    "name": "搜索",
                    "role": "button",
                    "selector": "[data-agent-idx=\"3\"]",
                    "tag": "input",
                    "text": "搜索",
                    "type": "submit",
                    "value": "搜索"
                  },
                  {
                    "bbox": {
                      "height": 44,
                      "width": 571,
                      "x": 193,
                      "y": 50
                    },
                    "disabled": false,
                    "element_id": 4,
                    "href": "",
                    "index": 4,
                    "label": "在此处输入你的搜索 — 输入时会显示搜索建议",
                    "name": "在此处输入你的搜索 — 输入时会显示搜索建议",
                    "role": "searchbox",
                    "selector": "[data-agent-idx=\"4\"]",
                    "tag": "input",
                    "text": "在此处输入你的搜索 — 输入时会显示搜索建议",
                    "type": "search",
                    "value": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫"
                  },
                  {
                    "bbox": {
                      "height": 50,
                      "width": 50,
                      "x": 1198,
                      "y": 48
                    },
                    "disabled": false,
                    "element_id": 5,
                    "href": "javascript:void(0)",
                    "index": 5,
                    "label": "",
                    "name": "",
                    "role": "link",
                    "selector": "[data-agent-idx=\"5\"]",
                    "tag": "a",
                    "text": "",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 26,
                      "width": 59,
                      "x": 227,
                      "y": 18
                    },
                    "disabled": false,
                    "element_id": 6,
                    "href": "",
                    "index": 6,
                    "label": "国际版",
                    "name": "国际版",
                    "role": "div",
                    "selector": "[data-agent-idx=\"6\"]",
                    "tag": "div",
                    "text": "国际版",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 38,
                      "x": 160,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 7,
                    "href": "https://cn.bing.com/?scope=web&FORM=HDRSC1",
                    "index": 7,
                    "label": "网页",
                    "name": "网页",
                    "role": "link",
                    "selector": "[data-agent-idx=\"7\"]",
                    "tag": "a",
                    "text": "网页",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 38,
                      "x": 222,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 8,
                    "href": "https://cn.bing.com/images/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC2",
                    "index": 8,
                    "label": "图片",
                    "name": "图片",
                    "role": "link",
                    "selector": "[data-agent-idx=\"8\"]",
                    "tag": "a",
                    "text": "图片",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 38,
                      "x": 284,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 9,
                    "href": "https://cn.bing.com/videos/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC3",
                    "index": 9,
                    "label": "视频",
                    "name": "视频",
                    "role": "link",
                    "selector": "[data-agent-idx=\"9\"]",
                    "tag": "a",
                    "text": "视频",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 38,
                      "x": 346,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 10,
                    "href": "https://cn.bing.com/academic/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC4",
                    "index": 10,
                    "label": "学术",
                    "name": "学术",
                    "role": "link",
                    "selector": "[data-agent-idx=\"10\"]",
                    "tag": "a",
                    "text": "学术",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 38,
                      "x": 408,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 11,
                    "href": "https://cn.bing.com/dict/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC6",
                    "index": 11,
                    "label": "词典",
                    "name": "词典",
                    "role": "link",
                    "selector": "[data-agent-idx=\"11\"]",
                    "tag": "a",
                    "text": "词典",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 38,
                      "x": 470,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 12,
                    "href": "https://cn.bing.com/maps?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC7",
                    "index": 12,
                    "label": "地图",
                    "name": "地图",
                    "role": "link",
                    "selector": "[data-agent-idx=\"12\"]",
                    "tag": "a",
                    "text": "地图",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 54,
                      "x": 532,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 13,
                    "href": "javascript:void(0);",
                    "index": 13,
                    "label": "更多",
                    "name": "更多",
                    "role": "button",
                    "selector": "[data-agent-idx=\"13\"]",
                    "tag": "a",
                    "text": "更多",
                    "type": "",
                    "value": ""
                  }
                ],
                "dynamic": true,
                "evidence_stage": "user_comments",
                "form_fields": [
                  {
                    "bbox": {
                      "height": 44,
                      "width": 571,
                      "x": 193,
                      "y": 50
                    },
                    "disabled": false,
                    "element_id": 4,
                    "href": "",
                    "index": 4,
                    "label": "在此处输入你的搜索 — 输入时会显示搜索建议",
                    "name": "在此处输入你的搜索 — 输入时会显示搜索建议",
                    "role": "searchbox",
                    "selector": "[data-agent-idx=\"4\"]",
                    "tag": "input",
                    "text": "在此处输入你的搜索 — 输入时会显示搜索建议",
                    "type": "search",
                    "value": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫"
                  }
                ],
                "interactable_elements": [
                  {
                    "bbox": {
                      "height": 32,
                      "width": 86,
                      "x": 0,
                      "y": 46
                    },
                    "disabled": false,
                    "element_id": 0,
                    "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                    "index": 0,
                    "label": "跳至内容",
                    "name": "跳至内容",
                    "role": "button",
                    "selector": "[data-agent-idx=\"0\"]",
                    "tag": "a",
                    "text": "跳至内容",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 32,
                      "width": 112,
                      "x": 0,
                      "y": 46
                    },
                    "disabled": false,
                    "element_id": 1,
                    "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                    "index": 1,
                    "label": "辅助功能反馈",
                    "name": "辅助功能反馈",
                    "role": "button",
                    "selector": "[data-agent-idx=\"1\"]",
                    "tag": "a",
                    "text": "辅助功能反馈",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 40,
                      "width": 154,
                      "x": 0,
                      "y": 48
                    },
                    "disabled": false,
                    "element_id": 2,
                    "href": "https://cn.bing.com/?FORM=Z9FD1",
                    "index": 2,
                    "label": "",
                    "name": "",
                    "role": "link",
                    "selector": "[data-agent-idx=\"2\"]",
                    "tag": "a",
                    "text": "",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 40,
                      "width": 40,
                      "x": 164,
                      "y": 52
                    },
                    "disabled": false,
                    "element_id": 3,
                    "href": "",
                    "index": 3,
                    "label": "搜索",
                    "name": "搜索",
                    "role": "button",
                    "selector": "[data-agent-idx=\"3\"]",
                    "tag": "input",
                    "text": "搜索",
                    "type": "submit",
                    "value": "搜索"
                  },
                  {
                    "bbox": {
                      "height": 44,
                      "width": 571,
                      "x": 193,
                      "y": 50
                    },
                    "disabled": false,
                    "element_id": 4,
                    "href": "",
                    "index": 4,
                    "label": "在此处输入你的搜索 — 输入时会显示搜索建议",
                    "name": "在此处输入你的搜索 — 输入时会显示搜索建议",
                    "role": "searchbox",
                    "selector": "[data-agent-idx=\"4\"]",
                    "tag": "input",
                    "text": "在此处输入你的搜索 — 输入时会显示搜索建议",
                    "type": "search",
                    "value": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫"
                  },
                  {
                    "bbox": {
                      "height": 50,
                      "width": 50,
                      "x": 1198,
                      "y": 48
                    },
                    "disabled": false,
                    "element_id": 5,
                    "href": "javascript:void(0)",
                    "index": 5,
                    "label": "",
                    "name": "",
                    "role": "link",
                    "selector": "[data-agent-idx=\"5\"]",
                    "tag": "a",
                    "text": "",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 26,
                      "width": 59,
                      "x": 227,
                      "y": 18
                    },
                    "disabled": false,
                    "element_id": 6,
                    "href": "",
                    "index": 6,
                    "label": "国际版",
                    "name": "国际版",
                    "role": "div",
                    "selector": "[data-agent-idx=\"6\"]",
                    "tag": "div",
                    "text": "国际版",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 38,
                      "x": 160,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 7,
                    "href": "https://cn.bing.com/?scope=web&FORM=HDRSC1",
                    "index": 7,
                    "label": "网页",
                    "name": "网页",
                    "role": "link",
                    "selector": "[data-agent-idx=\"7\"]",
                    "tag": "a",
                    "text": "网页",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 38,
                      "x": 222,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 8,
                    "href": "https://cn.bing.com/images/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC2",
                    "index": 8,
                    "label": "图片",
                    "name": "图片",
                    "role": "link",
                    "selector": "[data-agent-idx=\"8\"]",
                    "tag": "a",
                    "text": "图片",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 38,
                      "x": 284,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 9,
                    "href": "https://cn.bing.com/videos/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC3",
                    "index": 9,
                    "label": "视频",
                    "name": "视频",
                    "role": "link",
                    "selector": "[data-agent-idx=\"9\"]",
                    "tag": "a",
                    "text": "视频",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 38,
                      "x": 346,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 10,
                    "href": "https://cn.bing.com/academic/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC4",
                    "index": 10,
                    "label": "学术",
                    "name": "学术",
                    "role": "link",
                    "selector": "[data-agent-idx=\"10\"]",
                    "tag": "a",
                    "text": "学术",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 38,
                      "x": 408,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 11,
                    "href": "https://cn.bing.com/dict/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC6",
                    "index": 11,
                    "label": "词典",
                    "name": "词典",
                    "role": "link",
                    "selector": "[data-agent-idx=\"11\"]",
                    "tag": "a",
                    "text": "词典",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 38,
                      "x": 470,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 12,
                    "href": "https://cn.bing.com/maps?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%e7%94%a8%e6%88%b7%e8%af%84%e4%bb%b7+%e5%b7%ae%e8%af%84+%e4%bd%a9%e6%88%b4+%e8%88%92%e9%80%82%e5%ba%a6+%e5%ba%95%e5%99%aa+%e5%a4%b9%e5%a4%b4+%e8%bf%9e%e6%8e%a5+%e6%95%85%e9%9a%9c+%e4%ba%ac%e4%b8%9c+%e5%a4%a9%e7%8c%ab&FORM=HDRSC7",
                    "index": 12,
                    "label": "地图",
                    "name": "地图",
                    "role": "link",
                    "selector": "[data-agent-idx=\"12\"]",
                    "tag": "a",
                    "text": "地图",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 54,
                      "x": 532,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 13,
                    "href": "javascript:void(0);",
                    "index": 13,
                    "label": "更多",
                    "name": "更多",
                    "role": "button",
                    "selector": "[data-agent-idx=\"13\"]",
                    "tag": "a",
                    "text": "更多",
                    "type": "",
                    "value": ""
                  }
                ],
                "screenshot_path": "runs/screenshots/d3-ec5539de.png",
                "source": "general",
                "status": 200,
                "visible_buttons": [
                  {
                    "bbox": {
                      "height": 32,
                      "width": 86,
                      "x": 0,
                      "y": 46
                    },
                    "disabled": false,
                    "element_id": 0,
                    "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                    "index": 0,
                    "label": "跳至内容",
                    "name": "跳至内容",
                    "role": "button",
                    "selector": "[data-agent-idx=\"0\"]",
                    "tag": "a",
                    "text": "跳至内容",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 32,
                      "width": 112,
                      "x": 0,
                      "y": 46
                    },
                    "disabled": false,
                    "element_id": 1,
                    "href": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB#",
                    "index": 1,
                    "label": "辅助功能反馈",
                    "name": "辅助功能反馈",
                    "role": "button",
                    "selector": "[data-agent-idx=\"1\"]",
                    "tag": "a",
                    "text": "辅助功能反馈",
                    "type": "",
                    "value": ""
                  },
                  {
                    "bbox": {
                      "height": 40,
                      "width": 40,
                      "x": 164,
                      "y": 52
                    },
                    "disabled": false,
                    "element_id": 3,
                    "href": "",
                    "index": 3,
                    "label": "搜索",
                    "name": "搜索",
                    "role": "button",
                    "selector": "[data-agent-idx=\"3\"]",
                    "tag": "input",
                    "text": "搜索",
                    "type": "submit",
                    "value": "搜索"
                  },
                  {
                    "bbox": {
                      "height": 30,
                      "width": 54,
                      "x": 532,
                      "y": 110
                    },
                    "disabled": false,
                    "element_id": 13,
                    "href": "javascript:void(0);",
                    "index": 13,
                    "label": "更多",
                    "name": "更多",
                    "role": "button",
                    "selector": "[data-agent-idx=\"13\"]",
                    "tag": "a",
                    "text": "更多",
                    "type": "",
                    "value": ""
                  }
                ],
                "visual_summary": "Screenshot captured for multimodal grounding; use provider analysis when configured."
              },
              "human_review_required": false,
              "ok": true,
              "text": "跳至内容 辅助功能反馈 国内版国际版 网页图片视频学术词典地图 更多",
              "title": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫 - 搜索",
              "url": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB"
            },
            "fallback_used": null,
            "node_id": "d3",
            "ok": true,
            "score": 1
          }
        ],
        "workflow": {
          "confidence": 0.68,
          "domain": "shopping",
          "goal": "推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论",
          "nodes": [
            {
              "action": "collect_links",
              "depends_on": [],
              "id": "d1",
              "inputs": {
                "checklist_status": [
                  {
                    "evidence": "尚未收集预算内主流型号和价格线索。",
                    "stage": "candidate_pool",
                    "status": "missing"
                  },
                  {
                    "evidence": "尚未核对商城商品页价格、参数和评价入口。",
                    "stage": "marketplace_pages",
                    "status": "missing"
                  },
                  {
                    "evidence": "尚未收集专业对比评测。",
                    "stage": "comparative_reviews",
                    "status": "missing"
                  },
                  {
                    "evidence": "尚未收集用户差评和佩戴/故障反馈。",
                    "stage": "user_comments",
                    "status": "missing"
                  },
                  {
                    "evidence": "尚未收集视频测评及评论区线索。",
                    "stage": "video_reviews",
                    "status": "missing"
                  }
                ],
                "dynamic": true,
                "evidence_stage": "candidate_pool",
                "multimodal_planning_used": false,
                "planner_suggested_action": "search_web",
                "planner_suggested_rationale": "当前搜索页没有可用结果摘要或可交互元素，需要先用更聚焦的购物/推荐查询建立候选型号池。",
                "query": "1000元以内 降噪耳机 推荐 通勤 办公 头戴式 入耳式 型号 价格",
                "rationale": "Progress guard: current page is already a results/search page, so collect visible candidates before issuing another search or wait.",
                "source": "shopping"
              },
              "instruction": "当前已经到达搜索/结果页，先抽取候选链接或启用垂直候选恢复。",
              "retry_policy": {
                "max_retries": 2
              },
              "success_criteria": [
                "action_ok",
                "evidence_or_fields"
              ],
              "type": "agent_dynamic_guarded"
            },
            {
              "action": "deep_read_candidates",
              "depends_on": [
                "d1"
              ],
              "id": "d2",
              "inputs": {
                "checklist_status": [
                  {
                    "evidence": "已有 Sony WH-CH720N、Soundcore Space Q45、Edifier W820NB Plus 等候选链接。",
                    "stage": "candidate_pool",
                    "status": "partial"
                  },
                  {
                    "evidence": "已有官方商品页线索，但还缺少商城价格、销量和用户评价入口。",
                    "stage": "marketplace_pages",
                    "status": "partial"
                  },
                  {
                    "evidence": "已有 RTINGS 对比和 What Hi-Fi 评测链接，尚需提取具体结论。",
                    "stage": "comparative_reviews",
                    "status": "partial"
                  },
                  {
                    "evidence": "尚未收集差评、佩戴疲劳、底噪、故障等用户反馈。",
                    "stage": "user_comments",
                    "status": "missing"
                  },
                  {
                    "evidence": "尚未收集视频测评和评论区线索。",
                    "stage": "video_reviews",
                    "status": "missing"
                  }
                ],
                "dynamic": true,
                "evidence_stage": "comparative_reviews",
                "limit": 3,
                "multimodal_planning_used": true,
                "rationale": "已有候选商品页和专业评测链接，下一步应先深入读取商品与测评证据，补齐价格参数和对比信息。",
                "source": "shopping"
              },
              "instruction": "深入读取当前候选链接中的商品页和专业评测，提取型号参数、价格定位、降噪/舒适度/办公通勤表现和主要短板。",
              "retry_policy": {
                "max_retries": 2
              },
              "success_criteria": [
                "action_ok",
                "evidence_or_fields"
              ],
              "type": "agent_dynamic"
            },
            {
              "action": "search_web",
              "depends_on": [
                "d2"
              ],
              "id": "d3",
              "inputs": {
                "checklist_status": [
                  {
                    "evidence": "已覆盖 Space Q45、WH-CH720N、W820NB Plus 等候选，但国内价格/渠道仍需核对。",
                    "stage": "candidate_pool",
                    "status": "partial"
                  },
                  {
                    "evidence": "已有官方商品页参数，缺少京东/天猫等商城价格、销量和评价入口证据。",
                    "stage": "marketplace_pages",
                    "status": "partial"
                  },
                  {
                    "evidence": "已有 RTINGS 对比和 What Hi-Fi 专业评测，支持降噪、音质、舒适度初判。",
                    "stage": "comparative_reviews",
                    "status": "partial"
                  },
                  {
                    "evidence": "尚未收集用户评论、差评、佩戴疲劳、底噪、夹头或故障反馈。",
                    "stage": "user_comments",
                    "status": "missing"
                  },
                  {
                    "evidence": "尚未收集视频测评及评论区线索。",
                    "stage": "video_reviews",
                    "status": "missing"
                  }
                ],
                "dynamic": true,
                "evidence_stage": "user_comments",
                "multimodal_planning_used": true,
                "query": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫",
                "rationale": "已有候选型号和部分专业/商品页证据，下一步需要补齐真实用户差评与佩戴/故障反馈。",
                "source": "general"
              },
              "instruction": "搜索具体候选型号的用户评价和差评，重点关注通勤办公场景下的佩戴舒适度、降噪、底噪、夹头、连接稳定性和常见故障。",
              "retry_policy": {
                "max_retries": 2
              },
              "success_criteria": [
                "action_ok",
                "evidence_or_fields"
              ],
              "type": "agent_dynamic"
            }
          ],
          "output_schema": {
            "candidates": "list",
            "comparison_matrix": "list",
            "decision_criteria": "list",
            "multimodal_notes": "list",
            "next_actions": "list",
            "recommendations": "list",
            "summary": "str",
            "uncertainties": "list",
            "video_digest": "dict"
          },
          "summary": "shopping workflow for: 推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论",
          "template": "shopping_workflow",
          "workflow_id": "0b519077-62a9-4c19-bfed-ff49a9e53fbd"
        }
      },
      "monitorMessage": "任务页面已满足要求",
      "monitorObservations": [
        {
          "pageAction": {
            "action": {
              "controlIndex": 5,
              "reason": "fill_visible_search_box",
              "type": "fill_and_submit",
              "value": "1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论"
            },
            "result": {
              "ok": true,
              "reason": "submitted_form"
            }
          },
          "step": 1,
          "title": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫 - 搜索",
          "url": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB&rdr=1&rdrig=749392FD78A94236BC144A23A9DFA12B",
          "verdict": {
            "domain": "shopping",
            "hasGithubRepoChrome": false,
            "hasSearchResultPage": true,
            "hasZeroResults": false,
            "hits": [],
            "isGithubRepoPage": false,
            "isVideoPage": false,
            "ok": false,
            "reason": "shopping_search_page_needs_product_or_review_page",
            "title": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫 - 搜索",
            "url": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB&rdr=1&rdrig=749392FD78A94236BC144A23A9DFA12B"
          }
        },
        {
          "step": 2,
          "title": "1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论 - 搜索",
          "url": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85%E9%80%82%E5%90%88%E9%80%9A%E5%8B%A4%E5%92%8C%E5%8A%9E%E5%85%AC%E7%9A%84%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA%EF%BC%8C%E9%9C%80%E8%A6%81%E6%AF%94%E8%BE%83%E5%95%86%E5%9F%8E%E5%95%86%E5%93%81%E9%A1%B5%E3%80%81%E4%B8%93%E4%B8%9A%E6%B5%8B%E8%AF%84%E3%80%81%E7%94%A8%E6%88%B7%E8%AF%84%E8%AE%BA%E5%B7%AE%E8%AF%84%E3%80%81%E8%A7%86%E9%A2%91%E6%B5%8B%E8%AF%84%E8%AF%84%E8%AE%BA%E5%90%8E%E7%BB%99%E5%87%BA%E7%BB%93%E8%AE%BA&qs=n&form=QBRE&sp=-1&lq=0&pq=&sc=0-0&sk=&cvid=15938C2D9D4644FAA4F8C9417A67FFCB",
          "verdict": {
            "domain": "shopping",
            "hasGithubRepoChrome": false,
            "hasSearchResultPage": true,
            "hasZeroResults": false,
            "hits": [
              "需要比较商城商品页",
              "专业测评",
              "用户评论差评",
              "视频测评评论后给出结论"
            ],
            "isGithubRepoPage": false,
            "isVideoPage": false,
            "ok": false,
            "reason": "shopping_search_page_needs_product_or_review_page",
            "title": "1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论 - 搜索",
            "url": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85%E9%80%82%E5%90%88%E9%80%9A%E5%8B%A4%E5%92%8C%E5%8A%9E%E5%85%AC%E7%9A%84%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA%EF%BC%8C%E9%9C%80%E8%A6%81%E6%AF%94%E8%BE%83%E5%95%86%E5%9F%8E%E5%95%86%E5%93%81%E9%A1%B5%E3%80%81%E4%B8%93%E4%B8%9A%E6%B5%8B%E8%AF%84%E3%80%81%E7%94%A8%E6%88%B7%E8%AF%84%E8%AE%BA%E5%B7%AE%E8%AF%84%E3%80%81%E8%A7%86%E9%A2%91%E6%B5%8B%E8%AF%84%E8%AF%84%E8%AE%BA%E5%90%8E%E7%BB%99%E5%87%BA%E7%BB%93%E8%AE%BA&qs=n&form=QBRE&sp=-1&lq=0&pq=&sc=0-0&sk=&cvid=15938C2D9D4644FAA4F8C9417A67FFCB"
          }
        },
        {
          "step": 3,
          "title": "1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论 - 搜索 视频",
          "url": "https://cn.bing.com/videos/search?q=1000%e5%85%83%e4%bb%a5%e5%86%85%e9%80%82%e5%90%88%e9%80%9a%e5%8b%a4%e5%92%8c%e5%8a%9e%e5%85%ac%e7%9a%84%e9%99%8d%e5%99%aa%e8%80%b3%e6%9c%ba%ef%bc%8c%e9%9c%80%e8%a6%81%e6%af%94%e8%be%83%e5%95%86%e5%9f%8e%e5%95%86%e5%93%81%e9%a1%b5%e3%80%81%e4%b8%93%e4%b8%9a%e6%b5%8b%e8%af%84%e3%80%81%e7%94%a8%e6%88%b7%e8%af%84%e8%ae%ba%e5%b7%ae%e8%af%84%e3%80%81%e8%a7%86%e9%a2%91%e6%b5%8b%e8%af%84%e8%af%84%e8%ae%ba%e5%90%8e%e7%bb%99%e5%87%ba%e7%bb%93%e8%ae%ba&FORM=HDRSC3",
          "verdict": {
            "domain": "shopping",
            "hasGithubRepoChrome": false,
            "hasSearchResultPage": false,
            "hasZeroResults": false,
            "hits": [
              "需要比较商城商品页",
              "专业测评",
              "用户评论差评",
              "视频测评评论后给出结论"
            ],
            "isGithubRepoPage": false,
            "isVideoPage": false,
            "ok": true,
            "reason": "page_matches_task",
            "title": "1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论 - 搜索 视频",
            "url": "https://cn.bing.com/videos/search?q=1000%e5%85%83%e4%bb%a5%e5%86%85%e9%80%82%e5%90%88%e9%80%9a%e5%8b%a4%e5%92%8c%e5%8a%9e%e5%85%ac%e7%9a%84%e9%99%8d%e5%99%aa%e8%80%b3%e6%9c%ba%ef%bc%8c%e9%9c%80%e8%a6%81%e6%af%94%e8%be%83%e5%95%86%e5%9f%8e%e5%95%86%e5%93%81%e9%a1%b5%e3%80%81%e4%b8%93%e4%b8%9a%e6%b5%8b%e8%af%84%e3%80%81%e7%94%a8%e6%88%b7%e8%af%84%e8%ae%ba%e5%b7%ae%e8%af%84%e3%80%81%e8%a7%86%e9%a2%91%e6%b5%8b%e8%af%84%e8%af%84%e8%ae%ba%e5%90%8e%e7%bb%99%e5%87%ba%e7%bb%93%e8%ae%ba&FORM=HDRSC3"
          }
        }
      ],
      "_history": [
        {
          "poll": 1,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=E69570FFC62B450684175A23CCC1D15A",
          "visibleTitle": "Loading https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC"
        },
        {
          "poll": 2,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 3,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 4,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 5,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 6,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 7,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 8,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 9,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 10,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 11,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 12,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 13,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 14,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 15,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 16,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 17,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 18,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 19,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 20,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 21,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 22,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 23,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 24,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 25,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 26,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 27,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 28,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 29,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 30,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 31,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 32,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 33,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 34,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 35,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 36,
          "status": "running",
          "monitorMessage": "",
          "finalUrl": "",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "1000元以内 降噪耳机 推荐 通勤 办公 - 搜索"
        },
        {
          "poll": 37,
          "status": "monitoring",
          "monitorMessage": "正在监视页面是否满足任务要求",
          "finalUrl": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC&rdr=1&rdrig=7F24CDEBB2D04A51B2CB848E6C3B83E5",
          "visibleTitle": "Loading https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB"
        },
        {
          "poll": 38,
          "status": "monitoring",
          "monitorMessage": "页面未满足任务，正在执行页面动作：fill_visible_search_box",
          "finalUrl": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB",
          "visibleUrl": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB&rdr=1&rdrig=749392FD78A94236BC144A23A9DFA12B",
          "visibleTitle": "Loading https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85%E9%80%82%E5%90%88%E9%80%9A%E5%8B%A4%E5%92%8C%E5%8A%9E%E5%85%AC%E7%9A%84%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA%EF%BC%8C%E9%9C%80%E8%A6%81%E6%AF%94%E8%BE%83%E5%95%86%E5%9F%8E%E5%95%86%E5%93%81%E9%A1%B5%E3%80%81%E4%B8%93%E4%B8%9A%E6%B5%8B%E8%AF%84%E3%80%81%E7%94%A8%E6%88%B7%E8%AF%84%E8%AE%BA%E5%B7%AE%E8%AF%84%E3%80%81%E8%A7%86%E9%A2%91%E6%B5%8B%E8%AF%84%E8%AF%84%E8%AE%BA%E5%90%8E%E7%BB%99%E5%87%BA%E7%BB%93%E8%AE%BA&qs=n&form=QBRE&sp=-1&lq=0&pq=&sc=0-0&sk=&cvid=15938C2D9D4644FAA4F8C9417A67FFCB"
        },
        {
          "poll": 39,
          "status": "monitoring",
          "monitorMessage": "页面未满足任务，继续打开：https://cn.bing.com/videos/search?q=1000%e5%85%83%e4%bb%a5%e5%86%85%e9%80%82%e5%90%88%e9%80%9a%e5%8b%a4%e5%92%8c%e5%8a%9e%e5%85%ac%e7%9a%84%e9%99%8d%e5%99%aa%e8%80%b3%e6%9c%ba%ef%bc%8c%e9%9c%80%e8%a6%81%e6%af%94%e8%be%83%e5%95%86%e5%9f%8e%e5%95%86%e5%93%81%e9%a1%b5%e3%80%81%e4%b8%93%e4%b8%9a%e6%b5%8b%e8%af%84%e3%80%81%e7%94%a8%e6%88%b7%e8%af%84%e8%ae%ba%e5%b7%ae%e8%af%84%e3%80%81%e8%a7%86%e9%a2%91%e6%b5%8b%e8%af%84%e8%af%84%e8%ae%ba%e5%90%8e%e7%bb%99%e5%87%ba%e7%bb%93%e8%ae%ba&FORM=HDRSC3",
          "finalUrl": "https://cn.bing.com/search?q=Soundcore+Space+Q45+Sony+WH-CH720N+Edifier+W820NB+Plus+%E7%94%A8%E6%88%B7%E8%AF%84%E4%BB%B7+%E5%B7%AE%E8%AF%84+%E4%BD%A9%E6%88%B4+%E8%88%92%E9%80%82%E5%BA%A6+%E5%BA%95%E5%99%AA+%E5%A4%B9%E5%A4%B4+%E8%BF%9E%E6%8E%A5+%E6%95%85%E9%9A%9C+%E4%BA%AC%E4%B8%9C+%E5%A4%A9%E7%8C%AB",
          "visibleUrl": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85%E9%80%82%E5%90%88%E9%80%9A%E5%8B%A4%E5%92%8C%E5%8A%9E%E5%85%AC%E7%9A%84%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA%EF%BC%8C%E9%9C%80%E8%A6%81%E6%AF%94%E8%BE%83%E5%95%86%E5%9F%8E%E5%95%86%E5%93%81%E9%A1%B5%E3%80%81%E4%B8%93%E4%B8%9A%E6%B5%8B%E8%AF%84%E3%80%81%E7%94%A8%E6%88%B7%E8%AF%84%E8%AE%BA%E5%B7%AE%E8%AF%84%E3%80%81%E8%A7%86%E9%A2%91%E6%B5%8B%E8%AF%84%E8%AF%84%E8%AE%BA%E5%90%8E%E7%BB%99%E5%87%BA%E7%BB%93%E8%AE%BA&qs=n&form=QBRE&sp=-1&lq=0&pq=&sc=0-0&sk=&cvid=15938C2D9D4644FAA4F8C9417A67FFCB",
          "visibleTitle": "1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论 - 搜索 视频"
        },
        {
          "poll": 40,
          "status": "done",
          "monitorMessage": "任务页面已满足要求",
          "finalUrl": "https://cn.bing.com/videos/search?q=1000%e5%85%83%e4%bb%a5%e5%86%85%e9%80%82%e5%90%88%e9%80%9a%e5%8b%a4%e5%92%8c%e5%8a%9e%e5%85%ac%e7%9a%84%e9%99%8d%e5%99%aa%e8%80%b3%e6%9c%ba%ef%bc%8c%e9%9c%80%e8%a6%81%e6%af%94%e8%be%83%e5%95%86%e5%9f%8e%e5%95%86%e5%93%81%e9%a1%b5%e3%80%81%e4%b8%93%e4%b8%9a%e6%b5%8b%e8%af%84%e3%80%81%e7%94%a8%e6%88%b7%e8%af%84%e8%ae%ba%e5%b7%ae%e8%af%84%e3%80%81%e8%a7%86%e9%a2%91%e6%b5%8b%e8%af%84%e8%af%84%e8%ae%ba%e5%90%8e%e7%bb%99%e5%87%ba%e7%bb%93%e8%ae%ba&FORM=HDRSC3",
          "visibleUrl": "https://cn.bing.com/videos/search?q=1000%e5%85%83%e4%bb%a5%e5%86%85%e9%80%82%e5%90%88%e9%80%9a%e5%8b%a4%e5%92%8c%e5%8a%9e%e5%85%ac%e7%9a%84%e9%99%8d%e5%99%aa%e8%80%b3%e6%9c%ba%ef%bc%8c%e9%9c%80%e8%a6%81%e6%af%94%e8%be%83%e5%95%86%e5%9f%8e%e5%95%86%e5%93%81%e9%a1%b5%e3%80%81%e4%b8%93%e4%b8%9a%e6%b5%8b%e8%af%84%e3%80%81%e7%94%a8%e6%88%b7%e8%af%84%e8%ae%ba%e5%b7%ae%e8%af%84%e3%80%81%e8%a7%86%e9%a2%91%e6%b5%8b%e8%af%84%e8%af%84%e8%ae%ba%e5%90%8e%e7%bb%99%e5%87%ba%e7%bb%93%e8%ae%ba&FORM=HDRSC3",
          "visibleTitle": "1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论 - 搜索 视频"
        }
      ]
    },
    "visible_url": "https://cn.bing.com/videos/search?q=1000%e5%85%83%e4%bb%a5%e5%86%85%e9%80%82%e5%90%88%e9%80%9a%e5%8b%a4%e5%92%8c%e5%8a%9e%e5%85%ac%e7%9a%84%e9%99%8d%e5%99%aa%e8%80%b3%e6%9c%ba%ef%bc%8c%e9%9c%80%e8%a6%81%e6%af%94%e8%be%83%e5%95%86%e5%9f%8e%e5%95%86%e5%93%81%e9%a1%b5%e3%80%81%e4%b8%93%e4%b8%9a%e6%b5%8b%e8%af%84%e3%80%81%e7%94%a8%e6%88%b7%e8%af%84%e8%ae%ba%e5%b7%ae%e8%af%84%e3%80%81%e8%a7%86%e9%a2%91%e6%b5%8b%e8%af%84%e8%af%84%e8%ae%ba%e5%90%8e%e7%bb%99%e5%87%ba%e7%bb%93%e8%ae%ba&FORM=HDRSC3",
    "visible_title": "1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论 - 搜索 视频",
    "screenshot": "/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/extension-flow-04-agent-final-state.png",
    "latest_run_goal": "推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论",
    "latest_run_ok": true,
    "latest_run_agent": {
      "agent_name": "browser-workflow-agent",
      "provider": "openai_compatible",
      "model": "gpt-5.5",
      "model_fallbacks": [
        "gpt-5.4",
        "gpt-5.4-mini"
      ],
      "api_base_url": "https://synai996.space/v1",
      "use_llm": true,
      "vision_provider": "openai_compatible",
      "vision_model": "gpt-5.5",
      "vision_model_fallbacks": [
        "gpt-5.4",
        "gpt-5.4-mini"
      ],
      "vision_api_base_url": "https://synai996.space/v1",
      "http_user_agent": "codex-browser-agent/1.0",
      "llm_timeout_sec": 30,
      "vision_timeout_sec": 30,
      "planner_max_tokens": 1000,
      "report_max_tokens": 1600,
      "report_retry_max_tokens": 900,
      "use_multimodal_planning": true,
      "use_visual_precheck": false,
      "api_key_configured": true,
      "vision_api_key_configured": true
    },
    "latest_run_workflow": {
      "workflow_id": "0b519077-62a9-4c19-bfed-ff49a9e53fbd",
      "template": "shopping_workflow",
      "goal": "推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论",
      "domain": "shopping",
      "summary": "shopping workflow for: 推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论",
      "nodes": [
        {
          "id": "d1",
          "type": "agent_dynamic_guarded",
          "instruction": "当前已经到达搜索/结果页，先抽取候选链接或启用垂直候选恢复。",
          "action": "collect_links",
          "inputs": {
            "source": "shopping",
            "dynamic": true,
            "query": "1000元以内 降噪耳机 推荐 通勤 办公 头戴式 入耳式 型号 价格",
            "evidence_stage": "candidate_pool",
            "rationale": "Progress guard: current page is already a results/search page, so collect visible candidates before issuing another search or wait.",
            "checklist_status": [
              {
                "stage": "candidate_pool",
                "status": "missing",
                "evidence": "尚未收集预算内主流型号和价格线索。"
              },
              {
                "stage": "marketplace_pages",
                "status": "missing",
                "evidence": "尚未核对商城商品页价格、参数和评价入口。"
              },
              {
                "stage": "comparative_reviews",
                "status": "missing",
                "evidence": "尚未收集专业对比评测。"
              },
              {
                "stage": "user_comments",
                "status": "missing",
                "evidence": "尚未收集用户差评和佩戴/故障反馈。"
              },
              {
                "stage": "video_reviews",
                "status": "missing",
                "evidence": "尚未收集视频测评及评论区线索。"
              }
            ],
            "planner_suggested_action": "search_web",
            "planner_suggested_rationale": "当前搜索页没有可用结果摘要或可交互元素，需要先用更聚焦的购物/推荐查询建立候选型号池。",
            "multimodal_planning_used": false
          },
          "depends_on": [],
          "success_criteria": [
            "action_ok",
            "evidence_or_fields"
          ],
          "retry_policy": {
            "max_retries": 2
          }
        },
        {
          "id": "d2",
          "type": "agent_dynamic",
          "instruction": "深入读取当前候选链接中的商品页和专业评测，提取型号参数、价格定位、降噪/舒适度/办公通勤表现和主要短板。",
          "action": "deep_read_candidates",
          "inputs": {
            "source": "shopping",
            "evidence_stage": "comparative_reviews",
            "limit": 3,
            "dynamic": true,
            "rationale": "已有候选商品页和专业评测链接，下一步应先深入读取商品与测评证据，补齐价格参数和对比信息。",
            "checklist_status": [
              {
                "stage": "candidate_pool",
                "status": "partial",
                "evidence": "已有 Sony WH-CH720N、Soundcore Space Q45、Edifier W820NB Plus 等候选链接。"
              },
              {
                "stage": "marketplace_pages",
                "status": "partial",
                "evidence": "已有官方商品页线索，但还缺少商城价格、销量和用户评价入口。"
              },
              {
                "stage": "comparative_reviews",
                "status": "partial",
                "evidence": "已有 RTINGS 对比和 What Hi-Fi 评测链接，尚需提取具体结论。"
              },
              {
                "stage": "user_comments",
                "status": "missing",
                "evidence": "尚未收集差评、佩戴疲劳、底噪、故障等用户反馈。"
              },
              {
                "stage": "video_reviews",
                "status": "missing",
                "evidence": "尚未收集视频测评和评论区线索。"
              }
            ],
            "multimodal_planning_used": true
          },
          "depends_on": [
            "d1"
          ],
          "success_criteria": [
            "action_ok",
            "evidence_or_fields"
          ],
          "retry_policy": {
            "max_retries": 2
          }
        },
        {
          "id": "d3",
          "type": "agent_dynamic",
          "instruction": "搜索具体候选型号的用户评价和差评，重点关注通勤办公场景下的佩戴舒适度、降噪、底噪、夹头、连接稳定性和常见故障。",
          "action": "search_web",
          "inputs": {
            "source": "general",
            "evidence_stage": "user_comments",
            "query": "Soundcore Space Q45 Sony WH-CH720N Edifier W820NB Plus 用户评价 差评 佩戴 舒适度 底噪 夹头 连接 故障 京东 天猫",
            "dynamic": true,
            "rationale": "已有候选型号和部分专业/商品页证据，下一步需要补齐真实用户差评与佩戴/故障反馈。",
            "checklist_status": [
              {
                "stage": "candidate_pool",
                "status": "partial",
                "evidence": "已覆盖 Space Q45、WH-CH720N、W820NB Plus 等候选，但国内价格/渠道仍需核对。"
              },
              {
                "stage": "marketplace_pages",
                "status": "partial",
                "evidence": "已有官方商品页参数，缺少京东/天猫等商城价格、销量和评价入口证据。"
              },
              {
                "stage": "comparative_reviews",
                "status": "partial",
                "evidence": "已有 RTINGS 对比和 What Hi-Fi 专业评测，支持降噪、音质、舒适度初判。"
              },
              {
                "stage": "user_comments",
                "status": "missing",
                "evidence": "尚未收集用户评论、差评、佩戴疲劳、底噪、夹头或故障反馈。"
              },
              {
                "stage": "video_reviews",
                "status": "missing",
                "evidence": "尚未收集视频测评及评论区线索。"
              }
            ],
            "multimodal_planning_used": true
          },
          "depends_on": [
            "d2"
          ],
          "success_criteria": [
            "action_ok",
            "evidence_or_fields"
          ],
          "retry_policy": {
            "max_retries": 2
          }
        }
      ],
      "confidence": 0.68,
      "output_schema": {
        "summary": "str",
        "candidates": "list",
        "recommendations": "list",
        "decision_criteria": "list",
        "comparison_matrix": "list",
        "video_digest": "dict",
        "multimodal_notes": "list",
        "uncertainties": "list",
        "next_actions": "list"
      }
    },
    "latest_run_summary": "Workflow 'shopping_workflow' completed for '推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论'. Collected 5 candidate links and 9 evidence items.",
    "events": 3,
    "steps": 3,
    "latest_run_evidence_items": 9,
    "latest_run_recommendations": 3
  },
  "market_comparison_rows": [
    {
      "product": "This project",
      "browser_control": "Visible Chrome for Testing with unpacked extension, direct tab update, monitor loop, DOM-aware follow-up actions.",
      "observation": "URL/title/text/links/controls plus screenshots and multimodal planning hooks.",
      "planning": "Observation-driven action loop with evidence checklist and safe action set.",
      "reporting": "Local latest-run JSON, markdown report, screenshots, traceable evidence.",
      "current_gap": "Still needs tighter live-run progress UX and more predictable long-task convergence."
    },
    {
      "product": "OpenAI Operator",
      "browser_control": "Cloud/hosted browser interaction with strong UI execution and consumer task polish.",
      "observation": "Rich multimodal observation with strong grounding.",
      "planning": "Closed product loop with strong task completion heuristics.",
      "reporting": "Good user-facing outcome quality but less local inspectability.",
      "current_gap": "Harder to self-host or inspect internal traces compared with this repo."
    },
    {
      "product": "Anthropic Computer Use",
      "browser_control": "Desktop-style computer control across apps, not only browser tabs.",
      "observation": "Screenshot-centric perception with iterative action loop.",
      "planning": "General-purpose step-by-step interaction.",
      "reporting": "Strong demo value, but app-specific audit artifacts depend on host integration.",
      "current_gap": "This repo is narrower in control scope but stronger on local browser-specific artifacts."
    },
    {
      "product": "Browser Use",
      "browser_control": "Playwright/browser automation focused, developer-friendly and scriptable.",
      "observation": "DOM-first with browser automation affordances.",
      "planning": "Agent planning around browser tasks, usually developer oriented.",
      "reporting": "Good engineering ergonomics, lighter end-user certification packaging.",
      "current_gap": "This repo now approaches similar explainability, but still needs broader site reliability."
    },
    {
      "product": "Google Project Mariner",
      "browser_control": "Consumer-facing multi-step browser assistance direction.",
      "observation": "Strong product-layer UX and task continuity emphasis.",
      "planning": "Task-level planning with product polish.",
      "reporting": "Less open implementation detail for local benchmarking.",
      "current_gap": "This repo remains more inspectable, but less polished in user-facing continuity."
    }
  ]
}
```