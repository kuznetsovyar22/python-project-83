dev:
	poetry run flask --app page_analyzer:app run
PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 127.0.0.1:$(PORT) page_analyzer:app
lint:
	poetry run flake8 page_analyzer
test:
	poetry run pytest tests/test.py

test-coverage:
	poetry run pytest --cov --cov-report lcov