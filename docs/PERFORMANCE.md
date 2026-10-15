# Performance Tuning - Orquestra

Guia de otimização de performance para ambientes de produção.

## 🎯 Objetivos de Performance

### SLAs Sugeridos

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| Latência API (P50) | < 200ms | > 500ms |
| Latência API (P95) | < 500ms | > 2s |
| Latência API (P99) | < 1s | > 5s |
| Throughput API | > 100 req/s | < 50 req/s |
| Worker throughput | > 50 msg/min | < 20 msg/min |
| DB query time (P95) | < 100ms | > 500ms |
| RabbitMQ latency | < 50ms | > 200ms |
| Cache hit rate | > 80% | < 50% |

## 🗄️ PostgreSQL Tuning

### Configuração Básica

```yaml
# docker-compose.yml - db service
environment:
  POSTGRES_SHARED_BUFFERS: 256MB       # 25% da RAM
  POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB  # 50-75% da RAM
  POSTGRES_MAINTENANCE_WORK_MEM: 64MB
  POSTGRES_CHECKPOINT_COMPLETION_TARGET: 0.9
  POSTGRES_WAL_BUFFERS: 16MB
  POSTGRES_DEFAULT_STATISTICS_TARGET: 100
  POSTGRES_RANDOM_PAGE_COST: 1.1       # SSD
  POSTGRES_EFFECTIVE_IO_CONCURRENCY: 200
  POSTGRES_WORK_MEM: 16MB
  POSTGRES_MIN_WAL_SIZE: 1GB
  POSTGRES_MAX_WAL_SIZE: 4GB
```

### Índices

Índices já criados pelo projeto:

```sql
-- Ordem (frequente)
CREATE INDEX idx_orders_status ON orders_order(status);
CREATE INDEX idx_orders_created_at ON orders_order(created_at);
CREATE INDEX idx_orders_customer_id ON orders_order(customer_id);

-- Outbox (frequente)
CREATE INDEX idx_outbox_status ON outbox_outboxmessage(status);
CREATE INDEX idx_outbox_created_at ON outbox_outboxmessage(created_at);

-- Dead Letter (frequente)
CREATE INDEX idx_deadletter_status ON outbox_deadlettermessage(status);
CREATE INDEX idx_deadletter_created_at ON outbox_deadlettermessage(created_at);

-- Inbox (idempotência)
CREATE INDEX idx_inbox_consumer_message ON inbox_inboxmessage(consumer, message_id);
```

Índices adicionais recomendados para alta carga:

```sql
-- Composto para queries comuns
CREATE INDEX idx_orders_status_created ON orders_order(status, created_at DESC);

-- Partial index para mensagens pendentes
CREATE INDEX idx_outbox_pending ON outbox_outboxmessage(created_at)
WHERE status = 'PENDING';

-- Covering index para evitar table scan
CREATE INDEX idx_orders_covering ON orders_order(status, created_at, customer_id, total_amount);
```

### Pool de Conexões

```python
# config/settings/production.py
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,  # Reutiliza conexões por 10 min
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # Timeout de 30s
        },
    },
}
```

### Queries N+1

Usar `select_related` e `prefetch_related`:

```python
# ❌ Ruim (N+1)
orders = Order.objects.all()
for order in orders:
    print(order.customer.name)  # Query por ordem

# ✅ Bom (1 query)
orders = Order.objects.select_related('customer').all()
for order in orders:
    print(order.customer.name)

# ✅ Bom para many-to-many
orders = Order.objects.prefetch_related('items').all()
```

### Vacuum e Autovacuum

```yaml
# docker-compose.yml
environment:
  POSTGRES_AUTOVACUUM: 'on'
  POSTGRES_AUTOVACUUM_MAX_WORKERS: 3
  POSTGRES_AUTOVACACUUM_NAPTIME: 1s
```

## 🚀 Django Tuning

### Middleware e Settings

```python
# config/settings/production.py

# Remover middleware de debug
DEBUG = False

# Logging eficiente
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
            },
        },
    },
}

# Session via Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### DRF Optimization

```python
# config/settings/production.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',
        'user': '5000/hour',
    },
}
```

### Use defer/only

```python
# ❌ Carrega todos os campos
orders = Order.objects.all()

