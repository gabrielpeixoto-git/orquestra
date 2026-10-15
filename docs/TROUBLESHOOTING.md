# Troubleshooting Avançado - Orquestra

Guia avançado de diagnóstico e resolução de problemas complexos em produção.

## 🔍 Diagnóstico Rápido

### Checklist Inicial

Antes de investigar problemas complexos, verifique o básico:

```bash
# 1. Verificar health checks
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/detailed

# 2. Verificar containers
docker ps
docker logs orquestra-api --tail 100
docker logs orquestra-worker --tail 100
docker logs orquestra-relay --tail 100

# 3. Verificar RabbitMQ
curl -u guest:guest http://localhost:15672/api/queues
curl -u guest:guest http://localhost:15672/api/connections

# 4. Verificar PostgreSQL
docker exec orquestra-db pg_isready -U orquestra
docker exec orquestra-db psql -U orquestra -c "SELECT COUNT(*) FROM orders_order;"
```

## 🚨 Problemas Complexos

### 0. Celery Workers Não Funcionando

**Sintoma**: Workers Celery não processam mensagens, erros de routing key ou problemas de configuração.

**Solução Alternativa**: Consumidor RabbitMQ Direto

Se Celery estiver com problemas de routing key ou configuração, use o consumidor alternativo que chama handlers diretamente:

```bash
# Iniciar todos os consumidores (inventory, payments, notifications, orchestrator, audit)
uv run python scripts/run_all_consumers.py

# Ou iniciar consumidor individual
uv run python scripts/consumer.py inventory
uv run python scripts/consumer.py payments
uv run python scripts/consumer.py notifications
uv run python scripts/consumer.py orchestrator
uv run python scripts/consumer.py audit
```

O consumidor alternativo (`scripts/consumer.py`):
- Mapeia filas para handlers por tipo de mensagem
- Chama handlers Celery diretamente (funções Python)
- Suporta múltiplos handlers por tipo de mensagem (ex: PaymentProcessed → notifications + orchestrator + audit)
- Fix encoding no Windows (UTF-8)
- Usa idempotência via InboxMessage

**Nota**: Este é um workaround temporário. Para produção, investigue e corrija a configuração do Celery.

### 1. Saga Travada (Deadlock Lógico)

**Sintoma**: Pedidos ficam em estado intermediário por muito tempo (ex: STOCK_RESERVED mas não avança).

**Diagnóstico**:

```bash
# Verificar pedidos travados
uv run python manage.py shell
>>> from apps.orders.models import Order
>>> from django.utils import timezone
>>> from datetime import timedelta
>>> stuck_orders = Order.objects.filter(
...     status__in=['STOCK_RESERVED', 'PAYMENT_PENDING'],
...     updated_at__lt=timezone.now() - timedelta(minutes=30)
... )
>>> stuck_orders.count()

# Verificar se há mensagens não-processadas no outbox
>>> from apps.outbox.models import OutboxMessage
>>> OutboxMessage.objects.filter(status='PENDING').count()

# Verificar se há dead letters
>>> from apps.outbox.models import DeadLetterMessage
>>> DeadLetterMessage.objects.filter(status='PENDING').count()
```

**Causas Possíveis**:

1. **Worker parado**: Worker não está processando mensagens
2. **Relay parado**: Outbox não está publicando no RabbitMQ
3. **Erro silencioso**: Handler está falhando sem logar erro
4. **RabbitMQ desconectado**: Conexão com broker intermitente

**Solução**:

```bash
# 1. Reiniciar workers
docker compose restart worker beat

# 2. Forçar relay manual
uv run python manage.py relay --max-iterations 100

# 3. Verificar logs específicos
docker logs orquestra-worker | grep -i error
docker logs orquestra-relay | grep -i error

# 4. Se necessário, compensar manualmente (último recurso)
uv run python manage.py shell
>>> from apps.orders.services import cancel_order
>>> for order in stuck_orders:
...     cancel_order(order.id, reason="manual_compensation")
```

### 2. Memory Leak em Workers

**Sintoma**: Workers consomem cada vez mais memória até OOM.

**Diagnóstico**:

```bash
# Verificar uso de memória
docker stats orquestra-worker

# Verificar leaks com tracemalloc (em dev)
uv run python -c "
import tracemalloc
tracemalloc.start()
# ... código ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
"
```

**Causas Comuns**:

