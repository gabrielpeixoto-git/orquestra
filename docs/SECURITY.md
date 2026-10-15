# Segurança em Produção - Orquestra

Guia de hardening de segurança para ambientes de produção.

## 🔐 Checklist de Segurança

### Pré-Produção

- [ ] Todas as senhas alteradas dos defaults
- [ ] SECRET_KEY gerado aleatoriamente e armazenado em secret manager
- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS configurado corretamente
- [ ] HTTPS habilitado com certificado válido
- [ ] Rate limiting configurado
- [ ] Autenticação JWT habilitada
- [ ] CORS configurado restritivamente
- [ ] Headers de segurança configurados
- [ ] Logs não contêm dados sensíveis
- [ ] Backup de dados configurado
- [ ] Monitoramento de segurança ativo

## 🔑 Gestão de Secrets

### Nunca Hardcode Secrets

```python
# ❌ RUIM
SECRET_KEY = 'django-insecure-...'
DB_PASSWORD = 'password123'

# ✅ BOM
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    db_password: str

    class Config:
        env_file = '.env'
```

### Secret Managers

Produção deve usar secret managers:

**HashiCorp Vault**:
```bash
# Instalar Vault
vault login

# Armazenar secret
vault kv put secret/orquestra/production \
  secret_key=$(openssl rand -base64 64) \
  db_password=$(openssl rand -base64 32)

# Recuperar
vault kv get -field=secret_key secret/orquestra/production
```

**AWS Secrets Manager**:
```bash
# Armazenar
aws secretsmanager create-secret \
  --name orquestra/production \
  --secret-string '{"secret_key":"...","db_password":"..."}'

# Recuperar
aws secretsmanager get-secret-value \
  --secret-id orquestra/production
```

**Kubernetes Secrets**:
```yaml
# deploy/k8s/base/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: orquestra-secret
type: Opaque
stringData:
  secret-key: "<base64-encoded>"
  db-password: "<base64-encoded>"
```

### Rotation de Secrets

```bash
# PostgreSQL - rotation
docker exec orquestra-db psql -U postgres -c "
ALTER USER orquestra WITH PASSWORD 'new-strong-password';
"

# RabbitMQ - rotation
rabbitmqctl change_password guest new-strong-password

# Redis - rotation (usando ACL)
docker exec orquestra-redis redis-cli CONFIG SET requirepass new-strong-password
```

## 🌐 HTTPS e TLS

### Certbot (Let's Encrypt)

```bash
# Instalar certbot
apt-get install certbot python3-certbot-nginx

# Gerar certificado
certbot --nginx -d api.orquestra.com

# Auto-renewal (já configurado)
certbot renew --dry-run
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/orquestra
server {
    listen 443 ssl http2;
    server_name api.orquestra.com;

    ssl_certificate /etc/letsencrypt/live/api.orquestra.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.orquestra.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Django Settings

```python
# config/settings/production.py
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

## 🛡️ Headers de Segurança

### Django Middleware

```python
# config/settings/production.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # ... outros middlewares ...
]

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### Custom Headers

```python
# config/settings/production.py
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
CSP_DEFAULT_DIRECTIVES = {
    'default-src': ["'self'"],
    'script-src': ["'self'", 'cdn.jsdelivr.net'],
    'style-src': ["'self'", 'cdn.jsdelivr.net'],
    'img-src': ["'self'", 'data:'],
}
```

## 🔒 Autenticação e Autorização

### JWT Best Practices

```python
# config/settings/production.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

### Rate Limiting

```python
# config/settings/production.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'orders_create': '10/minute',
    },
}
```

### Per-endpoint Throttling

```python
# apps/orders/views.py
from rest_framework.throttling import UserRateThrottle

class CreateOrderThrottle(UserRateThrottle):
    rate = '10/minute'

class OrderCreateView(generics.CreateAPIView):
    throttle_classes = [CreateOrderThrottle]
    # ...
```

## 🌐 CORS

### Configuração Restritiva

```python
# config/settings/production.py
CORS_ALLOWED_ORIGINS = [
    'https://orquestra.com',
    'https://www.orquestra.com',
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'idempotency-key',
]
```

## 🔐 Database Security

