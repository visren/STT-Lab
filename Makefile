# Host tooling for reproducible local builds (optional helpers).
.PHONY: help install install-ci install-editable test test-ci doctor \
	model-lab-build model-lab model-lab-doctor vault-up vault-down \
	vault-prod-up backup compile clean

COMPOSE := docker compose -f envs/docker-compose.yml --env-file envs/.env
COMPOSE_PROD := docker compose -f envs/docker-compose.yml -f envs/docker-compose.prod.yml --env-file envs/.env
export DOCKER_BUILDKIT ?= 1
export COMPOSE_DOCKER_CLI_BUILD ?= 1

help:
	@echo "STT Lab targets:"
	@echo "  make install            Full local deps (ML + research + dictation)"
	@echo "  make install-ci         Fast unit-test deps (no torch)"
	@echo "  make test / test-ci     Run pytest"
	@echo "  make doctor             Local import / path sanity"
	@echo "  make model-lab-build    Build optimized model-lab image"
	@echo "  make model-lab          Interactive model-lab shell"
	@echo "  make model-lab-doctor   Smoke imports inside the image"
	@echo "  make vault-up           Start dataset-vault"
	@echo "  make vault-prod-up      Vault + TLS proxy overlay"
	@echo "  make backup             Run vault backup script"
	@echo "  make compile            Byte-compile Python sources"

install:
	python -m pip install -U pip setuptools wheel
	python -m pip install -r requirements.txt
	python -m pip install -e .

install-ci:
	python -m pip install -U pip
	python -m pip install -r requirements/ci.txt
	python -m pip install -e .

install-editable:
	python -m pip install -e .

test:
	python -m pytest tests/

test-ci:
	python -m pytest tests/ -q

doctor:
	python scripts/doctor.py

compile:
	python -m compileall -q stt_lab apps envs tests

model-lab-build:
	$(COMPOSE) build model-lab

model-lab:
	$(COMPOSE) run --rm model-lab

model-lab-doctor:
	$(COMPOSE) run --rm model-lab doctor

vault-up:
	$(COMPOSE) up -d dataset-vault dataset-vault-init

vault-down:
	$(COMPOSE) down

vault-prod-up:
	./envs/vault/scripts/gen-certs.sh
	$(COMPOSE_PROD) up -d

backup:
	./envs/vault/scripts/backup.sh

clean:
	rm -rf .pytest_cache **/__pycache__ *.egg-info .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
