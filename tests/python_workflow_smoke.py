import os
import tempfile
from pathlib import Path

from browser_agent.browser.action import _shopping_link_relevant, _video_link_relevant
from browser_agent.config import build_agent_config
from browser_agent.output.report_builder import _reading_to_matrix_row, _scored_comparison_matrix
from browser_agent.planner.tot import plan_goal
from browser_agent.types import Observation
from browser_agent.vision.keyframes import extract_video_keyframes, visual_inputs_from_video_digest
from browser_agent.vision.multimodal import GeminiVisionProvider, build_video_visual_prompt


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def assert_false(value, message):
    if value:
        raise AssertionError(message)


assert_true(
    _shopping_link_relevant(
        'Sony WH-CH720N 无线降噪耳机 评测 ANC headphones review',
        'https://www.whathifi.com/reviews/sony-wh-ch720n',
        'WH-CH720N W820NB Space Q45 降噪耳机 对比 评测 缺点',
    ),
    'headphone review links should be relevant',
)
assert_false(
    _shopping_link_relevant(
        '免费在线音频降噪工具 noise removal',
        'https://rtcd.io/zh-cn/audio-noise-reduction/',
        'WH-CH720N W820NB Space Q45 降噪耳机 对比 评测 缺点',
    ),
    'audio denoise utility pages should not be treated as headphone evidence',
)
assert_true(
    _video_link_relevant(
        'CLIP 多模态模型入门教程 bilibili',
        'https://www.bilibili.com/video/BV1XZR9ByEV2/',
        'CLIP 多模态 模型 入门 教程 视频 讲解',
    ),
    'CLIP tutorial video links should be relevant',
)
assert_false(
    _video_link_relevant(
        'Microsoft Outlook Sucks, Even In Space #funfact',
        'https://www.youtube.com/watch?v=Y-Kf5URgcBM',
        'CLIP 多模态 模型 入门 教程 视频 讲解',
    ),
    'unrelated video links should be filtered out',
)

github_workflow = plan_goal(
    '帮我找几个可以参考的浏览器自动化智能体 GitHub 开源项目',
    Observation(url='https://github.com', title='', text=''),
    domain='github',
)
github_queries = [node.inputs.get('query') for node in github_workflow.nodes if node.action == 'search_web']
assert_true(github_queries == ['browser automation agent LLM'], 'GitHub browser-agent goals should use an English search query')

with tempfile.TemporaryDirectory() as tmpdir:
    image_path = Path(tmpdir) / 'frame.png'
    image_path.write_bytes(b'not a real png but existence is enough before provider call')
    old_key = os.environ.pop('GEMINI_API_KEY', None)
    try:
        config = build_agent_config(vision_provider='gemini', vision_api_key_env='GEMINI_API_KEY')
        provider = GeminiVisionProvider(config)
        result = provider.analyze_image(str(image_path), build_video_visual_prompt('整理视频', '已知上下文'))
        assert_false(result.get('ok'), 'Gemini should be unavailable without API key')
        assert_true(result.get('reason') == 'gemini_api_key_missing_or_provider_disabled', 'missing key should be explicit')
    finally:
        if old_key is not None:
            os.environ['GEMINI_API_KEY'] = old_key

keyframe_result = extract_video_keyframes('', out_root='runs/test-keyframes')
assert_false(keyframe_result.get('ok'), 'missing URL should not extract keyframes')
assert_true(keyframe_result.get('reason') == 'missing_video_url', 'missing URL reason should be explicit')

keyframe_result = extract_video_keyframes('https://example.com/video', out_root='runs/test-keyframes')
assert_false(keyframe_result.get('ok'), 'missing local media tools should degrade safely in this environment')
assert_true(
    keyframe_result.get('reason') in {'yt-dlp_not_installed', 'ffmpeg_not_installed', 'yt-dlp_failed'},
    'keyframe extraction should report a structured unavailable/failed reason',
)

