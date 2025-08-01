#!/bin/bash

# Запускаем OPC сервер в фоне
python /app/backend/app/opc_server/my_server.py &

# Ждем инициализации OPC сервера
sleep 3

# Запускаем FastAPI
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000