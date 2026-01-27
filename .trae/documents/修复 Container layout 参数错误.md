# 修复 Textual 布局错误

将 `Container(..., layout="horizontal")` 替换为 `Horizontal(...)`，以修复 `TypeError`。

## 修改内容

编辑 `src/codesoul/app.py`：
1.  找到 `compose` 方法。
2.  将 `yield Container(..., layout="horizontal")` 改为 `yield Horizontal(...)`。
3.  移除不再需要的 `Container` 引用（如果不冲突）。
