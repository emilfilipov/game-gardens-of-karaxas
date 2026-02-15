from fastapi import APIRouter

from app.api.routes import auth, characters, chat, health, lobby, ops

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(lobby.router)
api_router.include_router(characters.router)
api_router.include_router(chat.router)
api_router.include_router(ops.router)
