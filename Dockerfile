FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    YOLO_CONFIG_DIR=/tmp/ultralytics \
    MPLCONFIGDIR=/tmp/matplotlib

# OpenCV/YOLO and PDF generation need these native libraries.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config libcairo2-dev libgl1 libglib2.0-0 libgomp1 fonts-dejavu-core curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /tmp/requirements.txt
# Keep the repository pins, using CPU wheels to avoid downloading CUDA libraries.
RUN python -c "from pathlib import Path; lines=Path('/tmp/requirements.txt').read_text().splitlines(); Path('/tmp/requirements-torch.txt').write_text('\n'.join(line for line in lines if line.startswith(('torch==', 'torchvision=='))) + '\n')" \
    && python -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu -r /tmp/requirements-torch.txt \
    && python -m pip install --no-cache-dir -r /tmp/requirements.txt \
    && python -m pip check

RUN useradd --create-home --uid 1000 smilemanager \
    && mkdir -p /app/media /var/lib/smilemanager/mail \
    && chown -R smilemanager:smilemanager /app /var/lib/smilemanager
COPY --chown=smilemanager:smilemanager . /app
COPY --chmod=755 docker/entrypoint.sh /usr/local/bin/smilemanager-entrypoint

USER smilemanager
EXPOSE 8000
ENTRYPOINT ["smilemanager-entrypoint"]
FROM runtime AS development
CMD ["runserver", "0.0.0.0:8000"]

FROM runtime AS fullstack
COPY --from=frontend --chown=smilemanager:smilemanager /app/frontend/dist /app/frontend/dist
CMD ["gunicorn", "SmileManager.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
