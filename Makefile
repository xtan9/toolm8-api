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

# Run the application
run:
	python app/main.py

# Run scraper setup
setup:
	python run.py