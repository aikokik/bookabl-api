.PHONY: install run clean test lint all fix-all check-all fix-format check-format fix-lint check-lint check-types test-coverage test-system docker-build docker-shell

PYTHON := /opt/bb/bin/python3.12

all: fix-all check-all
fix-all: fix-format fix-lint
check-all: check-format check-lint check-types test
test: test-coverage 

# Install dependencies
install:
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-dev.txt

fix-format:
	ruff format .

check-format:
	ruff format --diff .

fix-lint:
	ruff check --fix .

check-lint:
	ruff check .

check-types:
	mypy

test-coverage:
	pytest \
		--cov=bookabl \
		--junit-xml=tests.xml \
		--cov-report=xml:coverage.xml \
		--cov-report=html \
		--cov-report=term-missing \
		tests/unit \
		tests/integration

# Run the server
run:
	uvicorn main:app --reload

# Clean up python cache files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete

activate:
	source .venv/bin/activate

