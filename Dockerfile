FROM python:3.13.17-slim-bookworm AS runtime
LABEL org.opencontainers.image.title="Codisplan NFS-e" \
      org.opencontainers.image.source="https://github.com/codisplanfiscalai/nfse" \
      org.opencontainers.image.description="Distribuição ADN e relatórios fiscais"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 NFSE_DATA_DIR=/data
ARG APP_VERSION=0.2.0
ENV NFSE_VERSION=${APP_VERSION}
WORKDIR /app
COPY requirements-server.txt .
RUN python -m pip install --no-cache-dir -r requirements-server.txt
COPY src/ src/
COPY VERSION pyproject.toml ./
RUN mkdir /data && chown 10001:10001 /data && chmod 700 /data
USER 10001:10001
EXPOSE 8765
ENTRYPOINT ["python","-m","src.nfse.server"]

FROM runtime AS test
USER root
RUN python -m pip install --no-cache-dir pytest==9.0.2
USER 10001:10001
COPY --chown=10001:10001 tests/ tests/
COPY --chown=10001:10001 desktop/ desktop/
RUN python -m pytest -q

FROM runtime AS final
