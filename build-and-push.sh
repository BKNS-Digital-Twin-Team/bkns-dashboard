#!/bin/bash
set -e

NAMESPACE="kolchedan"
TIMESTAMP=$(date +%Y-%m-%d-%H-%M-%S)
BUILD_DATE=$(date +%Y-%m-%d\ %H:%M:%S)

BACKEND_LATEST="$NAMESPACE/bkns-dashboard-backend:latest"
OPC_LATEST="$NAMESPACE/bkns-dashboard-opc-server:latest"

BACKEND_IMAGE="$NAMESPACE/bkns-dashboard-backend:$TIMESTAMP"
OPC_IMAGE="$NAMESPACE/bkns-dashboard-opc-server:$TIMESTAMP"

# Сборка бэкенда
echo "🔨 Собираем бэкенд..."
docker build --no-cache -t $BACKEND_IMAGE -t $BACKEND_LATEST -f ./backend/Dockerfile.prod .

# Сборка OPC-сервера (исправлен путь к Dockerfile)
echo "🔨 Собираем OPC-сервер..."
docker build --no-cache -t $OPC_IMAGE -t $OPC_LATEST -f ./opc_server/Dockerfile.prod ./opc_server

# Пуш образов
echo "📤 Пушим бэкенд..."
docker push $BACKEND_IMAGE
docker push $BACKEND_LATEST

echo "📤 Пушим OPC-сервер..."
docker push $OPC_IMAGE
docker push $OPC_LATEST

echo "✅ Готово! Образы: $BACKEND_IMAGE, $OPC_IMAGE"