# ✅ Carrega apenas campos necessários
orders = Order.objects.only('id', 'status', 'total_amount').all()

# ✅ Adia carregamento de campos pesados
orders = Order.objects.defer('metadata', 'notes').all()
```

## 🐰 RabbitMQ Tuning

### Configuração de Filas

```yaml
# docker-compose.yml - rabbitmq service
environment:
  RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS: -rabbit log_levels [{connection,error},{default,warning}]
  RABBITMQ_VM_MEMORY_HIGH_WATERMARK: 0.6  # 60% da RAM
  RABBITMQ_DISK_FREE_LIMIT: 2GB
```

### Quorum Queues

Já configurado no projeto, mas ajustes possíveis:

```python
# config/celery.py
task_queues = [
    Queue(
        'orquestra.inventory',
        routing_key='orquestra.inventory',
        queue_arguments={
            'x-queue-type': 'quorum',
            'x-delivery-limit': 5,  # Máximo de redeliveries
            'x-quorum-initial-group-size': 3,
        },
    ),
]
```

### Prefetch e Concurrency

```python
# config/celery.py
worker_prefetch_multiplier = 1  # Reduz buffer, melhor latência
worker_concurrency = 4  # CPUs disponíveis
```

### Flow Control

```yaml
# docker-compose.yml
environment:
  RABBITMQ_FLOW_ACTIVE: 'true'
  RABBITMQ_FLOW_ACTIVE_TIMEOUT: 10000
```

## 🧠 Redis Tuning

### Configuração

```yaml
# docker-compose.yml - redis service
command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### Cache Strategy

```python
# Cache de leitura
from django.core.cache import cache

def get_product(product_id: UUID) -> Product:
    cache_key = f"product:{product_id}"
    product = cache.get(cache_key)
    if product is None:
        product = Product.objects.get(id=product_id)
        cache.set(cache_key, product, timeout=3600)  # 1 hora
    return product

# Cache de computação
def calculate_discount(order: Order) -> Decimal:
    cache_key = f"discount:{order.id}"
    discount = cache.get(cache_key)
    if discount is None:
        discount = complex_calculation(order)
        cache.set(cache_key, discount, timeout=300)  # 5 min
    return discount
```

### Cache Locks

```python
from django.core.cache import cache

def reserve_stock(product_id: UUID, quantity: int) -> bool:
    lock_key = f"lock:stock:{product_id}"
    # Tenta adquirir lock por 10s
    lock_acquired = cache.add(lock_key, "1", timeout=10)
    if not lock_acquired:
        return False  # Já em processamento

    try:
        # ... lógica de reserva ...
        return True
    finally:
        cache.delete(lock_key)
```

## ⚡ Celery Tuning

### Task Configuration

```python
# config/celery.py
task_acks_late = True  # Ack apenas após sucesso
task_reject_on_worker_lost = True
task_default_rate_limit = '100/m'  # Throttle global
task_time_limit = 300  # 5 min timeout
task_soft_time_limit = 280  # 4m40s soft timeout
```

### Retry com Backoff

```python
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def process_payment(self, order_id: UUID) -> None:
    try:
        # ... lógica ...
    except Exception as exc:
        logger.error(f"Payment failed: {exc}")
        raise self.retry(exc=exc)
```

### Beat Scheduling

```python
# config/celery.py
beat_schedule = {
    'watchdog-orders': {
        'task': 'orchestrator.tasks.watchdog.check_stuck_orders',
        'schedule': 60.0,  # A cada 1 min
    },
    'cleanup-outbox': {
        'task': 'outbox.tasks.cleanup_old_messages',
        'schedule': 3600.0,  # A cada 1 hora
    },
}
```

## 🌐 API Tuning

### Gunicorn

```bash
# Comando de produção
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class gthread \
  --threads 8 \
  --worker-connections 1000 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --timeout 30 \
  --keepalive 5 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

Regra de thumb para workers:
- CPU-bound: `(2 * CPUs) + 1`
- I/O-bound: `CPUs * 4`
- Django (mix): `CPUs * 2`

### Compression

```python
# config/settings/production.py
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # Compressão GZIP
    # ... outros middlewares ...
]
```

### Static Files

```python
# config/settings/production.py
STATIC_ROOT = '/var/www/static'
STATIC_URL = '/static/'

