# CareerPilot AI

CareerPilot AI is a production-oriented student career-intelligence platform powered by
the Adaptive Career Intelligence Framework (ACIF).

## Planned stack
- Frontend: Next.js + TypeScript + Tailwind CSS
- Backend: FastAPI + Python + SQLAlchemy + Alembic
- Database: PostgreSQL + pgvector
- Background processing: Redis + worker queue
- AI/ML: scikit-learn, XGBoost, Sentence Transformers, SHAP
- Deployment: Docker + CI/CD

## Repository areas
- `frontend/` — web application (Next.js will be initialized here)
- `backend/` — FastAPI modular monolith
- `ml/` — production ML components
- `data/` — dataset import/processing scripts and local data placeholders
- `research/` — ACIF baselines, ablations, evaluation and notebooks
- `docs/` — architecture and technical documentation
- `docker/` — container-related configuration

This ZIP is the project scaffold. We will initialize the actual frontend/backend
dependencies and production code step-by-step so versions remain controlled and reproducible.
