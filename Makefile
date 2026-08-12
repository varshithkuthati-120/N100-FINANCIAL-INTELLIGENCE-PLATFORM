.PHONY: load ratios test report dashboard api clean

load:
	python src/etl/loader.py

ratios:
	python src/etl/ratios_calculator.py

test:
	python -m pytest tests/etl/ tests/kpi/ tests/dq/ tests/api/ --html=reports/pytest_report.html -v

report:
	python src/analytics/tearsheets.py
	python src/analytics/sector_reports.py
	python src/analytics/portfolio_report.py

dashboard:
	streamlit run dashboard.py

api:
	python -m uvicorn src.api.main:app --port 8000

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -f reports/pytest_report.html