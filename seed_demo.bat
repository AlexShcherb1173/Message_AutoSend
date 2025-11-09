@echo off
REM ================================================================
REM  seed_demo.bat — запуск команды Django "seed_demo" под Windows
REM ---------------------------------------------------------------
REM  Назначение:
REM      Удобный способ наполнить базу демонстрационными данными
REM      (получатели, сообщения, рассылки) через:
REM          python manage.py seed_demo
REM      или, если используется Poetry:
REM          poetry run python manage.py seed_demo
REM
REM  Использование:
REM      seed_demo                 — просто загрузить фикстуры
REM      seed_demo --flush         — очистить таблицы перед загрузкой
REM      seed_demo --verbosity 2   — показать более подробный вывод
REM
REM  Скрипт:
REM      • автоматически выбирает между python и poetry run python
REM      • всегда работает из корня проекта (где manage.py)
REM      • использует кодировку UTF-8 для корректного вывода
REM ================================================================

chcp 65001 >nul
setlocal ENABLEDELAYEDEXPANSION

REM Определяем базовую команду Python
set "PY=python"

REM Проверяем наличие Poetry и pyproject.toml — если есть, используем Poetry
where poetry >nul 2>nul
if %ERRORLEVEL%==0 if exist "pyproject.toml" set "PY=poetry run python"

REM Переходим в директорию скрипта (корень проекта)
pushd "%~dp0"

REM Запускаем manage.py seed_demo с любыми переданными аргументами
%PY% manage.py seed_demo %*

REM Возвращаемся в исходную директорию
popd

REM Завершаем
endlocal