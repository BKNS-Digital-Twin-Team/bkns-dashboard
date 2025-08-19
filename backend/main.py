
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
app.include_router(simulation_router)

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

