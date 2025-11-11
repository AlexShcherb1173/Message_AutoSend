@echo off
setlocal
REM ==== Tick sender for Message_AutoSend ====
REM Скрипт запускается из папки, где он лежит
cd /d "%~dp0"

REM 1) Попробуем Poetry (если проект под poetry)
where poetry >nul 2>nul
if %errorlevel%==0 (
  echo [tick] Using Poetry env...
  poetry run python manage.py send_due_mailings
  goto :eof
)

REM 2) Иначе активируем локальный .venv проекта
if exist ".venv\Scripts\activate.bat" (
  echo [tick] Activating local .venv...
  call ".venv\Scripts\activate.bat"
  python --version
  where python
  echo [tick] Running manage.py...
  python manage.py send_due_mailings
  goto :eof
)

REM 3) Фоллбек: системный python (только если пакеты стоят глобально!)
echo [tick] WARNING: no Poetry and no .venv found. Using system Python.
python manage.py send_due_mailings