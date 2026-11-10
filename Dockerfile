FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend /app/frontend/dist /app/frontend/dist
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && addgroup --system django \
    && adduser --system --ingroup django django \
    && chown -R django:django /app
USER django
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "SmileManager.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
