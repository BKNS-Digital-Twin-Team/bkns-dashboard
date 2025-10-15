#!/bin/bash

# Скрипт для синхронизации папки sessions с удаленным сервером
# Использование: ./sync-sessions.sh [USER@]HOST [SSH_KEY_PATH] [REMOTE_DIR]

set -e

# Параметры по умолчанию
DEFAULT_SSH_KEY="/home/ars/my_private_key.pem"
DEFAULT_REMOTE_DIR="/home/ubuntu/bkns-dashboard"
LOCAL_SESSIONS_DIR="backend/sessions"

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

# Проверяем существование локальной папки sessions
if [ ! -d "$LOCAL_SESSIONS_DIR" ]; then
    echo "Ошибка: Локальная папка 'sessions' не найдена по пути: $LOCAL_SESSIONS_DIR"
    echo "Убедитесь, что вы запускаете скрипт из корневой директории проекта"
    exit 1
fi

echo "Синхронизация папки sessions с сервером $REMOTE_HOST..."
echo "Используемый SSH ключ: $SSH_KEY"
echo "Удаленная директория: $REMOTE_DIR"
echo "Локальная папка sessions: $LOCAL_SESSIONS_DIR"

# Создаем удаленную папку sessions если не существует
ssh -i "$SSH_KEY" "$REMOTE_HOST" "mkdir -p $REMOTE_DIR/sessions"

# Синхронизируем папку sessions с помощью rsync (если установлен)
if command -v rsync &> /dev/null; then
    echo "Используется rsync для синхронизации..."
    rsync -avz -e "ssh -i $SSH_KEY" "$LOCAL_SESSIONS_DIR/" "$REMOTE_HOST:$REMOTE_DIR/sessions/"
else
    echo "Используется scp для копирования..."
    scp -ri "$SSH_KEY" "$LOCAL_SESSIONS_DIR/" "$REMOTE_HOST:$REMOTE_DIR/sessions/"
fi

echo "Синхронизация завершена успешно!"