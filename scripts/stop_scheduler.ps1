# stop_scheduler.ps1
# Аккуратно завершает процесс, который крутит runapscheduler/вашу команду.
$ErrorActionPreference = "SilentlyContinue"

# Ищем процессы python, в командной строке которых есть runapscheduler (или своё имя)
$targets = Get-CimInstance Win32_Process |
  Where-Object { $_.Name -match 'python.exe' -and $_.CommandLine -match 'manage.py.*(runapscheduler|runscheduler)' }

if (-not $targets) {
  Write-Host "No scheduler process found."
  exit 0
}

foreach ($p in $targets) {
  Write-Host "Killing PID $($p.ProcessId): $($p.CommandLine)"
  Stop-Process -Id $p.ProcessId -Force
}