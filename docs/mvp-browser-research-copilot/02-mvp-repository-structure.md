# MVP 仓库结构

## 1. 推荐目录树

```text
browser-research-copilot/
  README.md
  pyproject.toml
  requirements.txt
  .env.example

  configs/
    app.yaml
    prompts/
      planner.md
      verifier.md
      summarizer.md

  src/
    app/
      main.py
      container.py

    contracts/
      request.py
      plan.py
      action.py
      observation.py
      evidence.py
      report.py
      events.py

    planner/
      planner.py
      step_templates.py

    harness/
      runtime.py
      state_machine.py
      retry_policy.py
      scheduler.py

    browser/
      playwright_client.py
      action_executor.py
      page_observer.py
      extractors/
        github_extractor.py
        paper_extractor.py

    understanding/
      dom_parser.py
      vision_grounding.py
      field_normalizer.py

    memory/
      session_store.py
      profile_store.py
      evidence_index.py

    verifier/
      verifier.py
      checks/
        schema_check.py
        evidence_check.py
        contradiction_check.py

    agents/
      github_agent.py
      paper_agent.py

    output/
      report_builder.py
      table_builder.py
      citation_formatter.py

    telemetry/
      logger.py
      trace.py
      metrics.py

  tests/
    unit/
    integration/
    e2e/
      test_github_flow.py
      test_paper_flow.py

  runs/
    .gitkeep

  docs/
    mvp-browser-research-copilot/
```

## 2. 模块依赖方向

```text
app/main
  -> planner
  -> harness
  -> agents
  -> output

harness
  -> browser
  -> verifier
  -> memory
  -> telemetry

agents
  -> harness (通过统一接口，不直接操作playwright)

output
  -> memory/evidence (只读)
```

规则：
- `agents/*` 不允许直接 import `playwright_client.py`
- `verifier/*` 不允许触发浏览器动作
- `contracts/*` 不依赖任何业务模块

## 3. MVP 里程碑对应代码范围

### M1（第1周）
- 完成 `contracts`、`planner`、`harness/runtime` 的最小闭环
- 打通 GitHub 单一来源抓取 + 总结

### M2（第2周）
- 加入 `paper_agent`（arXiv + Scholar）
- 增加 Verifier 和 retry policy

### M3（第3周）
- 增加 Memory 偏好注入
- 输出结构化对比报告（表格 + 引用）

## 4. 启动命令（建议）

```bash
python -m src.app.main --domain github --goal "找多模态OOD开源项目"
python -m src.app.main --domain paper --goal "找近两年Agent hallucination论文"
pytest tests/unit -q
pytest tests/e2e/test_github_flow.py -q
```
