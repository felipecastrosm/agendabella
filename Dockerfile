# Imagem única: compila o front-end Angular e serve tudo pela API FastAPI.

# ---- Etapa 1: build do front-end ----
FROM node:24-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Etapa 2: API em Python ----
FROM python:3.12-slim AS api
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    FRONTEND_DIST=/app/static \
    PORT=8000
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY --from=frontend /frontend/dist/frontend/browser ./static

# Executa sem privilégios de root.
RUN useradd --create-home --uid 10001 agendabella
USER agendabella

EXPOSE 8000
CMD ["sh", "-c", "python -m app.bootstrap && uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
