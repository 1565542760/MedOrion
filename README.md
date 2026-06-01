# MedOrion Backend

Disease-extensible FastAPI backend foundation for MedOrion.

CAP/COP is the first demonstration task only; persistence and APIs are designed for multiple diseases, modalities, model versions, traceable LLM calls, doctor feedback, and dynamic reassessment.

## Server Commands

```bash
cd /home/sygxdg/MedOrion
python3 -m venv .venv
. .venv/bin/activate
python -m ensurepip --upgrade
python -m pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn medorion.main:app --host 0.0.0.0 --port 8000 --reload
```

Deployment installation and final online rollout are intentionally outside this backend/API thread.
