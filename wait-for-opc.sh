#!/bin/sh
# wait-for-opc.sh

set -e

host="$1"
port="$2"
shift 2

echo "Ожидание готовности OPC-сервера на $host:$port..."
while ! nc -z "$host" "$port"; do
  sleep 1
done

echo "OPC-сервер готов, запуск backend..."
exec "$@"
