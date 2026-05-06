.PHONY: run test db_create db_mock_data run_frontend swagger help

help:
	@echo "Available commands:"
	@echo "  make run            - Run the FastAPI application using uvicorn"
	@echo "  make run_frontend   - Run the frontend Vite dev server"
	@echo "  make test           - Run pytest (currently no tests)"
	@echo "  make db_create      - Initialize the database and create tables"
	@echo "  make db_mock_data   - Insert mock data into the database"
	@echo "  make swagger        - Generate latest swagger.json into docs/"

run:
	uvicorn main:app --reload

run_frontend:
	cd frontend && npm run dev

test:
	pytest

db_create:
	python3 scripts/init_db.py

db_mock_data:
	python3 scripts/load_mock_data.py

swagger:
	conda run -n work python3 -c "from main import app; import json; print(json.dumps(app.openapi(), ensure_ascii=False, indent=2))" > docs/swagger.json
	conda run -n work python3 -c "from main import app; import json; print(json.dumps(app.openapi(), ensure_ascii=False, indent=2))" > openapi.json
	@echo "Generated docs/swagger.json and openapi.json"
