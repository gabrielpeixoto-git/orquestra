# Runbook - Orquestra

Guia de operação e troubleshooting para a plataforma Orquestra.

## 🚀 Inicialização

### Ambiente Local

```bash
# Subir infraestrutura básica (API, relay, worker, beat, db, redis, rabbitmq)
uv run poe up

# Subir com observabilidade (inclui Jaeger, Prometheus, Grafana)
uv run poe up-obs

# Verificar health checks
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/detailed
```

### Dashboard

Acesse o Control Center em http://localhost:8000/

## 📊 Observabilidade

### Jaeger (Distributed Tracing)

- **URL**: http://localhost:16686
- **Uso**: Visualizar traces distribuídos API → outbox → relay → workers
- **Como verificar**:
  1. Acesse o endpoint `/api/v1/orders/` via POST
  2. No Jaeger, selecione o serviço "orquestra"
  3. Clique em "Find Traces"
  4. Verifique o trace completo da requisição

### Prometheus (Metrics)

- **URL**: http://localhost:9090
- **Uso**: Consultar métricas de negócio e sistema
- **Queries úteis**:
  ```promql
  # Taxa de requisições HTTP
  rate(django_http_requests_total[5m])

  # Latência média
  rate(django_http_requests_latency_seconds_sum[5m]) / rate(django_http_requests_latency_seconds_count[5m])

  # Pedidos por status
  django_model_inserts_total{model="order"}
  ```

### Grafana (Dashboards)

- **URL**: http://localhost:3000
- **Credenciais**: admin/admin
- **Dashboards provisionados**: Orquestra Dashboard
- **Acesso**: Menu → Dashboards → Orquestra

## 🔧 Operações Comuns

### Rodar Migrations

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
```

### Rodar Relay (Manual)

```bash
uv run python manage.py relay
```

### Replay Dead Letters

```bash
# Via management command
uv run python manage.py replay_dlq

# Via API
curl -X POST http://localhost:8000/api/v1/staff/dead-letters/<id>/replay/
curl -X POST http://localhost:8000/api/v1/staff/dead-letters/<id>/discard/
```

### Seed Demo Data

```bash
uv run python manage.py seed_demo
```

### Smoke Tests

```bash
# Todos os cenários
uv run poe smoke

# Cenário específico
uv run python manage.py smoke --scenario success
uv run python manage.py smoke --scenario insufficient_stock
uv run python manage.py smoke --scenario payment_failed
uv run python manage.py smoke --scenario payment_timeout
uv run python manage.py smoke --scenario payment_error
```

## 🐛 Troubleshooting

### Workers não processando mensagens

**Sintoma**: Mensagens acumulando nas filas do RabbitMQ

**Diagnóstico**:
```bash
# Verificar filas do RabbitMQ
curl -u guest:guest http://localhost:15672/api/queues

# Verificar logs do worker
docker logs orquestra-worker
```

**Solução**:
1. Verifique se o worker está rodando: `docker ps`
2. Reinicie o worker: `docker compose restart worker`
3. Verifique se RabbitMQ está acessível: `docker logs orquestra-rabbitmq`

### Relay não publicando mensagens

**Sintoma**: Outbox cresce mas mensagens não chegam no RabbitMQ

**Diagnóstico**:
```bash
# Verificar outbox messages pendentes
uv run python manage.py shell
>>> from apps.outbox.models import OutboxMessage
>>> OutboxMessage.objects.filter(status='PENDING').count()
```

**Solução**:
1. Verifique logs do relay: `docker logs orquestra-relay`
2. Verifique conexão com RabbitMQ
3. Rode relay manualmente: `uv run python manage.py relay`

### Dead Letters acumulando

**Sintoma**: Muitas mensagens em DLQ

**Diagnóstico**:
```bash
# Via Dashboard: http://localhost:8000/dead-letters/
# Via API
curl http://localhost:8000/api/v1/staff/dead-letters/
```

**Solução**:
1. Analise o erro na dead letter
2. Corrija a causa raiz (ex: fix no handler)
3. Replay mensagens via Dashboard ou API
4. Descarte mensagens irrecuperáveis

### Pedidos travados em PENDING

**Sintoma**: Pedidos ficam em PENDING por muito tempo

**Diagnóstico**:
```bash
# Verificar pedidos antigos
uv run python manage.py shell
>>> from apps.orders.models import Order
>>> from django.utils import timezone
>>> from datetime import timedelta
>>> old_orders = Order.objects.filter(status='PENDING', created_at__lt=timezone.now() - timedelta(minutes=30))
>>> old_orders.count()
```

**Solução**:
1. O watchdog deveria detectar e cancelar automaticamente
2. Verifique se o beat está rodando: `docker logs orquestra-beat`
3. Se necessário, cancele manualmente via API
4. Verifique logs para entender por que a saga não progrediu

### Performance Issues

**Sintoma**: Latência alta ou timeouts

**Diagnóstico**:
1. Verifique métricas no Prometheus
2. Verifique traces no Jaeger
3. Verifique logs JSON com correlation_id

**Solução**:
1. Identifique o bottleneck (DB, Redis, RabbitMQ, ou código)
2. Verifique N+1 queries nos logs do Django
3. Ajuste configurações de cache/broker se necessário

## 📈 Monitoramento

### KPIs Chave

- **Taxa de sucesso de pedidos**: > 95%
- **Latência média de criação de pedido**: < 500ms
- **Dead letters acumuladas**: < 10
- **Pedidos travados > 30min**: 0
- **Uso de CPU/Docker**: < 80%

### Alertas Sugeridos

Configure alertas no Prometheus/Grafana para:
- Taxa de erros HTTP > 5%
- Dead letters > 20
- Latência P95 > 2s
- Workers parados por > 5min

## 🔐 Segurança

### Em Produção

1. Alterar SECRET_KEY
2. Alterar senhas de DB, Redis, RabbitMQ
3. Habilitar HTTPS
4. Configurar rate limiting adequado
5. Restringir acesso ao Dashboard (autenticação)
6. Restringir acesso ao Prometheus/Grafana/Jaeger

### Logs e Traces

- Logs contêm correlation_id para rastreamento
- Traces sensíveis devem ser omitidos (ex: dados de pagamento)
- Configure retenção de logs/traces conforme compliance

## 📝 Manutenção

### Backup

- Backup do PostgreSQL: `docker exec orquestra-db pg_dump -U orquestra orquestra > backup.sql`
- Backup de configurações: versionar docker-compose.yml e .env

### Limpeza

```bash
# Limpar dead letters antigas (replayed/discarded)
uv run python manage.py shell
>>> from apps.outbox.models import DeadLetterMessage
>>> from datetime import timedelta
>>> from django.utils import timezone
>>> DeadLetterMessage.objects.filter(
...     status__in=['REPLAYED', 'DISCARDED'],
...     created_at__lt=timezone.now() - timedelta(days=7)
... ).delete()
```

### Atualização

1. Backup do banco
2. Parar containers: `uv run poe down`
3. Atualizar código
4. Rodar migrations: `uv run python manage.py migrate`
5. Subir containers: `uv run poe up`
6. Verificar health checks
7. Rodar smoke tests
