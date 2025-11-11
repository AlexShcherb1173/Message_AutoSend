# tick_send_due_mailings.ps1
# Если используешь «минутный тикер» вместо постоянного демона. Вызывает вашу mgmt-команду (замени имя при необходимости), пишет логи отдельно.
[CmdletBinding()]
param(
  [string]$ManageCmd = "tick_send_due_mailings",  # ваша команда
  [int]$KeepDays = 7
)

$ErrorActionPreference = "Stop"
$PSDefaultParameterValues["Out-File:Encoding"] = "utf8"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$LogDir = Join-Path $ScriptDir "logs\ticker"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("tick_{0}.log" -f (Get-Date -Format "yyyyMMdd"))

function Write-Log($msg) {
  $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  "[{0}] {1}" -f $ts, $msg | Tee-Object -FilePath $LogFile -Append
}

function Rotate-Logs([string]$dir, [int]$keepDays) {
  Get-ChildItem $dir -File -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$keepDays) } |
    Remove-Item -Force -ErrorAction SilentlyContinue
}

Write-Log "=== tick start ==="
Rotate-Logs -dir $LogDir -keepDays $KeepDays

if (Get-Command poetry -ErrorAction SilentlyContinue) {
  Write-Log "Using Poetry"
  $cmd = "poetry run python manage.py $ManageCmd"
} elseif (Test-Path ".\.venv\Scripts\python.exe") {
  $env:Path = (Join-Path $ScriptDir ".\.venv\Scripts") + ";" + $env:Path
  Write-Log "Using .venv"
  $cmd = "python manage.py $ManageCmd"
} else {
  Write-Log "Using system Python"
  $cmd = "python manage.py $ManageCmd"
}

Write-Log "Run: $cmd"
$proc = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-Command",$cmd -Wait -PassThru -WindowStyle Hidden
Write-Log ("ExitCode: " + $proc.ExitCode)
Write-Log "=== tick end ==="