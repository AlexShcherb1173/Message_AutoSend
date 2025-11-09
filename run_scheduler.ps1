# run_scheduler.ps1
# Запускает django-apscheduler, пишет логи в .\logs\scheduler\run_YYYYMMDD.log.
# Умеет работать и через Poetry, и через локальный .venv, и через системный Python.
[CmdletBinding()]
param(
  [string]$ManageCmd = "runapscheduler",   # имя management-команды
  [int]$KeepDays = 14                      # сколько дней хранить логи
)

$ErrorActionPreference = "Stop"
$PSDefaultParameterValues["Out-File:Encoding"] = "utf8"

# --- Paths ---
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$LogDir  = Join-Path $ScriptDir "logs\scheduler"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("run_{0}.log" -f (Get-Date -Format "yyyyMMdd"))

# --- Single instance guard (global mutex) ---
$mutexName = "Global\MessageSend-RunScheduler-" + ([Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($ScriptDir)) -replace '[=/+]','_')
$mutex = New-Object System.Threading.Mutex($false, $mutexName)
$hasHandle = $false
try {
  $hasHandle = $mutex.WaitOne(0)
  if (-not $hasHandle) {
    Write-Host "[run_scheduler] Another instance is already running. Exit."
    exit 0
  }

  # --- Helpers ---
  function Write-Log([string]$msg) {
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "[{0}] {1}" -f $ts, $msg
    # один писатель — без Tee-Object
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
    Write-Host $line
  }

  function Rotate-Logs([string]$dir, [int]$keepDays) {
    Get-ChildItem $dir -File -ErrorAction SilentlyContinue |
      Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$keepDays) } |
      ForEach-Object {
        Write-Log "LOG ROTATE: remove $($_.FullName)"
        Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
      }
  }

  Write-Log "===== run_scheduler start ====="
  Rotate-Logs -dir $LogDir -keepDays $KeepDays

  # --- Pick Python runner (Poetry -> .venv -> system) ---
  $pythonCmd = $null
  if (Get-Command poetry -ErrorAction SilentlyContinue) {
    Write-Log "Using Poetry environment"
    $pythonCmd = { poetry run python }
  } elseif (Test-Path ".\.venv\Scripts\python.exe") {
    Write-Log "Using local .venv"
    $env:Path = (Join-Path $ScriptDir ".\.venv\Scripts") + ";" + $env:Path
    $pythonCmd = { python }
  } else {
    Write-Log "WARNING: fallback to system Python"
    $pythonCmd = { python }
  }

  # --- Show versions for debug ---
  $pyver = & $pythonCmd.Invoke() --version 2>&1
  Write-Log ("Python: " + $pyver)
  Write-Log "Command: manage.py $ManageCmd"

  # --- Run scheduler (blocking) ---
  try {
    & $pythonCmd.Invoke() manage.py $ManageCmd 2>&1 | ForEach-Object { Write-Log $_ }
    $exit = $LASTEXITCODE
    Write-Log "Scheduler exited with code $exit"
  } catch {
    Write-Log ("ERROR: " + $_.Exception.Message)
    Write-Log ("STACK: " + $_.ScriptStackTrace)
    exit 1
  } finally {
    Write-Log "===== run_scheduler end ====="
  }

} finally {
  if ($hasHandle) { $mutex.ReleaseMutex() | Out-Null }
  $mutex.Dispose()
}
