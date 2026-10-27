# Guia de Screenshots para Portfólio

Este documento fornece instruções para capturar screenshots do dashboard Orquestra para usar em portfólios, LinkedIn e apresentações.

## 📸 Screenshots Recomendados

### 1. Visão Geral do Dashboard (Principal)

**URL**: http://localhost:8000/

**O que capturar**:
- KPIs (Total Orders, Revenue, Success Rate, Dead Letters)
- Gráfico de distribuição de status (doughnut chart)
- Lista de contagem por status
- Sidebar com navegação
- Tema dark mode ativado (opcional, fica mais profissional)

**Dica**: Maximimize o browser e capture em tela cheia para mostrar UI completa. Use dark mode para visual mais profissional.

**Caption sugerido**: "Dashboard de controle com KPIs em tempo real"

---

### 2. Lista de Pedidos com Tabela Viva

**URL**: http://localhost:8000/orders/

**O que capturar**:
- Tabela com dados reais (150+ pedidos no seed_demo)
- Filtros funcionais (search por ID, filtro por status)
- Status badges coloridos (Pendente, Estoque Reservado, Pagamento Aprovado, Confirmado, Cancelado)
- Badge "Tempo Real" indicando auto-refresh
- Sidebar ativa na seção "Pedidos"

**Dica**: Aguarde alguns segundos para mostrar que a tabela atualiza automaticamente via HTMX.

**Caption sugerido**: "Tabela de pedidos com auto-refresh em tempo real via HTMX"

---

### 3. Timeline de Pedido (Saga Completa)

**URL**: http://localhost:8000/orders/<uuid>/

**O que capturar**:
- Timeline vertical completa com eventos da saga
- Eventos em ordem: OrderCreated → StockReserved → PaymentProcessed → OrderConfirmed
- Timestamps de cada etapa
- Detalhes do pedido (ID, cliente, status, total, datas)
- Status badge colorido
- Sidebar ativa

**Como preparar**:
1. Crie um pedido via API: `curl -X POST http://localhost:8000/api/v1/orders/ -H "Idempotency-Key: demo-1" -H "Content-Type: application/json" -d '{"items": [{"sku": "PROD-001", "quantity": 2}]}'`
2. Aguarde a saga completar (pode levar alguns segundos)
3. Copie o order_id da resposta
4. Abra a página de detalhe: http://localhost:8000/orders/<order_id>/
5. Capture a timeline

**Caption sugerido**: "Timeline da saga orquestrada com trace completo de eventos"

---

### 4. Dead Letters com Replay

**URL**: http://localhost:8000/dead-letters/

**O que capturar**:
- Tabela de dead letters (15+ mensagens no seed_demo)
- Colunas: ID, Fila, Tipo, Erro, Criado em, Ações
- Badge "Tempo Real" indicando auto-refresh
- Sidebar ativa na seção "Falhas / DLQ"

**Como preparar**:
1. O seed_demo já cria 15 dead letters automaticamente
2. Acesse a página diretamente
3. Capture a tabela

**Caption sugerido**: "Dead Letter Queue com interface de replay manual"

---

### 5. Laboratório de Testes

**URL**: http://localhost:8000/laboratory/

**O que capturar**:
- Card "Gerar Pedido de Teste" com botão
- Card "Injetar Falha" com botões para Timeout de Pagamento e Erro de Estoque
- Layout grid responsivo
- Sidebar ativa na seção "Laboratório"

**Caption sugerido**: "Laboratório para injeção de falhas e testes de saga"

---

### 6. Saúde dos Serviços

**URL**: http://localhost:8000/health/

**O que capturar**:
- Indicador de "Monitoramento em Tempo Real" com ping animado
- Cards de status de cada serviço (API, DB, Redis, RabbitMQ)
- Links para observabilidade (Jaeger, Prometheus, Grafana)
- Sidebar ativa na seção "Saúde"

**Caption sugerido**: "Monitoramento de saúde dos serviços em tempo real"

---

### 7. Grafana Dashboard

**URL**: http://localhost:3000 (admin/admin)

**O que capturar**:
- Dashboard Orquestra provisionado
- Gráficos de métricas (orders, payments, inventory)
- Status de serviços
- Dashboard selecionado no menu lateral