1. **Celery task sem cleanup**: Variáveis globais ou caches não limpos
2. **ORM queries sem select_related/prefetch_related**: N+1 carregando objetos na memória
3. **Conexões não fechadas**: Conexões DB/RabbitMQ acumulando

**Solução**:

```python
# Adicionar no worker config (config/celery.py)
worker_max_tasks_per_child = 100  # Recicla worker após N tarefas
worker_prefetch_multiplier = 1    # Reduz buffer de mensagens
```

```bash
# Reiniciar workers periodicamente (via cron/k8s)
docker compose restart worker
```

### 3. Race Condition em Estoque

**Sintoma**: Overselling (venda acima do estoque disponível) ou reservas duplicadas.

**Diagnóstico**:

```bash
# Verificar inconsistências no estoque
uv run python manage.py shell
>>> from apps.inventory.models import Product, StockReservation
>>> product = Product.objects.get(sku="PROD-001")
>>> reserved = StockReservation.objects.filter(
...     product=product,
...     status='ACTIVE'
... ).aggregate(total=models.Sum('quantity'))['total'] or 0
>>> print(f"Stock: {product.stock}, Reserved: {reserved}, Available: {product.stock - reserved}")
```

**Causas Comuns**:

1. **Sem locking no banco**: Reservas feitas sem SELECT FOR UPDATE
2. **Timing window**: Verificação e reserva não atômicas
3. **Idempotência quebrada**: Replay duplicando reservas

**Solução**:

```python
# Garantir uso de database lock (já implementado em services.py)
from django.db import transaction

@transaction.atomic
def reserve_stock(product_id: UUID, quantity: int, order_id: UUID) -> StockReservation:
    product = Product.objects.select_for_update().get(id=product_id)
    # ... validação e reserva ...
```

### 4. Outbox Crescendo Infinitamente

**Sintoma**: Tabela outbox_message cresce sem parar, relay não consegue acompanhar.

**Diagnóstico**:

```bash
# Verificar tamanho da tabela
docker exec orquestra-db psql -U orquestra -c "
SELECT COUNT(*), status FROM outbox_outboxmessage GROUP BY status;
"

# Verificar idade das mensagens pendentes
docker exec orquestra-db psql -U orquestra -c "
SELECT created_at, COUNT(*) FROM outbox_outboxmessage
WHERE status='PENDING'
GROUP BY created_at
ORDER BY created_at;
"
```

**Causas Comuns**:

1. **Relay muito lento**: Throttling ou RabbitMQ lento
2. **Flood de mensagens**: Loop criando mensagens infinitamente
3. **Erro de publicação**: RabbitMQ rejeitando mensagens mas relay não aborta

**Solução**:

```bash
# 1. Escalar relay
docker compose up -d --scale relay=3

# 2. Limpar mensagens antigas (cuidado!)
uv run python manage.py shell
>>> from apps.outbox.models import OutboxMessage
>>> from datetime import timedelta
>>> from django.utils import timezone
>>> old_messages = OutboxMessage.objects.filter(
...     status='PUBLISHED',
...     published_at__lt=timezone.now() - timedelta(days=7)
... )
>>> old_messages.delete()

# 3. Se houver flood, parar API e investigar causa
docker compose stop api
```

### 5. RabbitMQ Memory Alarm

**Sintoma**: RabbitMQ para de aceitar mensagens, logs mostram "memory alarm triggered".

**Diagnóstico**:

```bash
# Verificar status do RabbitMQ
curl -u guest:guest http://localhost:15672/api/alerm/memory

# Verificar filas acumuladas
curl -u guest:guest http://localhost:15672/api/queues | jq '.[] | select(.messages > 1000)'
```

**Causas Comuns**:

1. **DLQ não limpa**: Dead letters acumulando
2. **Consumidores parados**: Mensagens não sendo processadas
3. **Mensagens muito grandes**: Payload gigante nas filas

**Solução**:

```bash
# 1. Limpar DLQ (após analisar erros)
uv run python manage.py shell
>>> from apps.outbox.models import DeadLetterMessage
>>> DeadLetterMessage.objects.filter(
...     status__in=['REPLAYED', 'DISCARDED'],
...     created_at__lt=timezone.now() - timedelta(days=1)
... ).delete()

# 2. Purge filas críticas (último recurso)
rabbitmqadmin purge queue name=orquestra.dlq

# 3. Aumentar limite de memória do RabbitMQ
# Editar docker-compose.yml:
# RABBITMQ_VM_MEMORY_HIGH_WATERMARK: 0.8
```

