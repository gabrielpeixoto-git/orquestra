# Preparação para Entrevistas Técnicas - Orquestra

## 🎯 Como Usar Este Projeto em Entrevistas

### Antes da Entrevista

1. **Revise o README**
   - Leia as seções "Destaques Técnicos" e "Desafios Superados"
   - Memorize 3-5 desafios específicos que você resolveu
   - Entenda o diagrama de arquitetura Mermaid

2. **Prepare o Ambiente Local**
   ```bash
   # Teste localmente para garantir que funciona
   uv run poe demo
   # Verifique: API, Dashboard, Jaeger, Grafana
   ```

3. **Tenha Screenshots Prontas**
   - Capturar 3-5 screenshots do dashboard
   - Salvar como `screenshots/` no repositório
   - Ter URLs de serviços prontos (Jaeger, Grafana)

4. **Prepare o Guia para Recrutadores**
   - Enviar `docs/RECRUITER_GUIDE.md` antes da entrevista
   - Sugere ao recrutador: "Este documento explica minhas decisões técnicas"

### Durante a Entrevista

#### Estrutura Sugerida da Apresentação (10-15 minutos)

**Slide 1: Visão Geral (2 min)**
- "Orquestra é uma plataforma de processamento de pedidos orientada a eventos"
- Stack: Django, RabbitMQ, PostgreSQL, Celery
- Padrões: Saga orquestrada, Transactional Outbox, DLQ
- Destaque: "Focado em confiabilidade e observabilidade"

**Slide 2: Arquitetura (3 min)**
- Mostrar diagrama Mermaid do README
- Explicar bounded contexts (orders, inventory, payments, etc.)
- Explicar comunicação via mensagens (RabbitMQ)
- Destaque: "Monólito modular permite evoluir para microservices"

**Slide 3: Desafios Técnicos (5 min)**
- Escolher 2-3 desafios do README:
  1. Idempotência em ambiente distribuído
  2. Consistência entre DB e broker (Transactional Outbox)
  3. Concorrência em estoque (SELECT FOR UPDATE)
- Para cada: problema → solução → resultado

**Slide 4: Qualidade e Observabilidade (3 min)**
- Mostrar métricas: 80% cobertura, mypy strict, CI verde
- Mostrar Jaeger trace (se tiver screenshot)
- Mostrar Grafana dashboard (se tiver screenshot)
- Destaque: "Sistema production-ready com observabilidade completa"

**Slide 5: O que Aprendi (2 min)**
- Hard skills: DDD, event-driven, observabilidade
- Soft skills: documentação, debugging, priorização
- Destaque: "Projeto me preparou para arquitetura sênior"

#### Perguntas Técnicas Comuns e Respostas

**Q: Por que você escolheu Django ao invés de FastAPI?**
A: Django oferece:
- ORM maduro com migrations automáticas
- Admin interface útil para debug
- Ecossistema vasto (DRF, Celery integrado)
- Maior estabilidade para monólito modular
- FastAPI seria melhor para microservices, mas Django é ideal para este caso

**Q: Por que saga orquestrada ao invés de coreografada?**
A: Orquestração:
- Centraliza lógica de negócio (mais fácil de entender)
- Permite implementar timeouts e compensações previsíveis
- Mais fácil de debugar (single source of truth)
- Coreografada seria mais escalável, mas mais complexa

**Q: Como você escala este sistema?**
A: 3 camadas:
1. **Horizontal**: Escalar workers, relay, API (Kubernetes HPA)
2. **Vertical**: Optimizar queries, caching Redis, connection pooling
3. **Arquitetural**: Split bounded contexts em microservices se necessário
- Já preparado: Kubernetes manifests, observabilidade, feature flags

**Q: O que acontece se o RabbitMQ cair?**
A: Resiliência em 3 níveis:
1. **Outbox**: Mensagens ficam PENDING no DB
2. **Relay**: Continua tentando publicar (retry com backoff)
3. **Watchdog**: Timeout detecta e compensa se necessário
- Nenhuma mensagem perdida, apenas atraso

**Q: Como você garante qualidade de código?**
A: Processo:
- Type hints obrigatórios (mypy strict)
- Ruff com 50+ regras (lint + format)
- TDD para features críticas
- CI/CD bloqueia merge se check falhar
- Pre-commit hooks para feedback rápido

**Q: Qual foi o bug mais difícil que você resolveu?**
A: (escolha um real do seu projeto):
- "Routing key Celery vs RabbitMQ - workers não consumiam mensagens"
- Solução: Consumidores alternativos RabbitMQ direto
- Aprendizado: Documentação vendor-specific é crítica
- Resultado: Workaround + documentação detalhada em TROUBLESHOOTING.md

#### Demo ao Vivo (se permitido)

**Preparação (2 min)**
```bash
# Terminal 1: Ambiente
uv run poe demo

# Terminal 2: Verificar health
curl http://localhost:8000/health/detailed
```

**Demo do Caminho Feliz (3 min)**
```bash
# Criar pedido
curl -X POST http://localhost:8000/api/v1/orders/ \
  -H "Idempotency-Key: interview-demo" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"sku": "PROD-001", "quantity": 2}]}'

# Copiar order_id e abrir no browser
# http://localhost:8000/orders/<uuid>/
# Explicar timeline em tempo real
```

