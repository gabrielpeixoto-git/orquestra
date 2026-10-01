# ROADMAP - Orquestra

## Fase 0: Fundação
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

## Fase 1: Domínio + API
- [ ] Models e migrações (orders, inventory, payments, notifications, audit, outbox, inbox)
- [ ] Services (create_order, cancel_order, reserve_stock, etc.)
- [ ] DRF API (POST /api/v1/orders com Idempotency-Key)
- [ ] OpenAPI/Documentation (/api/docs)
- [ ] JWT
- [ ] Throttling (Redis)
- [ ] Erros padronizados
- [ ] Comando seed_demo
- [ ] Testes (inclui concorrência de estoque e idempotência)

**Critério de Aceite:** API funcional, idempotência testada, concorrência sem overselling

## Fase 2: Mensageria + Caminho Feliz
- [ ] Transactional Outbox
- [ ] Relay (management command)
- [ ] Inbox (idempotência de consumidores)
- [ ] Contrato de mensagem (pydantic v2)
- [ ] Celery setup (quorum queues)
- [ ] Handlers (inventory, payments, notifications, audit, orchestrator)
- [ ] RabbitMQ setup
- [ ] Testes de integração com RabbitMQ real
- [ ] Comando smoke (sucesso)

**Critério de Aceite:** pedido → saga completa → CONFIRMED, `poe smoke --scenario success` verde

## Fase 3: Confiabilidade
- [ ] Retry com backoff exponencial + jitter
- [ ] DLQ + DLX
- [ ] Replay (comando + endpoint + UI)
- [ ] Compensação
- [ ] Watchdog (beat)
- [ ] Gateway fake com cenários
- [ ] Testes (5 cenários de smoke)

**Critério de Aceite:** 5 cenários de smoke verde (sucesso, estoque insuficiente, pagamento recusado, timeout, DLQ replay)

## Fase 4: Control Center
- [ ] docs/DESIGN.md (tokens Tailwind)
- [ ] Tailwind setup (django-tailwind-cli)
- [ ] Vendorize JS (htmx 2.x, Alpine 3, Chart.js 4)
- [ ] Layout base (dark mode)
- [ ] Página Visão Geral (KPIs, pipeline animado)
- [ ] Página Pedidos (tabela viva, filtros)
- [ ] Página Detalhe (timeline vertical)
- [ ] Página Falhas/DLQ (replay, descarte)
- [ ] Página Laboratório (gerar pedidos, injetar falhas)
- [ ] Página Saúde dos Serviços
- [ ] Testes (view, N+1, validação no Preview)

**Critério de Aceite:** Responsivo (375/768/1280), acessível (AA), zero console errors, validado no Preview

## Fase 5: Observabilidade
- [ ] Logs JSON com structlog (correlation_id)
- [ ] OpenTelemetry (Django, Celery, psycopg, Redis)
- [ ] Jaeger (trace completo)
- [ ] Prometheus + métricas de negócio
- [ ] Grafana com dashboards provisionados
- [ ] Página Saúde (atualizada)
- [ ] docs/RUNBOOK.md

**Critério de Aceite:** Trace completo API→outbox→relay→workers no Jaeger

## Fase 6: CI/CD
- [ ] CI completo (lint, types, testes, service containers, Docker build, pip-audit, drift OpenAPI)
- [ ] Release (GHCR em tag v*)
- [ ] Dependabot
- [ ] actionlint
- [ ] Badges

**Critério de Aceite:** CI verde, release funcional

## Fase 7: Docs e Acabamento
- [ ] README pt-BR (resumo EN, Mermaid, quickstart 3 comandos)
- [ ] Comando demo
- [ ] ADRs
- [ ] LICENSE MIT
- [ ] Teste de clone limpo → up → demo
- [ ] Atualizar ROADMAP

**Critério de Aceite:** Demo funciona, ROADMAP completo

## Fase 8 (Opcional): Kubernetes
- [ ] Kubernetes manifests (kustomize, kind)
- [ ] SSE no lugar do polling

**Critério de Aceite:** kustomize build válido, kind apply funciona, SSE funciona
