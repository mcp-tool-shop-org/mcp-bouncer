.PHONY: verify test lint typecheck

verify: lint typecheck test
	@echo "✓ All checks passed"

test:
	pytest --cov=mcp_bouncer --cov-report=term-missing

lint:
	ruff check .

typecheck:
	mypy src/ --ignore-missing-imports
