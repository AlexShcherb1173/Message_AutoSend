@echo off
setlocal
REM Закрываем процесс python, который крутит runapscheduler в текущем каталоге
for /f "tokens=2 delims=," %%p in ('wmic process where "name='python.exe'" get ProcessId^,CommandLine /format:csv ^| findstr /i "manage.py runapscheduler"') do (
  echo Killing PID %%p
  taskkill /PID %%p /F >nul 2>nul
)
echo Done.