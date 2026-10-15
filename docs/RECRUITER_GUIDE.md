# Guia para Recrutadores - Orquestra

## 🎯 Resumo Executivo

**Orquestra** é uma plataforma de processamento de pedidos orientada a eventos que demonstra habilidades avançadas em:
- Arquitetura de sistemas distribuídos
- Padrões de resiliência e confiabilidade
- Engenharia de software de alta qualidade
- Observabilidade em produção
- CI/CD e DevOps

## 💼 Perfil do Candidato

Este projeto evidencia experiência em:
- **Nível**: Engenheiro de Software Sênior / Tech Lead
- **Foco**: Backend, Arquitetura, Confiabilidade
- **Stack**: Python, Django, RabbitMQ, PostgreSQL, Kubernetes
- **Práticas**: TDD, CI/CD, Observabilidade, DDD

## 🏗️ Arquitetura Técnica

### Por que essa arquitetura?

**Monólito Modular** vs Microservices:
- Monólito modular é mais simples para começar e evita overhead de rede
- Contextos isolados (bounded contexts) permitem evolução para microservices
- Comunicação via mensagens garante baixo acoplamento

**Saga Orquestrada** vs Coreografada:
- Orquestração centralizada é mais fácil de debugar e monitorar
- Permite implementar timeouts e compensações de forma previsível
- Adequado para fluxos de negócio complexos

**Transactional Outbox**:
- Resolve o problema de consistência entre DB e broker
- Garante que mensagens são publicadas apenas se a transação commitar
- Pattern essencial em sistemas event-driven

## 🔍 Pontos Técnicos a Explorar em Entrevista

### 1. Idempotência
**Pergunta**: Como você garante que mensagens duplicadas não causam problemas?

**Resposta esperada**:
- API: Idempotency-Key + hash do corpo com constraint UNIQUE
- Consumidores: InboxMessage com UNIQUE(consumer, message_id)
- Explicação de trade-offs (storage vs consistência)

### 2. Concorrência em Estoque
**Pergunta**: Como você evita overselling com múltiplas requisições simultâneas?

**Resposta esperada**:
- SELECT FOR UPDATE com database lock
- Transação atômica
- Testes de concorrência com 50 threads
- Explicação de deadlocks e como evitá-los

### 3. Retry e DLQ
**Pergunta**: Como você lida com falhas transitórias vs permanentes?

**Resposta esperada**:
- Retry apenas para erros transitórios (ConnectionError, Timeout)
- Backoff exponencial + jitter para evitar thundering herd
- DLQ para erros permanentes após esgotar retry
- Replay manual com investigação prévia

### 4. Observabilidade
**Pergunta**: Como você debuga um pedido que falhou em produção?

**Resposta esperada**:
- correlation_id em todos os logs
- Distributed tracing no Jaeger (API → outbox → relay → workers)
- Métricas Prometheus (taxa de erro, latência P95)
- Dashboards Grafana com alertas

### 5. Saga Travada
**Pergunta**: O que acontece se um gateway de pagamento não responde?

**Resposta esperada**:
- Watchdog Celery Beat detecta timeouts
- Compensação automática (cancela pedido, libera estoque)
- OrderFailed message para notificação
- Explicação de eventual consistency

## 📊 Métricas de Qualidade

| Métrica | Valor | Status |
|---------|-------|--------|
| Cobertura de testes | 80%+ | ✅ Verde |
| Type safety | mypy strict | ✅ 0 erros |
| Linting | ruff 50+ regras | ✅ 0 violações |
| CI/CD | GitHub Actions | ✅ Passando |
| Security | pip-audit | ✅ 0 vulnerabilidades |
| Performance | < 100ms P95 (API) | ✅ Otimizado |

## 🚀 Decisões de Arquitetura (ADRs)

### ADR-0001: Stack Tecnológica
- Python 3.13 por estabilidade e tooling
- Django 6.1 por maturidade e ecossistema
- RabbitMQ 4.x por quorum queues nativas
- PostgreSQL 18 por performance e features
- OpenTelemetry por padrão de indústria

### Trade-offs Considerados
- Monólito vs Microservices: Monólito para simplicidade inicial
- Celery vs Pika: Celery por features avançadas (delayed delivery)
- Sync vs Async: Sync Django por simplicidade, async futuro

## 🎓 O que o Candidato Aprendiu

### Hard Skills
- Padrões de resiliência (retry, circuit breaker, bulkhead)
- Domain-Driven Design (bounded contexts, aggregates)
- Event-driven architecture (contracts, evolution)
- Observabilidade (tracing, metrics, logs)
- CI/CD pipelines e GitOps

### Soft Skills
- Documentação técnica (ADRs, runbooks, troubleshooting)
- Debugging de sistemas distribuídos
- Comunicação técnica (README para recrutadores)
- Priorização de features (roadmap por fases)
- Decisões baseadas em trade-offs

## 🧪 Como Avaliar o Projeto

### Review de Código
Sugestão de arquivos para revisar:
1. `apps/orders/services.py` - Lógica de negócio core
2. `apps/outbox/services.py` - Transactional outbox
3. `apps/orchestrator/handlers.py` - Saga orquestrada
4. `config/celery.py` - Configuração avançada Celery
5. `apps/dashboard/views.py` - Views bem estruturadas

### Perguntas Técnicas Sugeridas
1. "Por que você escolheu saga orquestrada ao invés de coreografada?"
2. "Como você garante idempotência em consumidores?"
3. "O que acontece se o RabbitMQ cair durante o relay?"
4. "Como você scale este sistema para 10x mais pedidos?"
5. "Quais são os principais bottlenecks e como você resolveu?"

### Perguntas de Comportamento
1. "Qual foi o desafio mais difícil que você enfrentou neste projeto?"
2. "Como você priorizou features ao longo do roadmap?"
3. "O que você faria diferente se pudesse recomeçar?"
4. "Como você garante qualidade de código ao longo do tempo?"

## 📱 Demonstração ao Vivo

### Quick Demo (5 minutos)
```bash
# 1. Subir ambiente
uv run poe demo

# 2. Criar pedido via API
curl -X POST http://localhost:8000/api/v1/orders/ \
  -H "Idempotency-Key: demo-1" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"sku": "PROD-001", "quantity": 2}]}'

# 3. Assistir saga no dashboard
# Acessar http://localhost:8000/orders/<uuid>/
# Ver timeline em tempo real

# 4. Injetar falha no laboratório
# Acessar http://localhost:8000/laboratory/
# Criar pedido com estoque insuficiente
# Ver compensação automática
```

### Deep Dive (30 minutos)
- Explicar arquitetura com diagrama Mermaid
- Mostrar traces no Jaeger
- Demonstrar replay de DLQ
- Explicar configuração do Celery
- Mostrar métricas no Grafana

## 🎯 Por que Contratar?

### Competências Técnicas
- Arquitetura de sistemas distribuídos
- Padrões de resiliência e confiabilidade
- Observabilidade em produção
- CI/CD e DevOps

### Competências de Engenharia
- Documentação técnica clara
- Testes de alta qualidade
- Código limpo e type-safe
- Decisões baseadas em trade-offs

### Potencial de Crescimento
- Aptidão para arquitetura avançada
- Capacidade de ensinar e documentar
- Foco em qualidade e confiabilidade
- Visão de produto e roadmap

## 📞 Contato

Para mais informações sobre este projeto ou o candidato:
- LinkedIn: [seu perfil]
- GitHub: https://github.com/gabri/orquestra
- Email: [seu email]

---

**Este projeto foi desenvolvido para demonstrar habilidades técnicas de nível sênior em engenharia de software backend.**
