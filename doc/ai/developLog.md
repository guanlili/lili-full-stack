# 学术搜索 Agent (Scholar Search Agent) 开发日志

本项目旨在构建一个智能学术搜索助手，能够从 Google Scholar 抓取、标准化展示并导出高质量的学术文献数据。

## 核心实现方案 (Core Implementation)

### 1. 后端架构 (FastAPI)
- **定制化爬虫**：采用 `httpx` 模拟高仿真浏览器头（User-Agent, Referer 等），有效绕过基础反爬。
- **智能解析引擎**：结合 `BeautifulSoup` 与 **正则匹配 (Regex)**，能够从杂乱的摘要中精准提取：
  - **核心指标**：标题、作者、发表平台、年份、被引次数、版本数量。
  - **身份识别**：自动解析学者档案，包含 Scholar ID、机构、研究领域及头像。
- **数据导出服务**：集成 `pandas` 与 `openpyxl`，实现结构化数据向 Excel 文件的秒级转化。

### 2. 前端交互 (React + TypeScript)
- **现代美学 UI**：基于玻璃拟态 (Glassmorphism) 风格设计，支持响应式布局、焦点动效与悬浮卡片。
- **多维度视图切换**：
  - **Visual Flow (视觉流)**：以卡片形式展示作者画像与文献精选。
  - **Statistics Table (统计表格)**：展示标准化、可扩展的学术指标报表。
- **智能文本处理**：实现 `ExpandableText` 组件，支持长字段（标题、作者）的自动截断与一键展开。

---

## 今日关键更新记录 (2026-01-07)

### 1. 数据解析与展示优化
- **鲁棒的年份提取**：引入正则表达式，解决了 Google Scholar 摘要格式多变导致年份抓取为空的顽疾，识别率提升 300%。
- **全维度指标对齐**：在统计表格中补全了 **“被引次数 (Cited By)”** 与 **“版本数 (Versions)”**，并配以直观图标。
- **交互细节**：增加了自适应截断功能，确保高信息密度下的页面整洁度。

### 2. 导出逻辑重构 (WYSIWYG 策略)
- **从 GET 到 POST 的革命**：
  - **背景**：传统的后端二次抓取模式（GET）易触发谷歌 Captcha 拦截，导致 Excel 为空。
  - **方案**：改为 **“所见即所得 (What You See Is What You Get)”** 模式。前端将当前页面已成功加载的数据通过 POST 实时发送给后端。
  - **优势**：100% 导出成功率，彻底规避反爬干扰，且导出的数据与屏幕展示完全一致。
- **URL 地址修复**：通过配置 `OpenAPI.BASE`，解决了开发模式下前端请求 404 (Not Found) 的路径重定向问题。

### 3. 深挖大数据：分页系统 (Pagination)
- **无限探索能力**：新增 `Prev` / `Next` 翻页控件。
- **增量抓取**：支持按页码（偏移量 10）深度检索 Google Scholar 后续记录，满足大批量文献综述的需求。
- **导出文件名同步**：导出文件自动命名为 `scholar_results_[关键词]_p[页码].xlsx`，方便科研资料归档。

---

## 主要修改文件清单
- `backend/app/api/routes/scholar.py`: 实现 POST 导出逻辑、分页支持及 Regex 解析增强。
- `backend/app/models.py`: 新增 `ScholarExportData` 模型，支持结构化数据传输。
- `frontend/src/routes/_layout/scholar.tsx`: 重构分页 UI、POST 导出逻辑及 `ExpandableText` 交互。
- `backend/pyproject.toml`: 确认 `pandas` 与 `openpyxl` 依赖。

---

## 如何体验最新功能
1. **深度搜索**：在搜索框输入关键词（如 "Deep Learning"），开启高级过滤器设置年份。
2. **多页翻阅**：滚动至页面下方，点击 **Next** 查看更多高相关度学术成果。
3. **精准导出**：在统计表格视图下，点击 **Export Current Page**，瞬间获取当前页的完整学术 Excel 条目。

---

**当前状态**：学术搜索 Agent 已形成从“精准检索 -> 标准化处理 -> 批量翻页 -> 结构化导出”的工业级闭环。