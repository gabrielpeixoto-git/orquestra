# Screenshots do Orquestra

Esta pasta contém screenshots do dashboard Orquestra para demonstrar a arquitetura e funcionalidades do sistema.

## Estrutura de Pastas

```
screenshots/
├── dashboard/           # Screenshots do dashboard principal
│   ├── overview.png    # Visão geral com KPIs
│   ├── orders_list.png # Lista de pedidos com filtros
│   └── order_timeline.png # Timeline de pedido
├── observability/      # Screenshots de observabilidade
│   ├── grafana_dashboard.png # Dashboard Grafana
│   ├── jaeger_trace.png     # Trace no Jaeger
│   └── health_monitoring.png # Monitoramento de saúde
└── failure-scenarios/  # Screenshots de cenários de falha
    ├── dead_letters.png     # Dead Letter Queue
    └── laboratory.png       # Laboratório de testes
```

## Como Capturar Screenshots

Consulte o guia completo em [../docs/SCREENSHOTS.md](../docs/SCREENSHOTS.md).

## Comandos Rápidos

```bash
# Subir ambiente
uv run poe up

# Rodar migrations e seed
uv run python manage.py migrate
uv run python manage.py seed_demo

# Iniciar servidor
uv run python manage.py runserver

# Acessar URLs
# Dashboard: http://localhost:8000/
# Pedidos: http://localhost:8000/orders/
# Dead Letters: http://localhost:8000/dead-letters/
# Laboratório: http://localhost:8000/laboratory/
# Saúde: http://localhost:8000/health/
```

## Dicas

- Use dark mode para visual mais profissional
- Capture em 100% zoom para máxima qualidade
- Use PNG para qualidade ou WebP para tamanho menor
- Remova dados sensíveis se necessário
- Mantenha nomes de arquivos descritivos e em lowercase
