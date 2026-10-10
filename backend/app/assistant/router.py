from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.assistant.provider import get_assistant_provider
from backend.app.assistant.schemas import AssistantRequest, AssistantResponse, AssistantStatus
from backend.app.assistant.service import chat, provider_status

router = APIRouter(prefix="/api/v1/assistant", tags=["CareerPilot AI Assistant"])


@router.get("/status", response_model=AssistantStatus)
def status(user: User = Depends(get_current_user), provider=Depends(get_assistant_provider)):
    return provider_status(provider)


@router.post("/chat", response_model=AssistantResponse)
def answer(payload: AssistantRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user), provider=Depends(get_assistant_provider)):
    return chat(db, user.id, payload, provider)
