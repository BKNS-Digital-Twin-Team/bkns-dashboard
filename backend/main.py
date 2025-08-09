
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ИЗМЕНЕНИЕ: Убраны лишние импорты, которые больше не используются в этом файле
from state import (
    sessions, session_states, opc_adapters
)
from api.simulation import api_router as simulation_router
from opc_utils import update_opc_from_model_state

# 3 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ И ФОНОВЫЕ ЗАДАЧИ
async def update_loop(session_id):
    print(f">>> update_loop стартует для {session_id} <<<", flush=True)
    while session_id in sessions:
        if session_states.get(session_id, {}).get("running"):
            sessions[session_id].update_system()
            await update_opc_from_model_state(session_id, force_send_all=False)
        await asyncio.sleep(1)
    print(f">>> update_loop для сессии {session_id} завершен <<<")
    
# 4 ОПРЕДЕЛЕНИЕ API ЭНДПОИНТОВ

# 5 СБОРКА И ЗАПУСК ПРИЛОЖЕНИЯ FASTAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print("Завершение работы, остановка всех активных OPC адаптеров...")
    tasks = [adapter.disconnect() for adapter in opc_adapters.values()]
    await asyncio.gather(*tasks, return_exceptions=True)
    print("Все адаптеры остановлены.")

app = FastAPI(lifespan=lifespan)

# Разрешаем CORS в dev-режиме
if os.getenv("DEV_MODE") == "true":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Только в проде монтируем статику
    STATIC_FILES_DIR = os.getenv("STATIC_FILES_DIR")
    if STATIC_FILES_DIR is None:
        STATIC_FILES_DIR = "./backend/build/"
    app.mount("/", StaticFiles(directory=STATIC_FILES_DIR, html=True), name="static")

app.include_router(simulation_router)