### 6. Conexão com DB Intermitente

**Sintoma**: Erros de conexão com PostgreSQL em logs, timeouts aleatórios.

**Diagnóstico**:

```bash
# Verificar conexões ativas
docker exec orquestra-db psql -U orquestra -c "
SELECT count(*) FROM pg_stat_activity;
"

# Verificar conexões em idle
docker exec orquestra-db psql -U orquestra -c "
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;
"
```

**Causas Comuns**:

1. **Pool de conexões muito grande**: Muitas conexões abertas
2. **Connection leaks**: Conexões não fechadas
3. **DB sobrecarregado**: Queries lentas bloqueando conexões

**Solução**:

```python
# Ajustar pool de conexões (config/settings/base.py)
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,  # Reutiliza conexões
        'OPTIONS': {
            'connect_timeout': 10,
        },
    },
}
```

```bash
# Matar conexões idle (tempo real)
docker exec orquestra-db psql -U orquestra -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < now() - interval '10 minutes';
"
```

## 📊 Diagnóstico com Observabilidade

### Jaeger - Tracing Distribuído

```bash
# Acessar: http://localhost:16686

# Buscar traces por serviço
- orquestra-api: Requisições HTTP
- orquestra-worker: Tasks Celery
- orquestra-relay: Publicação de mensagens

# Analisar:
- Spans com erro (vermelho)
- Latência alta (> 1s)
- Spans faltando (gap no trace)
```

### Prometheus - Métricas

```bash
# Acessar: http://localhost:9090

# Queries úteis:
# Taxa de erros HTTP
rate(django_http_requests_total{status=~"5.."}[5m])

# Latência P95
histogram_quantile(0.95, rate(django_http_requests_latency_seconds_bucket[5m]))

# Mensagens em DLQ
rabbitmq_queue_messages{queue=~".*\\.dlq"}

# Conexões DB ativas
pg_stat_activity_count{state="active"}
```

### Grafana - Dashboards

```bash
# Acessar: http://localhost:3000 (admin/admin)

# Dashboards disponíveis:
- Orquestra Dashboard: Visão geral
- RabbitMQ Dashboard: Status do broker
- PostgreSQL Dashboard: Performance do DB
```

## 🔧 Ferramentas de Diagnóstico

### Django Debug Toolbar (Dev)

```python
# Adicionar em INSTALLED_APPS (settings/dev.py)
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

### Django Shell Plus

```bash
uv add django-extensions
uv run python manage.py shell_plus
```

### PostgreSQL EXPLAIN

```bash
uv run python manage.py shell
>>> from django.db import connection
>>> from apps.orders.models import Order
>>> query = Order.objects.all().query
>>> cursor = connection.cursor()
>>> cursor.execute("EXPLAIN ANALYZE " + str(query))
>>> print(cursor.fetchall())
```

### RabbitMQ Management Plugin

```bash
# Acessar: http://localhost:15672 (guest/guest)

# Recursos:
- Queues: Ver filas e mensagens
- Connections: Ver conexões ativas
- Channels: Ver canais e consumers
- Admin: Gerenciar usuários e permissões
```

## 🆘 Quando Escalar

Se o problema não pode ser resolvido com os passos acima:

1. **Coletar evidências**:
   - Logs de todos os containers
   - Métricas do Prometheus
   - Traces do Jaeger
   - Dump do banco (se seguro)

2. **Isolar o problema**:
   - Parar API (se estiver causando flood)
   - Parar workers (se estiverem processando incorretamente)
   - Manter infraestrutura crítica (DB, RabbitMQ)

3. **Comunicar**:
   - Documentar o incidente
   - Compartilhar evidências
   - Propor rollback ou hotfix

4. **Post-mortem**:
   - CRIAR ADR com a decisão
   - Atualizar RUNBOOK com aprendizados
   - Adicionar alertas para detectar precocemente

## 📚 Referências

- [Django Troubleshooting](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Celery Troubleshooting](https://docs.celeryq.dev/en/stable/userguide/troubleshooting.html)
- [RabbitMQ Troubleshooting](https://www.rabbitmq.com/troubleshooting.html)
- [PostgreSQL Performance](https://wiki.postgresql.org/wiki/Performance_Optimization)
