$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

function Fail-And-Exit {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [int]$Code = 1
    )

    Write-Host "[ERROR] $Message" -ForegroundColor Red
    Read-Host "Press Enter to exit" | Out-Null
    exit $Code
}

Write-Host "[Highlight-to-AI] Starting in background..." -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Fail-And-Exit -Message "Python not found. Please install Python 3.11+ and add it to PATH."
}

if (-not (Test-Path "config.toml")) {
    if (Test-Path "config.example.toml") {
        Copy-Item "config.example.toml" "config.toml"
        Fail-And-Exit -Message "config.toml created. Please set api_key in config.toml, then run again."
    }
    else {
        Fail-And-Exit -Message "config.example.toml is missing, cannot create config.toml automatically."
    }
}

Write-Host "Installing/checking dependencies (first run may take a while)..." -ForegroundColor DarkCyan
python -m pip install -e . | Out-Host
if ($LASTEXITCODE -ne 0) {
    Fail-And-Exit -Message "pip install failed with exit code $LASTEXITCODE" -Code $LASTEXITCODE
}

# 按你给的格式：后台拉起 pythonw + 指定工作目录
# 等价于：Start-Process -FilePath pythonw -ArgumentList "-m highlight_to_ai" -WorkingDirectory "$scriptDir"
if (Get-Command pythonw -ErrorAction SilentlyContinue) {
    Start-Process -FilePath pythonw -ArgumentList "-m", "highlight_to_ai" -WorkingDirectory $scriptDir | Out-Null
}
else {
    # 某些环境没有 pythonw，回退到 python 后台启动
    Start-Process -FilePath python -ArgumentList "-m", "highlight_to_ai" -WorkingDirectory $scriptDir | Out-Null
}

Write-Host "Highlight-to-AI launched in background. Hotkey: F3" -ForegroundColor Green
Start-Sleep -Seconds 1
exit 0
