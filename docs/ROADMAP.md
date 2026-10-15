# ROADMAP - Orquestra

## Fase 0: Fundação ✅
- [x] Instalar uv
- [x] Criar estrutura do projeto
- [x] Configurar pyproject.toml com dependências
- [x] Criar estrutura Django (config, apps, tests, deploy, docs, scripts)
- [x] Configurar settings modulares com pydantic-settings
- [x] Criar Dockerfile multi-stage não-root
- [x] Criar docker-compose.yml com perfis
- [x] Implementar endpoints de health (/health/live, /health/ready)
- [x] Configurar pre-commit hooks
- [x] Criar CI mínimo no GitHub Actions
- [x] Criar documentação (AGENTS.md, ARCHITECTURE.md, ROADMAP.md, ADR-0001)
- [x] Criar .gitignore e commit inicial
- [x] Executar uv run poe check e validar

**Critério de Aceite:** `uv run poe up` + `/health/ready` = 200, `poe check` verde

## Fase 1: Domínio + API ✅
- [x] Models e migrações (orders, inventory, payments, notifications, audit, outbox, inbox)
- [x] Services (create_order, cancel_order, reserve_stock, etc.)
- [x] DRF API (POST /api/v1/orders com Idempotency-Key)
- [x] OpenAPI/Documentation (/api/docs)
- [x] JWT
- [x] Throttling (Redis)
- [x] Erros padronizados
- [x] Comando seed_demo
- [x] Testes (inclui concorrência de estoque e idempotência)

**Critério de Aceite:** API funcional, idempotência testada, concorrência sem overselling

## Fase 2: Mensageria + Caminho Feliz ✅
- [x] Transactional Outbox
- [x] Relay (management command)
- [x] Inbox (idempotência de consumidores)
- [x] Contrato de mensagem (pydantic v2)
- [x] Celery setup (quorum queues)
- [x] Handlers (inventory, payments, notifications, audit, orchestrator)
- [x] RabbitMQ setup
- [x] Testes de integração com RabbitMQ real
- [x] Comando smoke (sucesso)

**Critério de Aceite:** pedido → saga completa → CONFIRMED, `poe smoke --scenario success` verde

## Fase 3: Confiabilidade ✅
- [x] Retry com backoff exponencial + jitter
- [x] DLQ + DLX
- [x] Replay (comando + endpoint + UI)
- [x] Compensação
- [x] Watchdog (beat)
- [x] Gateway fake com cenários
- [x] Testes (5 cenários de smoke)

**Critério de Aceite:** 5 cenários de smoke verde (sucesso, estoque insuficiente, pagamento recusado, timeout, DLQ replay)

## Fase 4: Control Center ✅
- [x] docs/DESIGN.md (tokens Tailwind)
- [x] Tailwind setup (via CDN)
- [x] Vendorize JS (htmx 2.x, Alpine 3, Chart.js 4 via CDN)
- [x] Layout base (dark mode)
- [x] Página Visão Geral (KPIs, pipeline)
- [x] Página Pedidos (tabela viva, filtros)
- [x] Página Detalhe (timeline vertical)
- [x] Página Falhas/DLQ (replay, descarte)
- [x] Página Laboratório (gerar pedidos, injetar falhas)
- [x] Página Saúde dos Serviços
- [x] Testes (view, N+1, validação)

**Critério de Aceite:** Dashboard funcional com auto-refresh, testes passando

## Fase 5: Observabilidade ✅
- [x] Logs JSON com structlog (correlation_id)
- [x] OpenTelemetry (Django, Celery, psycopg, Redis)
- [x] Jaeger (trace completo)
- [x] Prometheus + métricas de negócio
- [x] Grafana com dashboards provisionados
- [x] Página Saúde (atualizada)
- [x] docs/RUNBOOK.md

**Critério de Aceite:** Trace completo API→outbox→relay→workers no Jaeger

## Fase 6: CI/CD ✅
- [x] CI completo (lint, types, testes, service containers, Docker build, pip-audit, drift OpenAPI)
- [x] Release (GHCR em tag v*)
- [x] Dependabot
- [x] actionlint
- [x] Badges

**Critério de Aceite:** CI verde, release funcional

## Fase 7: Docs e Acabamento ✅
- [x] README pt-BR (resumo EN, Mermaid, quickstart 3 comandos)
- [x] Comando demo
- [x] ADRs
- [x] LICENSE MIT
- [x] Teste de clone limpo → up → demo
- [x] Atualizar ROADMAP

**Critério de Aceite:** Demo funciona, ROADMAP completo

## Fase 8 (Opcional): Kubernetes ✅
- [x] Kubernetes manifests (kustomize, kind)
- [x] SSE no lugar do polling

**Critério de Aceite:** kustomize build válido, kind apply funciona, SSE funciona

## Fase 9: Consumidores Alternativos ✅
- [x] Consumer RabbitMQ alternativo (scripts/consumer.py)
- [x] Mapeamento por fila e tipo de mensagem
- [x] Suporte a múltiplos handlers por mensagem
- [x] Fix encoding no Windows
- [x] Integração com docker-compose (perfil alternative)
- [x] Documentação no README e TROUBLESHOOTING

**Critério de Aceite:** Fluxo completo da saga funcionando com consumidores alternativos
