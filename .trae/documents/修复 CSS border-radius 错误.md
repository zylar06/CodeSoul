# 修复 Textual CSS 错误

`Textual` 不支持 `border-radius` 属性。我们需要从 `src/codesoul/app.py` 的 CSS 定义中移除它。

## 修改内容

编辑 `src/codesoul/app.py`，定位到 `CodeSoulApp` 类的 `CSS` 属性：
1.  删除 `.user-message` 中的 `border-radius: 1;`。
2.  删除 `.ai-message` 中的 `border-radius: 1;`。
