.PHONY: all install test backend frontend run smoke clean

all: install test

install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

test:
	cd backend && pytest -q
	cd frontend && npm test

backend:
	cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

frontend:
	cd frontend && npm run dev

smoke:
	python scripts/smoke.py http://127.0.0.1:8000
