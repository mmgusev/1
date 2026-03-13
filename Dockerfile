FROM python:3.11-slim

WORKDIR /app

COPY app ./app
COPY tests ./tests
COPY requirements.txt ./requirements.txt
COPY schema.sql ./schema.sql
COPY demo_data.sql ./demo_data.sql
COPY create_user_and_grants.sql ./create_user_and_grants.sql

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["python","app/main.py"]