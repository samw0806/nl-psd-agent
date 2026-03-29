# 01 - PSD/PSB 引擎选型调研

> **更新日期**: 2026-03-26
> **调研目的**: 评估可用于编程操作 PSD/PSB 文件的库和工具

---

## 一、JavaScript 库

### ag-psd

- **GitHub**: https://github.com/Agamnentzar/ag-psd
- **NPM**: https://www.npmjs.com/package/ag-psd
- **Stars**: 639 | **License**: MIT | **最近更新**: 2026-01-28 (v30.1.0)
- **周下载量**: 21.2K
- **能力**: 读写 PSD、图层操作、文字图层（部分）、混合模式、蒙版、效果
- **限制**:
  - **不支持 PSB (Large Document Format)**
  - 不支持 CMYK、16-bit
  - 不支持动画、图案
  - 文字图层不完整（竖排可能导致文件损坏）
  - 不自动重绘图层合成图像
  - 不自动重绘修改后的图层位图
- **使用方式**: `readPsd(buffer)` 返回 JS 对象，`writePsd(psd)` 输出 ArrayBuffer
- **浏览器支持**: 支持，可在 Web Worker 中运行
- **评价**: 最活跃的 JS PSD 库，适合不需要 PSB 的简单场景

### psd-vanilla-js

- **GitHub**: https://github.com/sellersmith/psd-vanilla-js
- **基于 psd.js，2024 年创建**
- **能力**: 浏览器和 Node.js 解析 PSD，提取图层结构、文字、字体、矢量蒙版
- **限制**: 轻量，功能有限

### PSDLIB.js

- **GitHub**: https://github.com/tillschander/PSDLIB.js
- **最后更新**: 2017
- **状态**: 不再维护

---

## 二、Python 库

### psd-tools

- **GitHub**: https://github.com/psd-tools/psd-tools
- **Stars**: 1,354 | **License**: MIT
- **能力**: 读取 PSD 文件，解析图层结构，提取图像数据
- **限制**: 写入能力有限，PSB 支持不明确
- **评价**: Python 生态中最流行的 PSD 读取库

### Aspose.PSD for Python via .NET

- **官网**: https://products.aspose.com/psd/python-net/
- **能力**: 完整支持 PSD、PSB、AI 文件的创建、读取、编辑、转换
- **特性**: 文字图层更新、智能对象、填充图层、形状图层、混合模式、图层效果、变形变换
- **导出**: PDF, JPEG, PNG, TIFF, BMP, GIF
- **跨平台**: Windows, Linux, macOS
- **商业许可**: $999+/年
- **评价**: 功能最完整，但有商业成本

---

## 三、嵌入式方案

### Photopea

- **官网**: https://www.photopea.com
- **API 文档**: https://www.photopea.com/api/
- **性质**: 基于浏览器的完整 PSD/PSB 编辑器
- **嵌入方式**: iframe + URL hash 配置
- **通信方式**: `postMessage` 双向通信（发送脚本 / 接收数据）
- **脚本 API**: 兼容 Adobe Photoshop JavaScript Scripting Reference
- **功能**:
  - 完整 PSD/PSB 支持
  - 所有图层类型操作
  - 实时渲染
  - 原生拖拉拽编辑
  - 文件导入导出
- **价格**:
  - 免费嵌入（带广告）
  - Distributor 账号: 按月付费，隐藏广告和品牌
  - 自托管版本: $500-2000/月
- **Photopea 扩展 API**:
  - `app.echoToOE(string)` - 发送字符串到外部环境
  - `Document.saveToOE(format)` - 发送文件数据到外部环境
  - `App.open(url, as, asSmart)` - 从 URL 加载图片
- **Live Messaging**: 支持通过 postMessage 实时双向通信，可隐藏 UI 仅用作后台模块
- **评价**: 最完整的浏览器端 PSD 解决方案，API 成熟，适合快速集成

---

## 四、Adobe 官方方案

### Photoshop UXP Scripting

- **文档**: https://developer.adobe.com/photoshop/uxp/2022/
- **语言**: 现代 JavaScript (ES6, V8 引擎)
- **特点**: 异步 API，需要 `executeAsModal` 避免 UI 阻塞
- **限制**: 需要 Photoshop 应用程序运行，不能独立使用
- **评价**: 适合 Photoshop 插件开发，不适合独立 Web 应用

### Photoshop API (Cloud)

- **文档**: https://developer.adobe.com/photoshop/api/
- **能力**: 背景移除、预设、自动调色、智能对象替换、文字图层、动作执行
- **性质**: 云端 API，按调用次数付费
- **评价**: 适合批量处理，不适合实时交互编辑

---

## 五、Adobe AI Assistant (竞品参考)

- **发布**: 2025-10 Adobe MAX 发布，2026-03 公测
- **能力**: 自然语言 + 语音驱动 Photoshop 编辑
- **技术**: 基于 Adobe Firefly 生成式 AI
- **功能**: 移除干扰物、换背景、调光线/颜色、AI Markup（画标记+文字提示控制编辑位置）
- **评价**: 直接竞品，验证了"自然语言 P 图"的产品方向可行

---

## 六、选型结论

| 方案 | PSD | PSB | 浏览器渲染 | 手动编辑 | 开发量 | 推荐度 |
|------|-----|-----|-----------|---------|--------|--------|
| Photopea | 完整 | 完整 | 内置 | 内置 | 小 | **首选 (MVP)** |
| ag-psd + Canvas | 部分 | 不支持 | 需自建 | 需自建 | 巨大 | 不推荐 |
| psd-tools (Python) | 读取好 | 有限 | 需自建 | 需自建 | 大 | 备选 |
| Aspose.PSD (Python) | 完整 | 完整 | 需自建 | 需自建 | 中 | 备选(需付费) |
| Adobe UXP | 完整 | 完整 | 不支持 | Photoshop | - | 不适用 |
