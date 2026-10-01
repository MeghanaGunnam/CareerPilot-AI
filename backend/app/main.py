from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.auth.router import router as auth_router
from backend.app.core.config import settings
from backend.app.students.router import router as students_router
from backend.app.careers.router import router as careers_router
from backend.app.psychometrics.router import router as psychometrics_router
from backend.app.resumes.router import router as resumes_router
from backend.app.skills.router import router as skills_router
from backend.app.assessments.router import router as assessments_router
from backend.app.career_twin.router import router as career_twin_router
from backend.app.acif.router import router as acif_router

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
app.include_router(careers_router)
app.include_router(psychometrics_router)
app.include_router(resumes_router)
app.include_router(skills_router)
app.include_router(assessments_router)
app.include_router(career_twin_router)
app.include_router(acif_router)


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