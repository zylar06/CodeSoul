# CodeSoul 开发计划 (Hybrid RAG Architecture)

我们将构建一个混合架构的终端 RAG 应用。

## 阶段 1：项目初始化 (The Stack)

1.  **环境与依赖**:
    *   `uv init`
    *   **Core**: `fastembed` (轻量级本地向量化，无需 PyTorch), `chromadb` (向量数据库).
    *   **UI**: `textual` (TUI 框架).
    *   **AI**: `openai` (标准客户端适配 DeepSeek).
    *   **Utils**: `rich`, `python-dotenv`.

## 阶段 2：混合 RAG 引擎 (The Hybrid Engine)

1.  **代码摄取 (Ingestion)**:
    *   实现 `CodeScanner`：异步遍历文件，忽略非代码文件。
    *   **切片 (Chunking)**：实现简单的基于行号或缩进的代码分块策略。
2.  **向量化 (Embedding)**:
    *   集成 `fastembed`。
    *   **亮点**：实现一个带缓存的 Embedding 流程，如果文件没变，就不重新计算向量（展示工程优化能力）。
    *   存储入 `ChromaDB` (Persistent 模式，数据存本地)。
3.  **检索逻辑**:
    *   Query -> Local Embedding -> ChromaDB Search -> Top K Chunks -> DeepSeek Context。

## 阶段 3：人格与交互 (The Soul & UI)

1.  **人格生成**:
    *   "Cold Read"（冷读）：在索引结束后，统计代码特征（如：平均缩进深度、最长的函数行数），生成一份 JSON 侧写。
    *   注入 DeepSeek System Prompt。
2.  **Textual 界面**:
    *   **Split View**: 左侧文件树，右侧聊天流。
    *   **Thinking State**: 明确展示 "Embedding...", "Searching...", "DeepSeek Thinking..." 的不同状态。

## 阶段 4：交付

1.  完善的 `README`，解释混合架构的优势。
2.  代码主要注释清晰，方便面试官 Review。

## 确认配置
*   LLM: DeepSeek API (Base URL: `https://api.deepseek.com`)
*   Embedding: `fastembed` (本地运行，自动下载模型)

准备好开始写代码了吗？