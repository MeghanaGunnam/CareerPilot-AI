from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.auth.router import router as auth_router
from backend.app.core.config import settings
from backend.app.students.router import router as students_router


app = FastAPI(
    title="CareerPilot AI API",
    description=(
        "Backend API for the CareerPilot AI "
        "career intelligence platform."
    ),
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(students_router)


@app.get(
    "/api/v1/health",
    tags=["System"],
)
async def health_check():
    return {
        "status": "healthy",
        "service": "careerpilot-api",
        "version": "0.1.0",
    }