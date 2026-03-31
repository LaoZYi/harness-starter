PYTHON ?= python3
PACKAGE = src/ticket_router

.PHONY: test check ci run

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

check:
	$(PYTHON) scripts/check_repo.py
	$(PYTHON) -m py_compile $(PACKAGE)/*.py tests/*.py scripts/*.py

ci: check test

run:
	PYTHONPATH=src $(PYTHON) -m ticket_router.cli
