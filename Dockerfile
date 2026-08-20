FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

WORKDIR /app

RUN pip install --no-cache-dir poetry==2.3.2

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main

COPY . .

RUN mkdir -p /app/staticfiles /app/media

EXPOSE 8000
