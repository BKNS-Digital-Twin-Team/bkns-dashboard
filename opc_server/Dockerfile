FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY my_server.py .

EXPOSE 4840

CMD ["python", "my_server.py"]