**Como preparar**:
1. Suba com observabilidade: `docker compose --profile obs up -d`
2. Aguarde alguns minutos para coletar dados
3. Capture o dashboard

**Caption sugerido**: "Observabilidade com Grafana dashboards provisionados"

---

### 8. Jaeger Distributed Tracing

**URL**: http://localhost:16686

**O que capturar**:
- Lista de traces recentes
- Trace detalhado da saga com spans (API → Outbox → Relay → Workers)
- Timeline com latência de cada span
- Service map (se disponível)

**Como preparar**:
1. Crie um pedido via API
2. Busque o trace no Jaeger pelo correlation_id
3. Abra o trace detalhado
4. Capture

**Caption sugerido**: "Distributed tracing com OpenTelemetry e Jaeger"

---

## 🎥 Como Capturar Screenshots

### Windows

1. **Snipping Tool** (Windows 10/11):
   - Pressione `Win + Shift + S`
   - Selecione a área
   - Salve como PNG

2. **ShareX** (recomendado para qualidade):
   - Baixe em https://getsharex.com/
   - Configure para captura de janela
   - Salve em alta qualidade

### macOS

1. **Built-in Screenshot**:
   - `Cmd + Shift + 4` - Selecionar área
   - `Cmd + Shift + 5` - Interface completa
   - Salva em Desktop

2. **CleanShot X** (recomendado):
   - Compra em https://cleanshot.com/
   - Remove sombras e fundo
   - Adiciona bordas automaticamente

### Linux

1. **GNOME Screenshot**:
   - `gnome-screenshot`
   - Disponível na maioria das distros

2. **Flameshot** (recomendado):
   - `sudo apt install flameshot`
   - `flameshot gui`

---

## 🎨 Dicas de Design

### Antes de Capturar

1. **Limpe o browser**:
   - Remova extensões visíveis
   - Use modo privativo se necessário
   - Maximimize a janela (recomendado: 1920x1080 ou maior)

2. **Dados de exemplo**:
   - Use `uv run python manage.py seed_demo` para dados consistentes
   - O seed_demo cria 150 pedidos com dados realistas
   - Evite dados sensíveis

3. **Dark mode**:
   - Dashboard já suporta dark mode automaticamente
   - Use para visual mais profissional
   - Configure sistema para dark mode ou use o toggle no sidebar

4. **Zoom do browser**:
   - Use 100% zoom para captura nativa
   - Evite zoom < 100% (pixels borrados)
   - Evite zoom > 100% (cabe menos conteúdo)

### Pós-Processamento

1. **Remova dados sensíveis**:
   - IDs completos de UUID (se necessário)
   - Tokens ou chaves (não existem no dashboard, mas verifique)
   - Use ferramenta de edição se necessário

2. **Adicione bordas/arredondamento** (opcional)**:
   - Melhora apresentação em portfólios
   - Use ferramentas como CleanShot X, Figma ou Canva
   - Sugestão: borda cinza 2px, arredondamento 8px

3. **Tamanho consistente**:
   - Mantenha aspect ratio
   - Sugestão: 16:9 (1920x1080) ou 4:3 (1600x1200)
   - Min width: 1200px para legibilidade
   - Compressão: PNG (qualidade) ou WebP (tamanho menor)

---

## 📦 Organização de Screenshots

### Estrutura de Pastas

```
orquestra/
├── screenshots/
│   ├── dashboard/
│   │   ├── overview.png
│   │   ├── orders-table.png
│   │   └── order-timeline.png
│   ├── observability/
│   │   ├── grafana.png
│   │   ├── jaeger-trace.png
│   │   └── health-status.png
│   └── failure-scenarios/
│       ├── dead-letters.png
│       └── laboratory.png
```

### Nomenclatura

Use nomes descritivos e minúsculos com underscores:
- `overview.png` - Visão geral do dashboard
- `orders_list.png` - Lista de pedidos
- `order_timeline.png` - Timeline de pedido
- `dead_letters.png` - Dead Letter Queue
- `grafana_dashboard.png` - Dashboard Grafana
- `jaeger_trace.png` - Trace no Jaeger
- `health_monitoring.png` - Monitoramento de saúde

---

## 🎯 Uso em LinkedIn

### Post de Projeto

