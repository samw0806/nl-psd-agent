打开并分析 PSD/PSB 文件。

用法：/open $ARGUMENTS

执行以下步骤：
1. 运行 `python scripts/info.py $ARGUMENTS` 获取图层树
2. 运行 `python scripts/preview.py $ARGUMENTS` 生成预览图
3. 用 Read 工具读取 `.tmp/preview.png`
4. 用中文向用户描述文件内容（尺寸、图层结构、视觉内容）
