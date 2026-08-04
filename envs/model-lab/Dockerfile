# syntax=docker/dockerfile:1.7
# Optimized model-lab image:
#   - BuildKit pip/apt caches
#   - CPU torch wheels (smaller, faster than CUDA defaults)
#   - Multi-stage (no compilers in runtime)
#   - Non-root user
#
# Build:
#   DOCKER_BUILDKIT=1 docker compose -f envs/docker-compose.yml build model-lab
#   make model-lab-build

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=0 \
    HF_HOME=/home/lab/.cache/huggingface \
    XDG_CACHE_HOME=/home/lab/.cache \
    PATH="/home/lab/.local/bin:${PATH}"

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg \
      curl \
      ca-certificates \
      libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

FROM base AS builder

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements/base.txt requirements/ml.txt requirements/model-lab.txt /build/requirements/

# CPU torch first (pins the heavy layer for cache reuse), then the rest.
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel \
    && pip install --index-url "${TORCH_INDEX_URL}" \
         "torch>=2.2.0,<3" "torchaudio>=2.2.0,<3" \
    && pip install -r /build/requirements/model-lab.txt

# Bake library for import smoke (compose still bind-mounts for live edits).
COPY pyproject.toml README.md /build/
COPY stt_lab /build/stt_lab
COPY envs/model_lab /build/envs/model_lab
COPY envs/__init__.py /build/envs/__init__.py
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-deps /build \
    && python -c "import stt_lab, envs.model_lab.cli; print('bake-ok', stt_lab.__version__)"

FROM base AS runtime

ARG APP_UID=1000
ARG APP_GID=1000

RUN groupadd --gid "${APP_GID}" lab \
    && useradd --uid "${APP_UID}" --gid lab --create-home --shell /bin/bash lab

COPY --from=builder /usr/local /usr/local

COPY envs/model-lab/entrypoint.sh /usr/local/bin/model-lab-entry
RUN chmod 755 /usr/local/bin/model-lab-entry \
    && mkdir -p /workspace /home/lab/.cache \
    && chown -R lab:lab /workspace /home/lab

WORKDIR /workspace
USER lab

# Default cache lives in the named volume mounted at /home/lab/.cache
VOLUME ["/home/lab/.cache"]

ENTRYPOINT ["/usr/local/bin/model-lab-entry"]
CMD ["bash"]
