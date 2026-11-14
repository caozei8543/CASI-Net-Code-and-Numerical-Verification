.PHONY: setup test arithmetic integrity
setup:
	python -m pip install -e . pytest
test:
	python -m pytest -q
arithmetic:
	python scripts/check_reported_arithmetic.py
integrity:
	python scripts/verify_repository_checksums.py
