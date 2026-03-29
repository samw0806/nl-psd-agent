查看 PSD/PSB 文件的图层树结构。

用法：/layers $ARGUMENTS

执行：`python scripts/info.py $ARGUMENTS`

以清晰的格式向用户展示图层结构，重点标注：
- 图层类型（Pixel/Type/Group/Shape/Smart/Fill）
- 可见性状态
- 不透明度
- 图层路径（用于后续操作）
