# Arquitetura do Orquestra

## Visão Geral

Orquestra é uma plataforma de processamento de pedidos orientada a eventos implementada como um monólito modular com processos separados. O sistema usa uma saga orquestrada para coordenar os serviços e garantir consistência eventual em um ambiente distribuído.

## Padrões Arquiteturais

### Monólito Modular

O projeto é um único repositório Django com apps organizados por contexto (bounded context). Cada contexto é dono das suas tabelas e só conversa com os outros por mensagens.

**Contextos:**
- `orders` - Gestão de pedidos e estado da saga
- `inventory` - Gestão de estoque e reservas
- `payments` - Processamento de pagamentos
- `notifications` - Envio de notificações
- `audit` - Logs de auditoria
- `orchestrator` - Orquestrador da saga
- `outbox` - Transactional Outbox pattern
- `core` - Funcionalidades compartilhadas
- `dashboard` - Control Center web

### Transactional Outbox Pattern

Todas as mudanças de estado são gravadas junto com um evento no outbox na mesma transação. Um processo relay lê eventos não-publicados, publica no RabbitMQ e marca como publicado.

**Benefícios:**
- Garante que mensagens são publicadas apenas se a transação commitar
- Entrega at-least-once
- Desacopla a escrita no banco da publicação no broker

### Saga Orquestrada

O orquestrador coordena o fluxo da saga através de eventos. Cada etapa tem um estado bem definido e deadlines configuráveis.

**Estados da Saga:**
- PENDING - Pedido criado
- STOCK_RESERVED - Estoque reservado
- PAYMENT_SUCCEEDED - Pagamento aprovado
- CONFIRMED - Saga completa
- CANCELLED - Saga cancelada (estoque insuficiente ou pagamento recusado)

**Compensação:**
- Pagamento recusado → libera estoque → CANCELLED
- Estoque insuficiente → CANCELLED
- Timeout → watchdog compensa → CANCELLED

## Contrato de Mensagem

Todas as mensagens seguem um contrato pydantic v2 versionado:

```python
class BaseMessage(BaseModel):
    message_id: UUID
    type: str  # "order.created.v1"
    version: str
    occurred_at: datetime
    correlation_id: UUID
    causation_id: UUID | None
    aggregate_id: UUID
    traceparent: str | None
    payload: dict
```

## Mensageria

### RabbitMQ

- Versão 4.x com quorum queues
- Exchanges topic
- DLX (Dead Letter Exchange) para cada fila
- Fan-out no relay: 1 task Celery por consumidor

### Celery

- Broker: RabbitMQ
- Backend: Redis
- Queue type: quorum
- acks_late: True
- prefetch: 1
- Retry com backoff exponencial + jitter
- Native delayed delivery para ETA

## Idempotência

### API

Header `Idempotency-Key` + hash do corpo:
- Mesma chave + mesmo corpo = resposta cacheada
- Mesma chave + corpo diferente = 422
- Constraint UNIQUE(key, body_hash) no banco

### Consumidores

Tabela `Inbox` com UNIQUE(consumer, message_id):
- Gravada na mesma transação do efeito
- Violação de UNIQUE = ignorar (já processado)

## Retry e DLQ

- Retry apenas para erros transitórios (ConnectionError, Timeout)
- Erros de negócio não fazem retry (ex.: PaymentDeclined)
- Esgotado de retry → grava DeadLetter no banco → rejeita sem requeue → DLX → fila <consumidor>.dlq
- Replay via comando, endpoint staff ou botão na UI

## Observabilidade

### Logs

- structlog com formato JSON
- correlation_id em todos os logs
- Stdout para coleta pelo Docker

### Tracing

- OpenTelemetry (Django, Celery, psycopg, Redis)
- Exporter OTLP para Jaeger
- traceparent propagado via outbox

### Métricas

- Prometheus + django-prometheus
- rabbitmq_prometheus plugin
- Métricas de negócio calculadas no scrape (evita multiprocess)
- Dashboards provisionados em código no Grafana

## Segurança

- Segredos via environment variables (.env)
- DEBUG desligado por padrão
- Throttling via DRF + Redis
- JWT na API
- Login por sessão (staff) no dashboard
- Nunca expor credenciais em código ou logs
