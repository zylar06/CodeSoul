# 修复并简化 App (纯 TUI 模式)

1.  **修复 Imports**: 在 `textual.containers` 导入中添加 `Horizontal`。
2.  **简化 Entry Point**: 移除 `Typer` 的复杂命令结构 (`start`, `analyze`)。
3.  **直接启动**: 修改 `main` 函数，使其直接解析命令行参数（使用 `sys.argv` 或简单的 `Typer` 单命令）并启动 `CodeSoulApp`。

这样，运行 `uv run codesoul .` 将直接启动界面，减少出错环节。
