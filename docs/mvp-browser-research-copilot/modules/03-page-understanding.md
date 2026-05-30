# 模块文档：Page Understanding（DOM + 视觉）

## 职责
从页面中提取可验证字段，统一输出结构化 observation。

## 输入
- DOM Snapshot
- Screenshot（可选）
- Extract Spec（字段定义）

## 输出
- `Observation`
- `ExtractedFields`

## 关键接口
- `observe(page) -> Observation`
- `extract(observation, spec) -> dict`
- `locate(target_hint) -> Locator`

## 设计说明
- 先 DOM，后视觉：优先低成本解析；失败再走视觉定位/OCR。
- 字段归一化：star、日期、作者等格式统一。

## 测试要点
- 同一页面多次抽取结果一致
- 中英文页面字段映射一致
- 页面轻微改版后抽取仍可用
