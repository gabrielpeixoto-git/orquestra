# Orquestra - Guia para Agentes

## Comandos

- `uv run poe check` - Executa verificação completa: ruff format --check, ruff check, mypy, pytest, manage.py check, makemigrations --check, import-linter
- `uv run poe smoke` - Executa testes de integração ponta a ponta (cenários de sucesso e falha)
- `uv run poe up` - Sobe Docker Compose com perfil lite (api, relay, worker, beat, db, redis, rabbitmq)
- `uv run poe down` - Para e remove containers do Docker Compose
- `uv run poe demo` - Sobe ambiente, executa seed_demo e inicia servidor de desenvolvimento

## Estrutura do Projeto

- `config/` - Configurações Django (settings modulares, urls, wsgi, asgi, celery)
- `apps/` - Apps Django por contexto (orders, inventory, payments, notifications, audit, orchestrator, outbox, core, dashboard)
- `tests/` - Testes do projeto
- `deploy/` - Configurações de deploy (Dockerfile, docker-compose, Prometheus, Grafana)
- `docs/` - Documentação (ARCHITECTURE.md, ROADMAP.md, ADRs, DESIGN.md, RUNBOOK.md)
- `scripts/` - Scripts utilitários
- `.devin/rules/` - Regras específicas para o agente (ui.md, messaging.md)

## Convenções

- Python 3.14+ com type hints em todas as funções e classes
- Docstrings no padrão Google Style em funções/classes públicas
- Arquivos com no máximo 300 linhas - refatore se exceder
- Máximo 4 parâmetros por função - use dataclasses ou TypedDict para mais
- Early return para reduzir aninhamento
- Nomes descritivos - evite `data`, `temp`, `info`
- Logging via structlog (JSON) em produção, não print
- Variáveis de ambiente via pydantic-settings - nunca hardcode secrets

## Portões de Qualidade

- `uv run poe check` deve estar verde antes de qualquer commit
- Cobertura de testes ≥ 85% em apps/
- Sem erros de mypy (strict mode)
- Sem violações de import-linter

## Regras Anti-Erro

1. Escreva testes junto com o código - cada tarefa do plano cita o teste que a comprova
2. Após cada `uv add`, rode um import-smoke e o `poe check`. Nunca edite uv.lock à mão
3. Não adivinhe assinaturas de API - leia o código instalado ou a doc oficial
4. Mesmo erro 3 vezes = pare, resuma a causa provável e proponha 2 alternativas
5. Nunca altere um teste só para ele passar - corrija a causa
6. Testes de integração com Postgres e RabbitMQ reais (nada de SQLite nem mock)
7. Arquivos < 300 linhas, funções pequenas, type hints em apps/**, sem TODO, sem código comentado
8. Comandos destrutivos (rm -rf, docker system prune, git reset --hard, force push) só com confirmação
9. Toda decisão relevante vira ADR curto em docs/adr/NNNN-titulo.md

## Contextos da Aplicação

- `orders` - Pedidos e estado da saga
- `inventory` - Estoque e reservas
- `payments` - Pagamentos e gateway fake
- `notifications` - Notificações (email, SMS)
- `audit` - Logs de auditoria
- `orchestrator` - Orquestrador da saga
- `outbox` - Transactional Outbox pattern
- `core` - Funcionalidades compartilhadas (health, utilitários)
- `dashboard` - Control Center web

## Comunicação Entre Contextos

- Comunicação exclusivamente via mensagens (RabbitMQ)
- Nunca importe services de outro contexto (enforced por import-linter)
- Use o contrato de mensagem (pydantic v2) em apps/messaging/messages.py
