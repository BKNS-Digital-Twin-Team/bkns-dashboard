#!/bin/bash
set -e

NAMESPACE="kolchedan"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
BACKEND_IMAGE="$NAMESPACE/bkns-dashboard-backend:$TIMESTAMP"
BACKEND_LATEST="$NAMESPACE/bkns-dashboard-backend:latest"
OPC_IMAGE="$NAMESPACE/bkns-dashboard-opc-server:$TIMESTAMP"
OPC_LATEST="$NAMESPACE/bkns-dashboard-opc-server:latest"

# Очистка предыдущих сборок
echo "🧹 Очистка предыдущих сборок..."
docker system prune -f

# Сборка бэкенда с фронтендом
echo "🔨 Сборка backend (Dockerfile.prod)..."
docker build --no-cache -t $BACKEND_IMAGE -t $BACKEND_LATEST -f ./backend/Dockerfile.prod .
echo "🔨 Сборка OPC-сервера..."
docker build --no-cache -t $OPC_IMAGE -t $OPC_LATEST ./opc_server

# Пуш образов
echo "📤 Пушим backend..."
docker push $BACKEND_IMAGE
docker push $BACKEND_LATEST

echo "📤 Пушим OPC-сервер..."
docker push $OPC_IMAGE
docker push $OPC_LATEST

echo "✅ Готово! Образы: $BACKEND_IMAGE, $OPC_IMAGE"