### PostgreSQL Hardening

```yaml
# docker-compose.yml
environment:
  POSTGRES_HOST_AUTH_METHOD: scram-sha-256
  POSTGRES_INITDB_ARGS: '--auth-host=scram-sha-256 --auth-local=scram-sha-256'
```

### Network Isolation

```yaml
# docker-compose.yml
services:
  db:
    networks:
      - backend
    # Sem exposição externa

  api:
    networks:
      - backend
      - frontend

networks:
  backend:
    internal: true  # Isolado da internet
  frontend:
```

### Row-Level Security (RLS)

```sql
-- Exemplo: RLS para orders
ALTER TABLE orders_order ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_can_see_own_orders ON orders_order
    FOR SELECT
    USING (customer_id = current_user_id());
```

## 🐰 RabbitMQ Security

### Disable Guest User

```yaml
# docker-compose.yml
environment:
  RABBITMQ_DEFAULT_USER: orquestra
  RABBITMQ_DEFAULT_PASS: <strong-password>
  RABBITMQ_DEFAULT_VHOST: /
```

### TLS/SSL

```yaml
# docker-compose.yml
volumes:
  - ./deploy/rabbitmq/certs:/etc/rabbitmq/ssl

environment:
  RABBITMQ_SSL_CERT_FILE: /etc/rabbitmq/ssl/server.crt
  RABBITMQ_SSL_KEY_FILE: /etc/rabbitmq/ssl/server.key
  RABBITMQ_SSL_CA_FILE: /etc/rabbitmq/ssl/ca.crt
  RABBITMQ_SSL_VERIFY: verify_peer
  RABBITMQ_SSL_FAIL_IF_NO_PEER_CERT: true
```

### Management Plugin

```yaml
# docker-compose.yml
environment:
  RABBITMQ_MANAGEMENT_SSL: 'true'
  RABBITMQ_MANAGEMENT_SSL_CACERTFILE: /etc/rabbitmq/ssl/ca.crt
  RABBITMQ_MANAGEMENT_SSL_CERTFILE: /etc/rabbitmq/ssl/server.crt
  RABBITMQ_MANAGEMENT_SSL_KEYFILE: /etc/rabbitmq/ssl/server.key
```

## 🔐 Redis Security

### Require Auth

```yaml
# docker-compose.yml
command: redis-server --requirepass <strong-password>
```

### ACLs (Redis 6+)

```bash
# Criar usuário com permissões limitadas
docker exec orquestra-redis redis-cli ACL SETUSER orquestra on >password ~* +@all

# Criar usuário只读
docker exec orquestra-redis redis-cli ACL SETUSER readonly on >readonly ~* +@read
```

### TLS

```yaml
# docker-compose.yml
command: redis-server --tls-port 6379 --port 0 --tls-cert-file /etc/redis/tls/server.crt --tls-key-file /etc/redis/tls/server.key --tls-ca-file /etc/redis/tls/ca.crt --tls-auth-clients no
```

## 📝 Logging Security

### Remover Dados Sensíveis

```python
# config/settings/production.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'sensitive': {
            '()': 'apps.core.logging.SensitiveDataFilter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['sensitive'],
        },
    },
}

# apps/core/logging.py
import re
import logging

class SensitiveDataFilter(logging.Filter):
    """Remove dados sensíveis dos logs"""

    PATTERNS = [
        (r'"password":\s*"[^"]+"', '"password": "***"'),
        (r'"secret_key":\s*"[^"]+"', '"secret_key": "***"'),
        (r'"token":\s*"[^"]+"', '"token": "***"'),
        (r'"api_key":\s*"[^"]+"', '"api_key": "***"'),
        (r'Bearer\s+[A-Za-z0-9\-._~+/]+', 'Bearer ***'),
    ]

    def filter(self, record):
        if record.msg:
            for pattern, replacement in self.PATTERNS:
                record.msg = re.sub(pattern, replacement, str(record.msg))
        return True
```

### Log Rotation

```yaml
# docker-compose.yml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🔍 Input Validation

### Pydantic Validation

```python
# apps/orders/serializers.py
from pydantic import BaseModel, Field, validator

