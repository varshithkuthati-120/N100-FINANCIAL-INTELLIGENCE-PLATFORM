.PHONY: help init load validate ratios test report dashboard api clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

init: ## Create virtual environment and install dependencies
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

load: ## Load all data into SQLite
	.venv/bin/python -m src.etl.loader

validate: ## Run all 16 DQ rules
	.venv/bin/python -m src.etl.validator

ratios: ## Compute financial ratios
	.venv/bin/python -m src.etl.ratios

test: ## Run 35+ unit tests
	.venv/bin/pytest tests/ -v --tb=short

report: ## Generate data quality report
	.venv/bin/python -m src.etl.report

dashboard: ## Launch dashboard (future)
	@echo "Dashboard not yet implemented"

api: ## Launch API server (future)
	@echo "API not yet implemented"

clean: ## Remove generated files
	rm -f nifty100.db
	rm -f output/*.csv
	rm -rf .venv __pycache__ src/__pycache__ src/etl/__pycache__ tests/__pycache__ tests/etl/__pycache__