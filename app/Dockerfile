FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /

# Создаём папку для логов
RUN mkdir -p /app/logs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Убедимся, что main.py исполняемый
RUN chmod +x main.py

EXPOSE 5000

CMD ["python", "main.py"]