class OrderItemSchema(BaseModel):
    product_sku: str = Field(..., min_length=1, max_length=50)
    quantity: int = Field(..., gt=0, le=100)

    @validator('product_sku')
    def validate_sku(cls, v):
        if not re.match(r'^[A-Z0-9\-]+$', v):
            raise ValueError('Invalid SKU format')
        return v
```

### SQL Injection Prevention

```python
# ❌ RUIM - Vulnerável
query = f"SELECT * FROM orders WHERE id = {order_id}"

# ✅ BOM - ORM protege
order = Order.objects.get(id=order_id)

# ✅ BOM - Raw SQL com parâmetros
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT * FROM orders WHERE id = %s", [order_id])
```

### XSS Prevention

```python
# Django templates auto-escape por padrão
# Para desativar apenas quando necessário:
{{ data|safe }}  # CUIDADO - use apenas com dados confiáveis
```

## 🔄 Backup e Recovery

### PostgreSQL Backup

```bash
# Backup
docker exec orquestra-db pg_dump -U orquestra orquestra | gzip > backup.sql.gz

# Restore
gunzip -c backup.sql.gz | docker exec -i orquestra-db psql -U orquestra orquestra
```

### Automated Backup (Cron)

```bash
# /etc/cron.d/orquestra-backup
0 2 * * * root docker exec orquestra-db pg_dump -U orquestra orquestra | gzip > /backups/orquestra-$(date +\%Y\%m\%d).sql.gz
0 3 * * * root find /backups -name "orquestra-*.sql.gz" -mtime +7 -delete
```

### Backup Crypt

```bash
# Criptografar backup
gpg --symmetric --cipher-algo AES256 backup.sql.gz

# Descriptografar
gpg --decrypt backup.sql.gz.gpg > backup.sql.gz
```

## 🚨 Monitoramento de Segurança

### Security Events

```python
# apps/core/audit.py
from structlog import get_logger

logger = get_logger()

def log_security_event(event_type: str, details: dict) -> None:
    logger.info(
        "security_event",
        event_type=event_type,
        **details,
    )

# Uso
log_security_event("login_failed", {
    "username": username,
    "ip": request.META['REMOTE_ADDR'],
    "user_agent": request.META['HTTP_USER_AGENT'],
})
```

### Failed Login Alerts

```python
# apps/dashboard/signals.py
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    logger.warning(
        "failed_login_attempt",
        username=credentials.get('username'),
        ip=request.META.get('REMOTE_ADDR'),
    )
```

### Anomaly Detection

```promql
# Prometheus - taxa de login falhos
rate(failed_login_attempts_total[5m]) > 10

# Prometheus - spikes de requisições
rate(django_http_requests_total[1m]) > 1000

# Prometheus - dead letters inesperadas
rate(rabbitmq_queue_messages{queue=~".*\\.dlq"}[5m]) > 5
```

## 🧪 Security Testing

### Dependency Scanning

```bash
# pip-audit (já configurado no CI)
uv run pip-audit

# Snyk
npm install -g snyk
snyk test
```

### Static Analysis

```bash
# Bandit - Python security linter
uv add bandit
uv run bandit -r apps/

# Semgrep
uv add semgrep
uv run semgrep --config auto
```

### Dynamic Analysis

```bash
# OWASP ZAP
docker run -t owasp/zap2docker-stable zap-baseline.py -t https://api.orquestra.com

# Nuclei
nuclei -u https://api.orquestra.com -t cves/
```

## 📋 Incident Response

### Checklist de Incidente

1. **Identificar**
   - O que aconteceu?
   - Quando?
   - Qual o impacto?

2. **Conter**
   - Isolar sistemas afetados
   - Bloquear IPs maliciosos
   - Desabilitar funcionalidades vulneráveis

3. **Erradicar**
   - Remover malware/backdoors
   - Corrigir vulnerabilidade
   - Rotacionar credenciais comprometidas

4. **Recuperar**
   - Restaurar de backup limpo
   - Verificar integridade
   - Monitorar por reinfecção

5. **Lição Aprendida**
   - Documentar incidente
   - Criar ADR
   - Atualizar RUNBOOK
   - Adicionar detecção automática

## 📚 Referências

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker_container)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
