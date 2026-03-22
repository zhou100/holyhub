.PHONY: dev-backend dev-frontend seed test install

dev-backend:
	venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

seed:
	venv/bin/python -m backend.seed

test:
	venv/bin/python -m pytest tests/ -v

install:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt
	cd frontend && npm install
