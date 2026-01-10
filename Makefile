# Makefile для Message_AutoSend

# Если используешь Poetry:
PYTHON = poetry run python

# Если хочешь использовать активированное venv — можно поменять на:
# PYTHON = python

.PHONY: migrate seed reset dev scheduler

migrate:
	$(PYTHON) manage.py migrate

seed:
	$(PYTHON) manage.py seed_demo
	$(PYTHON) manage.py seed_managers

reset:
	$(PYTHON) manage.py migrate
	$(PYTHON) manage.py flush --no-input
	$(MAKE) migrate
	$(MAKE) seed

dev:
	$(PYTHON) manage.py runserver

scheduler:
	$(PYTHON) manage.py run_scheduler --interval 60