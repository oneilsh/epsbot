.PHONY: install demo

install:
	@echo "Installing dependencies..."
	poetry install --no-root

app:
	@echo "Running demo..."
	poetry run streamlit run main.py