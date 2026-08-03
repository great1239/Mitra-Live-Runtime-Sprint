FROM alpine/git:2.49.1 AS source

ARG KANISHK_RUNTIME_REPOSITORY=https://github.com/blackholeinfiverse107-creator/Mitra-runtime_execution_fabric.git
ARG KANISHK_RUNTIME_REF=74a5efdd4d3c079d415903c4e151250bf4642f57
RUN git clone --filter=blob:none --no-checkout "$KANISHK_RUNTIME_REPOSITORY" /source \
    && cd /source \
    && git checkout "$KANISHK_RUNTIME_REF"

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app:/opt/kanishk-runtime

WORKDIR /app
COPY --from=source /source /opt/kanishk-runtime
COPY integration_services/requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir \
    -r /opt/kanishk-runtime/requirements.txt \
    -r /app/requirements.txt

COPY integration_services /app/integration_services

RUN useradd --system --create-home --home-dir /home/runtime runtime \
    && mkdir -p /data/kanishk-runtime \
    && chown -R runtime:runtime /data /home/runtime

USER runtime

CMD ["uvicorn", "integration_services.kanishk_runtime_adapter:app", "--host", "0.0.0.0", "--port", "8000"]
