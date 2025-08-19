FROM node:20-alpine as builder

WORKDIR /app

# Копируем package файлы
COPY package*.json ./
RUN npm ci

# Копируем исходники и собираем
COPY . .
RUN npm run build

# Результат будет в /app/build



