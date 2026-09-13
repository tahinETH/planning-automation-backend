from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..auth import CurrentUser, current_user
from ..config import settings
from . import knowledge
from .models import ChatRequest
from .service import chat, stream_chat

router = APIRouter(prefix="/api/ravi", tags=["Ravi"])


@router.get("/status")
def status(user: CurrentUser = Depends(current_user)):
    return {"configured": bool(settings.deepseek_api_key), "model": settings.deepseek_model,
            "knowledgeVersion": knowledge.version(), "navigation": knowledge.navigation_targets(user.is_admin)}


@router.post("/chat")
async def post_chat(payload: ChatRequest, user: CurrentUser = Depends(current_user)):
    return await chat(payload, user)


@router.post("/chat/stream")
async def post_chat_stream(payload: ChatRequest, user: CurrentUser = Depends(current_user)):
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=503, detail="Ravi henüz yapılandırılmamış. Yöneticiniz backend DeepSeek anahtarını eklemeli.")
    return StreamingResponse(stream_chat(payload, user), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"})
