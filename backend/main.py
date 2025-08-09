# =============================================================================
# 1. ИМПОРТЫ И КОНФИГУРАЦИЯ
# =============================================================================
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from fastapi.middleware.cors import CORSMiddleware
import uuid
import importlib.util
import time


# Импортируем роутер из другого файла
from state import (
    sessions, session_states, previous_states, session_last_full_sync,
    opc_adapters, SERVER_URL, FULL_SYNC_INTERVAL
)
from logic import ControlLogic # Импортируем готовый объект, а не класс
from opc_adapter import OPCAdapter
from api.simulation import api_router as simulation_router
from opc_utils import update_opc_from_model_state
from Math.BKNS import BKNS


# =============================================================================
# 3. ИНИЦИАЛИЗАЦИЯ ГЛОБАЛЬНЫХ ОБЪЕКТОВ
# =============================================================================
control_logic = ControlLogic()
opc_adapter = OPCAdapter(SERVER_URL, control_logic, sessions, update_opc_from_model_state)


# =============================================================================
# 4. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ И ФОНОВЫЕ ЗАДАЧИ
# =============================================================================
async def update_loop(session_id):
    print(f">>> update_loop стартует для {session_id} <<<", flush=True)
    while True:
        if session_states[session_id]["running"]:
            sessions[session_id].update_system()
            await update_opc_from_model_state(session_id, force_send_all=False)
        await asyncio.sleep(1)


# =============================================================================
# 5. ОПРЕДЕЛЕНИЕ API ЭНДПОИНТОВ
# =============================================================================
api_router = APIRouter(prefix="/api")
api_router.include_router(simulation_router)

# =============================================================================
# 6. СБОРКА И ЗАПУСК ПРИЛОЖЕНИЯ FASTAPI
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управляет фоновыми задачами во время жизни приложения."""
    opc_task = asyncio.create_task(opc_adapter.run())
    model_task = asyncio.create_task(update_loop())
    yield
    print("Завершение работы, остановка фоновых задач...")
    await opc_adapter.disconnect()
    model_task.cancel()
    opc_task.cancel()
    await asyncio.gather(model_task, opc_task, return_exceptions=True)

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

app.include_router(api_router)
