#!/bin/bash
set -e

NAMESPACE="kolchedan"
BACKEND_IMAGE="$NAMESPACE/bkns-dashboard-backend:latest"
OPC_IMAGE="$NAMESPACE/bkns-dashboard-opc-server:latest"

echo "🔨 Сборка backend (Dockerfile.prod, контекст = весь проект)..."
docker build -t $BACKEND_IMAGE -f ./backend/Dockerfile.prod .

echo "🔨 Сборка OPC-сервера..."
docker build -t $OPC_IMAGE ./opc_server

echo "📤 Пушим backend..."
docker push $BACKEND_IMAGE

echo "📤 Пушим OPC-сервер..."
docker push $OPC_IMAGE

echo "✅ Готово!"
