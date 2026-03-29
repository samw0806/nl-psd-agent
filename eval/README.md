# Evaluation Framework

`eval/` 用于管理 NL-PSD Agent 的测评数据、夹具和 runner。

## 目录

- `cases/script/`：脚本层自动化 case
- `cases/agent/`：自然语言 Agent 层 case
- `assets/`：合成插图素材
- `fixtures/`：合成 PSD 夹具
- `results/`：评测输出目录

## 用法

先生成合成素材与夹具：

```bash
.venv/bin/python eval/generate_fixtures.py
```

运行脚本层评测：

```bash
.venv/bin/python eval/runner.py --layer script
```

运行单条脚本层 case：

```bash
.venv/bin/python eval/runner.py --layer script --case script_info_simple_banner --format json
```

输出 Agent 层人工测评清单：

```bash
.venv/bin/python eval/runner.py --layer agent --format json
```

## Case 格式

首版 case 文件扩展名使用 `.yaml`，内容采用 JSON-compatible YAML 子集，避免额外依赖。