**Demo de Falha (2 min)**
```bash
# Acessar laboratório no browser
# http://localhost:8000/laboratory/
# Criar pedido com estoque insuficiente
# Assistir compensação automática
```

**Demo de Observabilidade (2 min)**
```bash
# Jaeger: http://localhost:16686
# Buscar trace do pedido criado
# Mostrar spans: API → outbox → relay → workers

# Grafana: http://localhost:3000
# Mostrar dashboard orquestra
# Explicar métricas de negócio
```

### Após a Entrevista

#### Follow-up Email

**Assunto**: Orquestra - Demo de Entrevista e Recursos Adicionais

Corpo:
```
Olá [Nome],

Foi um prazer discutir o projeto Orquestra com você. Como mencionado, aqui estão recursos adicionais:

**Documentação Técnica**:
- Guia para Recrutadores: docs/RECRUITER_GUIDE.md
- Arquitetura Detalhada: docs/ARCHITECTURE.md
- Troubleshooting Avançado: docs/TROUBLESHOOTING.md

**Demo ao Vivo**:
- Repositório: https://github.com/gabri/orquestra
- Quick Start: 3 comandos no README
- Demo automatizada: uv run poe demo

**Screenshots**:
- [Link para screenshots se tiver hospedado]
- Caso contrário: "Posso enviar screenshots na próxima chamada"

Se você tiver mais perguntas técnicas sobre arquitetura, padrões ou decisões de design, estou à disposição.

Atenciosamente,
[Seu Nome]
```

#### LinkedIn Post (opcional)

**Texto sugerido**:
```
Acabei de apresentar meu projeto Orquestra em uma entrevista técnica! 🚀

É uma plataforma de processamento de pedidos orientada a eventos com:
- Saga orquestrada com compensação automática
- Transactional Outbox para consistência DB/broker
- Observabilidade completa (Jaeger, Prometheus, Grafana)
- 80% cobertura de testes, mypy strict, CI/CD

Desenvolvi para demonstrar skills em arquitetura de sistemas distribuídos e confiabilidade. O que vocês acham?

#python #django #microservices #sagapattern #observabilidade
```

## 🎓 Estudo Adicional

### Tópicos para Aprofundar

Se o entrevistador perguntar sobre tópicos relacionados:

**Event Sourcing vs CDC**:
- Orquestra usa CDC (Change Data Capture) via outbox
- Event Sourcing seria mais complexo mas oferece replay completo
- Trade-off: simplicidade vs poder de replay

**CQRS (Command Query Responsibility Segregation)**:
- Orquestra não usa CQRS explícito
- Poderia adicionar read models otimizados para queries complexas
- Benefício: performance em leituras frequentes

**Feature Flags**:
- Não implementado mas documentado em roadmap futuro
- Unleash ou Flagsmith para gradual rollout
- Benefício: canary deployments e dark launching

**Chaos Engineering**:
- Chaos Monkey ou LitmusChaos para testar resiliência
- Injetar falhas de forma sistemática
- Benefício: confiança em auto-recuperação

**Multi-region Deployment**:
- PostgreSQL streaming replication
- RabbitMQ federation ou shovel
- Geo-redundancy com DNS round-robin

### Leitura Recomendada

Se o entrevistador perguntar "O que você leu para construir isso?":

- **Designing Data-Intensive Applications** (Martin Kleppmann)
  - CAP theorem, consistency models
  - Transactional outbox pattern
- **Microservices Patterns** (Chris Richardson)
  - Saga pattern, event-driven architecture
  - Database per service vs shared database
- **Release It!** (Michael Nygard)
  - Patterns for production systems
  - Circuit breakers, bulkheads, timeouts
- **Domain-Driven Design** (Eric Evans)
  - Bounded contexts, aggregates
  - Ubiquitous language

## 💡 Dicas de Sucesso

### O que NÃO fazer

❌ Não diga "usei Celery porque todo mundo usa"
✅ Diga "usei Celery por delayed delivery nativo e task routing"

❌ Não diga "não sei, chatgpt escreveu isso"
✅ Diga "pesquisei a documentação oficial e implementei assim"

❌ Não diga "foi fácil, Django faz tudo"
✅ Diga "Django simplifica, mas precisei configurar X, Y, Z"

❌ Não diga "não tenho screenshots"
✅ Diga "posso fazer uma demo ao vivo ou enviar depois"

### O que FAZER

✅ Prepare 3 histórias de desafios técnicos
✅ Tenha números concretos (80% cobertura, 51 testes)
✅ Seja honesto sobre trade-offs
✅ Mostre entusiasmo pelo que aprendeu
✅ Prepare perguntas para o entrevistador

### Perguntas para Fazer ao Entrevistador

1. "Vocês usam saga pattern ou eventual consistency?"
2. "Qual stack de observabilidade vocês usam?"
3. "Como vocês lidam com idempotência em microservices?"
4. "Vocês têm SLOs definidos para serviços críticos?"
5. "Qual abordagem vocês usam para feature flags?"

---

**Lembre-se**: O objetivo não é mostrar que você sabe tudo, mas que você:
- Pensa criticamente sobre arquitetura
- Faz decisões baseadas em trade-offs
- Aprende continuamente
- Documenta e compartilha conhecimento

Boa sorte! 🚀
