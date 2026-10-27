# UK Wind Procurement Desk - Backend Service

FastAPI Python backend service delivering cutoff-selected wind forecasts, empirical accuracy evaluation, and quantile-based safety buffer sizing based on official Elexon BMRS streams.

## Quickstart
```bash
pip install -e ".[dev]"
pytest -v
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
