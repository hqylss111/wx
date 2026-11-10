# 微信好友助手

## 安装版

双击 `installer-output/WeChatFriendAssistant-Setup-1.0.0.exe` 安装，支持 Windows 10/11 64 位，已包含 Python 和依赖。默认安装到当前用户的本地程序目录，可创建桌面快捷方式。安装包不包含联系人表格或开发日志。运行时仍需打开并登录电脑版微信。

通过 Windows“应用和功能”卸载。微信 UI 适配针对本机测试版本，微信升级或其他版本可能需要重新校准。当前程序未做代码签名。

复现构建：安装 requirements.txt 和 PyInstaller，准备 Inno Setup 编译工具到 `.build-tools/InnoSetup/tools/`，然后运行 `build.ps1`。

使用 Python、pywinauto 和 openpyxl 的 Windows 本地项目。

## 开发状态

已实现 Excel 导入与预览、联系人去重、断点恢复、微信窗口搜索与好友申请、逐条结果保存、自动备份、暂停/继续、等待倒计时，以及后台导出微信控件和实时日志。已在开发电脑上完成实机流程验证，其他电脑或微信版本需要重新确认控件适配。

## 使用

安装 Python 3.11 或更新版本后，在本目录运行：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py template data/contacts.xlsx
.\.venv\Scripts\python.exe main.py preview data/contacts.xlsx
.\.venv\Scripts\python.exe main.py inspect
```

Excel 第一行表头：联系人、验证消息、状态、处理时间、备注。联系人列使用文本格式，填写微信号或手机号。操作前关闭 Excel 中打开的工作簿，以便保存。

状态区分“已发送申请”和“已通过”；只有界面确认相应结果后才能记录。支持逐个搜索、验证消息、结果识别、暂停停止及异常后恢复；遇到验证码或账号限制时停止并交由人工处理。验证消息留空时保留微信默认内容。

## 本地数据

联系人 Excel、日志、截图、运行环境和安装产物均不提交到源码仓库。请在本机通过“生成模板”创建表格，再填写联系人信息。

## 桌面界面

运行 `powershell -ExecutionPolicy Bypass -File .\start.ps1`，或使用已有环境运行 `.\.venv\Scripts\python.exe app.py`。

支持选择工作簿、预览、默认验证消息、间隔、暂停和停止。每条操作前记录“处理中”，发送结果明确后再更新状态；意外中断的“处理中”和“待人工确认”不会自动重试。人工核对后清空状态才能重试。每次任务自动备份原表，检测到外部修改或保存失败立即停止。

`selectors.json` 包含开发电脑上已验证的控件配置，`calibrated` 为 `true`。更换微信版本或电脑后，请先用“导出微信控件”生成 `logs/wechat-controls.txt`，核对窗口、输入框和提交按钮是否唯一匹配。尚未确认适配时将 `calibrated` 设为 `false`，程序会拒绝发送。配置格式为 `{"window": {"title": "实际窗口标题"}, "child": {"title": "实际控件标题", "control_type": "Button"}}`。控件导出有后台进度、日志和 30 秒超时保护。

暂停在联系人之间生效；停止会中断界面等待，已发出申请需人工核对。运行过程中请保持微信窗口可交互，并关闭 Excel 中的源文件。

运行验证：`.\.venv\Scripts\python.exe -m unittest -v`。
