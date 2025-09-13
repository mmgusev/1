# Dockerfile
FROM python:3.11-slim

# Установка зависимостей для компиляции psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходники
COPY app/ .

# Экспорт порта (для удобства, хотя приложение не веб-сервис)
EXPOSE 5000

# Запуск приложения
CMD ["python", "main.py"]