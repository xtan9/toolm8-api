.PHONY: lint format type-check test install dev clean

# Install dependencies
install:
	pip install -r requirements.txt

# Development setup
dev:
	pip install -r requirements.txt
	pip install -e .

# Format code
format:
	black app/
	isort app/

# Lint code
lint:
	flake8 app/
	pylint app/

# Type checking
type-check:
	mypy app/

# Run all quality checks
check: format lint type-check
	@echo "✅ All quality checks passed!"

# Clean cache and build files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .mypy_cache/ .pytest_cache/

# Run basic tests (core functionality + database refactor)
test:
	pytest tests/test_basic.py tests/test_models.py tests/test_database.py tests/test_seed.py tests/test_scraper_integration.py -v --disable-warnings

# Run all tests (some may fail due to mocking complexity)
test-all:
	pytest

# Run tests with coverage
test-cov:
	pytest tests/test_basic.py tests/test_models.py --cov=app --cov-report=html --cov-report=term-missing --disable-warnings

# Run specific test file
test-file:
	pytest $(FILE) -v

# Run the application
run:
	python app/main.py

# Run scraper setup
setup:
	python run.py