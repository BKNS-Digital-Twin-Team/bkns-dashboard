FROM python:3.11-slim 

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

ENV PORT=8000
EXPOSE $PORT

# Исправленный ENTRYPOINT
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]