#!/bin/bash

# Скрипт для деплоя docker-compose на удаленный сервер
# Использование: ./deploy.sh [USER@]HOST [SSH_KEY_PATH] [REMOTE_DIR]

set -e  # Прерывать выполнение при ошибках

# Параметры по умолчанию
DEFAULT_SSH_KEY="/home/ars/my_private_key.pem"
DEFAULT_REMOTE_DIR="/home/ubuntu/bkns-dashboard"

# Проверяем обязательный параметр - хост
if [ $# -lt 1 ]; then
    echo "Использование: $0 [USER@]HOST [SSH_KEY_PATH] [REMOTE_DIR]"
    echo "Пример: $0 user@example.com ~/.ssh/my_key ~/my-app"
    exit 1
fi

REMOTE_HOST="$1"
SSH_KEY="${2:-$DEFAULT_SSH_KEY}"
REMOTE_DIR="${3:-$DEFAULT_REMOTE_DIR}"

# Проверяем существование SSH ключа
if [ ! -f "$SSH_KEY" ]; then
    echo "Ошибка: SSH ключ не найден: $SSH_KEY"
    exit 1
fi

# Проверяем существование docker-compose файла
if [ ! -f "docker-compose.server.yml" ]; then
    echo "Ошибка: Файл docker-compose.server.yml не найден в текущей директории"
    exit 1
fi

echo "Деплой на сервер $REMOTE_HOST..."
echo "Используемый SSH ключ: $SSH_KEY"
echo "Удаленная директория: $REMOTE_DIR"

# Создаем удаленную директорию если не существует
ssh -i "$SSH_KEY" "$REMOTE_HOST" "mkdir -p $REMOTE_DIR"

# Копируем docker-compose файл на сервер
echo "Копируем docker-compose.server.yml на сервер..."
scp -i "$SSH_KEY" docker-compose.server.yml "$REMOTE_HOST:$REMOTE_DIR/"

# Останавливаем и удаляем старые контейнеры, запускаем новые
echo "Запускаем docker compose на сервере..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "cd $REMOTE_DIR && sudo docker compose -f docker-compose.server.yml down"
ssh -i "$SSH_KEY" "$REMOTE_HOST" "cd $REMOTE_DIR && sudo docker compose -f docker-compose.server.yml pull
ssh -i "$SSH_KEY" "$REMOTE_HOST" "cd $REMOTE_DIR && sudo docker compose -f docker-compose.server.yml up -d --force-recreate"

echo "Деплой завершен успешно!"
echo "Приложение должно быть доступно на http://$REMOTE_HOST:8000"
