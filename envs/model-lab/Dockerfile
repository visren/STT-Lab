FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/root/.cache/huggingface

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install CPU-friendly defaults; override torch at runtime if GPU image is used.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt \
    && pip install minio pytest

COPY envs/model-lab/entrypoint.sh /usr/local/bin/model-lab-entry
RUN chmod +x /usr/local/bin/model-lab-entry

ENTRYPOINT ["/usr/local/bin/model-lab-entry"]
CMD ["bash"]