# Whitenoise para servir estáticos
MIDDLEWARE.insert(0, 'whitenoise.middleware.WhiteNoiseMiddleware')
```

## 📊 Monitoring Performance

### Prometheus Queries

```promql
# Latência P95
histogram_quantile(0.95, rate(django_http_requests_latency_seconds_bucket[5m]))

# Throughput
rate(django_http_requests_total[5m])

# Error rate
rate(django_http_requests_total{status=~"5.."}[5m]) / rate(django_http_requests_total[5m])

# DB query time
rate(django_db_query_total[5m])
histogram_quantile(0.95, rate(django_db_query_duration_seconds_bucket[5m]))

# Celery task rate
rate(celery_task_received_total[5m])

# RabbitMQ queue depth
rabbitmq_queue_messages{queue="orquestra.inventory"}
```

### Alerts

```yaml
# deploy/prometheus/alerts.yml
groups:
  - name: orquestra_performance
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(django_http_requests_latency_seconds_bucket[5m])) > 2
        for: 5m
        annotations:
          summary: "API latency P95 > 2s"

      - alert: HighErrorRate
        expr: rate(django_http_requests_total{status=~"5.."}[5m]) / rate(django_http_requests_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "Error rate > 5%"

      - alert: DBSlowQueries
        expr: histogram_quantile(0.95, rate(django_db_query_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        annotations:
          summary: "DB queries P95 > 500ms"

      - alert: RabbitMQQueueDepth
        expr: rabbitmq_queue_messages{queue=~"orquestra.*"} > 1000
        for: 5m
        annotations:
          summary: "Queue depth > 1000"
```

## 🔧 Load Testing

### Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class OrderUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def create_order(self):
        self.client.post(
            '/api/v1/orders/',
            json={
                'customer_id': str(uuid4()),
                'items': [
                    {'product_sku': 'PROD-001', 'quantity': 2},
                ],
            },
            headers={'Idempotency-Key': str(uuid4())},
        )

    @task(3)
    def list_orders(self):
        self.client.get('/api/v1/orders/')
```

```bash
# Rodar load test
uv add locust
uv run locust -f locustfile.py --host http://localhost:8000 --users 100 --spawn-rate 10
```

### K6

```javascript
// loadtest.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 50 },
    { duration: '5m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 0 },
  ],
};

export default function () {
  const res = http.post('http://localhost:8000/api/v1/orders/', JSON.stringify({
    customer_id: crypto.randomUUID(),
    items: [{ product_sku: 'PROD-001', quantity: 2 }],
  }), {
    headers: { 'Content-Type': 'application/json', 'Idempotency-Key': crypto.randomUUID() },
  });

  check(res, { 'status is 201': (r) => r.status === 201 });
  sleep(1);
}
```

```bash
# Rodar
k6 run loadtest.js
```

## 🎯 Checklist de Performance

### Pré-Produção

- [ ] Índices criados e analisados (EXPLAIN ANALYZE)
- [ ] N+1 queries eliminados
- [ ] Cache strategy definida
- [ ] Connection pool configurado
- [ ] Throttling ativo
- [ ] Compression habilitada
- [ ] Static files otimizados
- [ ] Load test executado
- [ ] Baseline de métricas coletado

### Pós-Deploy

- [ ] Monitorar latência P50/P95/P99
- [ ] Monitorar error rate
- [ ] Monitorar throughput
- [ ] Monitorar DB query time
- [ ] Monitorar RabbitMQ queue depth
- [ ] Monitorar cache hit rate
- [ ] Ajustar thresholds baseado em dados reais

## 📚 Referências

- [Django Performance](https://docs.djangoproject.com/en/stable/topics/performance/)
- [PostgreSQL Performance](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [RabbitMQ Best Practices](https://www.rabbitmq.com/best-practices.html)
- [Celery Best Practices](https://docs.celeryq.dev/en/stable/userguide/optimizing.html)
- [Redis Performance](https://redis.io/docs/manual/patterns/)
