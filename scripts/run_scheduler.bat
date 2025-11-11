@echo off
setlocal
REM ==== Message_AutoSend: APScheduler runner (console) ====
REM Запускает django-apscheduler из корректного окружения проекта.

REM 0) Переходим в каталог скрипта (корень Django-проекта)
cd /d "%~dp0"

REM 1) Если есть Poetry — используем его окружение
where poetry >nul 2>nul
if %errorlevel%==0 (
  echo [scheduler] Using Poetry env...
  poetry run python manage.py runapscheduler
  goto :eof
)

REM 2) Иначе активируем локальное .venv
if exist ".venv\Scripts\activate.bat" (
  echo [scheduler] Activating local .venv...
  call ".venv\Scripts\activate.bat"
  python --version
  where python
  echo [scheduler] Running manage.py runapscheduler ...
  python manage.py runapscheduler
  goto :eof
)

REM 3) Фоллбек: системный Python (если пакеты стоят глобально)
echo [scheduler] WARNING: no Poetry and no .venv found. Using system Python.
python manage.py runapscheduler
Если у тебя свой management-командный хэндлер (например, runscheduler), просто замени runapscheduler на своё имя.