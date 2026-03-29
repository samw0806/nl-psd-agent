# NL-PSD Agent 完整测评规划

> **版本**: v6
> **更新日期**: 2026-03-29
> **状态**: 已落地首版框架
> **目标**: 建立脚本层自动化评测基线，并为自然语言 Agent 层提供结构化测评数据与人工复核清单。

---

## 一、测评目标

- 先验证 `scripts/` 的确定性能力，再评估自然语言编排能力。
- 将 `examples/` 中的真实 PSB 作为本地 smoke/regression 夹具。
- 将 `eval/fixtures/` 中的合成 PSD 作为自动判分主夹具。
- 将正式测评前的阻断问题单列为基线缺陷。

## 二、被测对象分层

### 2.1 脚本层

覆盖以下方面：

- CLI 合同性：`--help`、错误码、错误文案
- 只读能力：`info.py`、`preview.py`、`read_text.py`、`extract_smart_object.py`
- 修改能力：`visibility.py`、`add_layer.py`、`resample_layer.py`
- 文件输出：预览图、导出文件、另存文件

### 2.2 Agent 层

覆盖以下方面：

- 意图理解是否正确
- 是否遵守 `info.py + preview.py` 先行工作流
- 是否正确拒答底层不支持的操作
- 是否在修改后重新预览并确认结果

## 三、数据集设计

### 3.1 真实样例夹具

本地已有：

- `examples/100009151672.psb`
- `examples/100070345702.psb`

用途：

- smoke test
- regression test
- Agent 真实任务人工复核

注意：

- 这两个文件当前被 `.gitignore` 排除，不作为仓库内可复现主夹具。
- 对它们的 case 必须允许“本地有则运行，本地无则跳过”。

### 3.2 合成夹具

由 `eval/generate_fixtures.py` 生成：

- `simple_banner.psd`
- `nested_groups.psd`
- `duplicate_names.psd`
- `pixel_resample_only.psd`
- `mutation_sandbox.psd`

用途：

- 自动化精确断言
- 回归稳定
- CI 友好

## 四、Case 结构

所有 case 文件放在 `eval/cases/`，扩展名统一为 `.yaml`。

首版字段：

- `id`
- `layer`
- `fixture`
- `paths`
- `setup`
- `input`
- `expected_behavior`
- `assertions`
- `tags`

首版实现使用 JSON-compatible YAML 子集，避免额外依赖。

## 五、评测执行

### 5.1 脚本层

- 默认通过 `eval/runner.py --layer script` 执行。
- 修改类用例先复制夹具到临时目录。
- 主断言包含：
  - 退出码
  - `stdout/stderr`
  - 输出文件存在与大小
  - 跟进命令二次验证

### 5.2 Agent 层

- 当前首版输出人工测评 checklist。
- 每个 case 记录 prompt 与人工检查项。
- 后续再接入真实对话 transcript 自动归档。

## 六、指标与门槛

首版目标：

- 只读脚本成功率 100%
- CLI 合同性 100%
- 修改类脚本成功率 >= 95%
- 不支持操作拒答准确率 100%
- Agent 工作流遵循率 >= 95%

## 七、当前首版落地内容

已落地：

- `eval/runner.py`
- `eval/generate_fixtures.py`
- 脚本层 synthetic cases
- 真实样例 local-only cases
- Agent 层人工复核 case pack
- `tests/` 中的回归测试

当前已知基线缺陷：

- Python 3.12 下 `%` 帮助文案导致 `opacity.py`、`add_layer.py`、`resample_layer.py` 的 `--help` 崩溃

该问题已纳入首版自动化测试，修复后才能作为正式 benchmark 基线。
