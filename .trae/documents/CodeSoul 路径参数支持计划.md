# 支持指定分析路径

我们将修改 `app.py`，允许用户通过命令行参数指定要分析的代码库路径。

## 修改内容

1.  **引入 CLI 参数处理**:
    *   修改 `src/codesoul/app.py`，使用 `Typer` 包装启动逻辑。
    *   添加一个 `path` 参数，默认为当前目录 `.`。

2.  **传递路径给 App**:
    *   更新 `CodeSoulApp` 类，使其 `__init__` 方法接收 `target_path` 参数。
    *   将该路径传递给 `CodeScanner` 和 `DirectoryTree` 控件，确保文件树和索引器都指向正确的位置。

3.  **UI 增强**:
    *   在 TUI 的标题栏 (`Header`) 或侧边栏显示当前正在分析的项目路径，明确“当前连接的灵魂”。

## 预期用法

修改后，你可以这样使用：

*   **分析当前目录**: `uv run src/codesoul/app.py`
*   **分析其他项目**: `uv run src/codesoul/app.py /path/to/your/awesome-project`
