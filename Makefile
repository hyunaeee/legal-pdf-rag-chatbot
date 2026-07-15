.PHONY: install install-ai run lint test evaluate verify

install:
	python -m pip install -e '.[dev]'

install-ai:
	python -m pip install -e '.[ai,observability,dev]'

run:
	uvicorn app.main:app --reload

lint:
	ruff check app agents mcp_server tests evaluation

test:
	pytest --cov=app --cov-report=term-missing

evaluate:
	python -m evaluation.run

verify: lint test evaluate
