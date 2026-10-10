# Orquestra

[![CI](https://github.com/gabri/orquestra/workflows/CI/badge.svg)](https://github.com/gabri/orquestra/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/gabri/orquestra/branch/main/graph/badge.svg)](https://codecov.io/gh/gabri/orquestra)
[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-6.1+-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Resumo

Plataforma de processamento de pedidos orientada a eventos com saga orquestrada, construída com Django, Celery, RabbitMQ e PostgreSQL.

A Orquestra implementa um padrão de saga orquestrada para gerenciar transações distribuídas de forma confiável, com mecanismos de retry, dead letter queue e compensação automática.

## Summary

Event-driven order processing platform with orchestrated saga pattern, built with Django, Celery, RabbitMQ, and PostgreSQL.

Orquestra implements an orchestrated saga pattern to manage distributed transactions reliably, with retry mechanisms, dead letter queue, and automatic compensation.

## Arquitetura

```mermaid
graph TD
    A[API /api/v1/orders] -->|Create Order| B[Orders Service]
    B -->|OrderCreated| C[Outbox]
    C -->|Relay| D[RabbitMQ]
    D -->|StockReserved| E[Inventory Handler]
    D -->|PaymentProcessed| F[Payments Handler]
    D -->|NotificationSent| G[Notifications Handler]
    D -->|AuditLog| H[Audit Handler]
    E -->|PaymentSucceeded| D
    F -->|OrderConfirmed| I[Orchestrator]
    F -->|PaymentFailed| I
    I -->|OrderFailed| D
    J[Watchdog] -->|Timeout| K[Cancel Order]
    K -->|Release Stock| L[Inventory]
```

## Quick Start

```bash
# 1. Subir infraestrutura
uv run poe up

# 2. Rodar migrations e seed
uv run python manage.py migrate
uv run python manage.py seed_demo

# 3. Iniciar servidor
uv run python manage.py runserver
```

Acesse:
- **API**: http://localhost:8000/api/docs
- **Dashboard**: http://localhost:8000/
- **Health**: http://localhost:8000/health/detailed

## Kubernetes Deployment

For production deployment with Kubernetes:

```bash
# Build image
docker build -t orquestra:latest .

# Create kind cluster (local)
uv run poe k8s-kind-create

# Deploy
uv run poe k8s-apply

# Access at http://localhost:8000
```

See [docs/KUBERNETES.md](docs/KUBERNETES.md) for detailed deployment guide.

## Documentação

- [Arquitetura](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Runbook](docs/RUNBOOK.md)
- [ADRs](docs/adr/)

## Licença

MIT
