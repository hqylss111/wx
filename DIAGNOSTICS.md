# 实机检查记录

以下为开发过程的历史排查记录；当前功能与适配状态以 README.md 和 selectors.json 为准。

## 后续实测修复

直接使用 pywinauto 后，成功获取“快捷操作”按钮坐标。UIA Invoke 调用出现阻塞，因此默认恢复物理点击。win32 后端成功打开“添加朋友”窗口，并通过 Pillow 截图。新增 search_smoke.py 执行仅搜索测试，严格检查已校准的窗口尺寸。

10 个无效前缀号码 00000000000–00000000009 已逐个在真实微信窗口输入、点击搜索并截图。核对全部截图，均显示“无法找到该用户”。结果写入 review/search-test/results.xlsx。此项验证不覆盖真实好友申请提交，也不表示主 GUI 的完整适配已完成。坐标仅适用于本次窗口布局，不能作为通用版本适配。

2026-11-09：Windows 自动化工具找到微信主窗口，成功读取 UIA 控件树，包含“快捷操作”按钮和“搜索”编辑框。读取文字不需要截图，可正常返回。

截图捕获连续超时。尝试点击“快捷操作”时，工具先返回窗口边界变化，刷新后仍返回 `coordinate input geometry is unavailable`。没有确认打开添加朋友窗口，没有执行手机号搜索或发送申请。

代码调整：pywinauto 适配器优先使用 UIA InvokePattern；仅在控件不提供 InvokePattern 时使用物理点击。调用失败不会自动换方式重试，避免重复提交。

限制：此次 UI 操作使用 computer-use 工具，无法据此证明 pywinauto InvokePattern 在目标控件上已成功。selectors.json 仍未完成校准，保留禁止发送状态。
