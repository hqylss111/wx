$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& ./.venv/Scripts/python.exe -m PyInstaller --noconfirm --clean --windowed --name WeChatFriendAssistant --add-data 'selectors.json;.' --hidden-import export_controls --hidden-import pywinauto --hidden-import pythoncom --collect-submodules comtypes app.py
if ($LASTEXITCODE -ne 0) { throw '程序打包失败' }
& ./.build-tools/InnoSetup/tools/ISCC.exe installer.iss
if ($LASTEXITCODE -ne 0) { throw '安装包编译失败' }