```
Acabei de completar o Orquestra! 🚀

Uma plataforma de processamento de pedidos orientada a eventos com:
- Saga orquestrada com compensação automática
- Transactional Outbox para consistência DB/broker
- Observabilidade completa (Jaeger, Prometheus, Grafana)
- 90% cobertura de testes, mypy strict, CI/CD

Desenvolvi para demonstrar skills em arquitetura de sistemas distribuídos.

Código: https://github.com/<username>/orquestra

#python #django #microservices #sagapattern #observabilidade #backend
```

### Anexar Screenshots

- Anexe 3-5 screenshots principais
- 1ª: Visão geral do dashboard (overview.png)
- 2ª: Lista de pedidos com filtros (orders_list.png)
- 3ª: Timeline da saga (order_timeline.png)
- 4ª: Observabilidade (grafana_dashboard.png ou jaeger_trace.png)
- 5ª: (opcional) Dead letters com replay (dead_letters.png)

---

## 🎓 Uso em Portfólio

### Seção de Projetos

**Título**: Orquestra - Event-Driven Order Processing Platform

**Descrição**:
Plataforma de processamento de pedidos orientada a eventos implementando saga orquestrada com compensação automática, transactional outbox pattern e observabilidade completa. Construída com Django, Celery, RabbitMQ e PostgreSQL.

**Screenshots**:
- Grid 2x2 com 4 screenshots principais
- Caption com descrição técnica abaixo de cada screenshot
- Link para repositório GitHub

**Tech Stack**:
- Python 3.14, Django 6.1, Celery 5.6
- RabbitMQ 4.x, PostgreSQL 18, Redis
- OpenTelemetry, Jaeger, Prometheus, Grafana
- HTMX, Alpine.js, Chart.js

---

## 📹 GIF Animado (Opcional)

### Ferramentas

1. **LICEcap** (Windows/macOS):
   - https://www.cockos.com/licecap/
   - Leve e simples
   - Exporta GIF

2. **ScreenToGif** (Windows):
   - https://www.screentogif.com/
   - Editor incluído
   - Otimização de arquivo

3. **OBS Studio** (Cross-platform):
   - https://obsproject.com/
   - Profissional
   - Exporta vídeo

### Cenário para GIF

**Fluxo da saga**:
1. Criar pedido via API (curl ou UI do laboratório)
2. Assistir timeline atualizar na página de detalhes
3. Ver mudança de status (PENDING → STOCK_RESERVED → PAYMENT_SUCCEEDED → CONFIRMED)
4. Mostrar KPIs atualizando na visão geral

**Duração**: 10-15 segundos
**Frame rate**: 15-20 fps
**Size**: < 5MB
**Resolução**: 1280x720 (HD) ou 1920x1080 (Full HD)

---

## ✅ Checklist Final

Antes de publicar:

- [ ] Ambiente rodando: `uv run poe up` + `uv run python manage.py seed_demo`
- [ ] Screenshots capturados em alta qualidade (PNG, 100% zoom)
- [ ] Dados sensíveis removidos (se necessário)
- [ ] Nomes de arquivos descritivos (lowercase com underscores)
- [ ] Captions preparados para cada screenshot
- [ ] GIF animado (opcional, mas recomendado)
- [ ] Organização em pastas (dashboard/, observability/, failure-scenarios/)
- [ ] Links verificados (GitHub, documentação)
- [ ] Tema consistente (dark mode recomendado)

---

## 🚀 Comandos Rápidos para Captura

```bash
# 1. Subir infraestrutura
uv run poe up

# 2. Rodar migrations e seed
uv run python manage.py migrate
uv run python manage.py seed_demo

# 3. Iniciar servidor
uv run python manage.py runserver

# 4. Criar pedido para timeline
curl -X POST http://localhost:8000/api/v1/orders/ \
  -H "Idempotency-Key: demo-1" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"sku": "PROD-001", "quantity": 2}]}'

# 5. Acessar URLs
# Dashboard: http://localhost:8000/
# Pedidos: http://localhost:8000/orders/
# Dead Letters: http://localhost:8000/dead-letters/
# Laboratório: http://localhost:8000/laboratory/
# Saúde: http://localhost:8000/health/
```

---

**Nota**: Screenshots são um ativo valioso do seu portfólio. Invista tempo para capturar imagens de alta qualidade que demonstrem seus conhecimentos técnicos e a complexidade da arquitetura implementada.