visual_inputs = visual_inputs_from_video_digest(
    {
        'screenshot_path': 'runs/screenshots/page.png',
        'keyframes': {'frames': ['runs/keyframes/f1.jpg', 'runs/keyframes/f2.jpg', 'runs/keyframes/f1.jpg']},
    }
)
assert_true(
    visual_inputs == ['runs/screenshots/page.png', 'runs/keyframes/f1.jpg', 'runs/keyframes/f2.jpg'],
    'visual inputs should combine screenshot and deduped keyframes',
)

github_row = _reading_to_matrix_row(
    {
        'ok': True,
        'name': 'browser-use/browser-use',
        'url': 'https://github.com/browser-use/browser-use',
        'title': 'browser-use/browser-use',
        'description': 'Make websites accessible for AI agents',
        'text': 'browser automation agent',
        'repo': {
            'stars': 123,
            'forks': 45,
            'language': 'Python',
            'license': 'MIT',
            'updated_at': '2026-05-28T00:00:00Z',
            'topics': ['browser', 'agent'],
            'readme_excerpt': 'Browser-use enables AI agents to control the browser.',
        },
    },
    'github',
)
assert_true(github_row['stars'] == 123, 'GitHub matrix should expose stars')
assert_true(github_row['language'] == 'Python', 'GitHub matrix should expose language')
assert_true(github_row['fit_notes'] == 'derived_from_github_api_and_readme', 'GitHub matrix should identify API-backed evidence')

github_fallback_row = _reading_to_matrix_row(
    {
        'ok': True,
        'name': 'nanobrowser/nanobrowser (13,050 stars) - browser automation',
        'url': 'https://github.com/nanobrowser/nanobrowser',
        'description': 'Open-source browser automation',
    },
    'github',
)
assert_true(github_fallback_row['stars'] == 13050, 'GitHub fallback rows should parse stars from search snippets')
assert_true(github_fallback_row['fit_notes'] == 'derived_from_github_page_or_search_snippet', 'GitHub fallback rows should not claim API-backed evidence')

scored = _scored_comparison_matrix(
    [
        {'name': 'low evidence repo', 'url': 'https://github.com/a/b', 'evidence_strength': 0.5, 'stars': 1},
        {'name': 'strong repo', 'url': 'https://github.com/c/d', 'evidence_strength': 0.8, 'stars': 5000, 'language': 'Python', 'license': 'MIT', 'topics': ['browser'], 'readme_signal': 'docs'},
    ],
    'github',
)
assert_true(scored[0]['name'] == 'strong repo', 'GitHub scorer should rank stronger repo first')
assert_true(scored[0]['score'] > scored[1]['score'], 'scores should explain recommendation ordering')
assert_true(scored[0]['score_reasons'], 'scored rows should include reasons')

print('python workflow smoke tests passed')

from browser_agent.output.markdown import render_markdown_report

markdown = render_markdown_report(
    {
        'run_id': 'test-run',
        'ok': True,
        'goal': '测试推荐报告',
        'workflow': {'domain': 'github'},
        'memory': {'evidence': []},
        'report': {
            'summary': '这是摘要',
            'reasoning_outline': ['先拆任务'],
            'search_plan': [{'purpose': '检索仓库', 'source': 'github', 'query': 'browser automation agent LLM'}],
            'recommendations': [{'name': 'browser-use/browser-use', 'url': 'https://github.com/browser-use/browser-use', 'score': 88, 'reason': 'README available'}],
            'comparison_matrix': [{'name': 'browser-use/browser-use', 'url': 'https://github.com/browser-use/browser-use', 'score': 88, 'score_reasons': ['README available'], 'stars': 1000, 'language': 'Python', 'license': 'MIT'}],
            'multimodal_notes': [{'provider': 'gemini', 'status': 'planned', 'purpose': '视觉识别'}],
        },
    }
)
assert_true('# 测试推荐报告' in markdown, 'Markdown report should include title')
assert_true('## Recommendations' in markdown, 'Markdown report should include recommendations')
assert_true('browser-use/browser-use' in markdown, 'Markdown report should include recommendation names')
assert_true('## Comparison Matrix' in markdown, 'Markdown report should include comparison matrix')
