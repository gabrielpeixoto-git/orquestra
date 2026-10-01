# ADR-0001: Stack Tecnológica

## Status

Aceito

## Contexto

Precisamos escolher uma stack tecnológica moderna e estável para implementar a plataforma Orquestra, focando em confiabilidade, mensageria e observabilidade.

## Decisão

Escolhemos as seguintes versões (confirmadas out/2026):

### Backend
- Python 3.13 (ruff e mypy não suportam 3.14 ainda)
- Django 6.1 (fallback 6.0, fallback 5.2 LTS)
- DRF 3.18+
- Celery 5.6
- PostgreSQL 18 (volume em /var/lib/postgresql)
- RabbitMQ 4.x (imagem -management, quorum queues)
- Redis 8 (cache, throttling, locks)

### Frontend
- Templates Django
- htmx 2.x (NÃO usar htmx 4)
- Alpine.js 3
- Tailwind CSS v4 via django-tailwind-cli
- Chart.js 4

### Qualidade
- ruff (lint + format)
- mypy + django-stubs + djangorestframework-stubs
- pytest + pytest-django + pytest-cov + factory-boy
- import-linter
- pre-commit
- pip-audit

### Observabilidade
- structlog (JSON)
- OpenTelemetry (Django, Celery, psycopg, Redis)
- Jaeger
- Prometheus + Grafana
- rabbitmq_prometheus

### CI/CD
- GitHub Actions
- actions/checkout v7
- astral-sh/setup-uv v8
- Docker multi-stage não-root
- GHCR para imagens

## Consequências

### Positivas
- Versões estáveis e bem suportadas
- Pydantic 2.12+ suporta Python 3.14
- Django 6.1 suporta Python 3.12-3.14
- OpenTelemetry 0.47b0+ suporta Python 3.14
- RabbitMQ 4.x tem quorum queues nativas

### Negativas
- Pydantic v1 não suporta Python 3.14
- OpenTelemetry 0.48+ não suporta Python 3.14
- Precisamos fixar versões para evitar breaking changes

## Ajustes Feitos Durante a Fase 0

- Python: 3.14 → 3.13 (ruff e mypy não suportam 3.14 ainda)
- Pydantic: 2.10+ → 2.12+ (para suportar Python 3.14/3.13)
- pydantic-settings: 2.7+ → 2.6+ (compatível com pydantic 2.12)
- OpenTelemetry: 1.30+ → 1.27+ (para suportar Python 3.14/3.13)
- OpenTelemetry instrumentation: 0.50b0+ → 0.47b0+ (para suportar Python 3.14/3.13)
- structlog: 25.0+ → 25.1+ (versão disponível)
- import-linter: 1.14+ → 1.12+ (versão disponível)
