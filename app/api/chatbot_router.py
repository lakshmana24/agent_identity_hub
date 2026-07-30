from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_admin
from app.services.chatbot_service import ask_chatbot_service
from app.models.admin import Admin

router = APIRouter(prefix="/chatbot", tags=["AI Insights Chatbot"])

class ChatbotAskRequest(BaseModel):
    question: str

class ChatbotAskResponse(BaseModel):
    question: str
    answer: str

@router.post("/ask", response_model=ChatbotAskResponse)
def ask_chatbot(
    payload: ChatbotAskRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    if not payload.question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty.")

    answer = ask_chatbot_service(db, payload.question.strip())
    return ChatbotAskResponse(question=payload.question, answer=answer)
