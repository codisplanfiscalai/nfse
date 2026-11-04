# Build do painel Vue (imagem publica somente depois que o CI concluir testes).
FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CODISPLAN_HOST=0.0.0.0 \
    CODISPLAN_DATA_DIR=/var/lib/codisplan-nfse CODISPLAN_REQUIRE_EXTERNAL_KEY=1
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt && useradd -r -u 11010 nfse \
    && mkdir -p /var/lib/codisplan-nfse && chown nfse:nfse /var/lib/codisplan-nfse
COPY backend/ /app/backend/
COPY --from=frontend /build/dist /app/frontend/dist
ENV PYTHONPATH=/app/backend
USER nfse
EXPOSE 8765
CMD ["python","/app/backend/run_server.py"]
