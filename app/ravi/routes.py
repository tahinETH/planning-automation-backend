from fastapi import APIRouter, Depends

from ..auth import CurrentUser, current_user
from ..config import settings
from . import knowledge
from .models import ChatRequest
from .service import chat

router = APIRouter(prefix="/api/ravi", tags=["Ravi"])


@router.get("/status")
def status(user: CurrentUser = Depends(current_user)):
    return {"configured": bool(settings.deepseek_api_key), "model": settings.deepseek_model,
            "knowledgeVersion": knowledge.version(), "navigation": knowledge.navigation_targets(user.is_admin)}


@router.post("/chat")
async def post_chat(payload: ChatRequest, user: CurrentUser = Depends(current_user)):
    return await chat(payload, user)
