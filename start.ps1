$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$runtime = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    if (Test-Path $runtime) { & $runtime -m venv .venv } else { py -m venv .venv }
    if ($LASTEXITCODE -ne 0) { throw '创建 Python 环境失败' }
}
& ./.venv/Scripts/python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw '安装依赖失败' }
& ./.venv/Scripts/python.exe app.py
