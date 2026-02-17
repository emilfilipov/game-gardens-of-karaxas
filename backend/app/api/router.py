from fastapi import APIRouter

from app.api.routes import auth, characters, chat, content, health, levels, lobby, ops

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(lobby.router)
api_router.include_router(characters.router)
api_router.include_router(levels.router)
api_router.include_router(content.router)
api_router.include_router(chat.router)
api_router.include_router(ops.router)
