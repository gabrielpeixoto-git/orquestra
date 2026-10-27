# Contribuindo com o Orquestra

Obrigado pelo interesse em contribuir com o projeto Orquestra! Este documento fornece diretrizes para contribuições.

## 🚀 Como Começar

### Pré-requisitos

- Python 3.13+
- uv (gerenciador de pacotes Python)
- Docker e Docker Compose
- Git

### Setup do Ambiente

```bash
# 1. Clone o repositório
git clone https://github.com/SEU-USUARIO/orquestra.git
cd orquestra

# 2. Instale as dependências
uv sync

# 3. Suba a infraestrutura
uv run poe up

# 4. Rode as migrations
uv run python manage.py migrate

# 5. Rode o seed de dados de demonstração
uv run python manage.py seed_demo

# 6. Verifique os health checks
curl http://localhost:8000/health/ready
```

## 📋 Processo de Desenvolvimento

### 1. Crie uma Branch

```bash
git checkout -b feature/nome-da-feature
# ou
git checkout -b fix/nome-do-bug
```

### 2. Faça as Alterações

- Siga as convenções de código descritas em `AGENTS.md`
- Adicione type hints em todas as funções
- Escreva docstrings no padrão Google Style
- Mantenha arquivos com no máximo 300 linhas

### 3. Execute os Testes

```bash
# Rodar todos os testes
uv run pytest

# Rodar com coverage
uv run pytest --cov=apps --cov-report=term-missing

# Rodar apenas testes de integração
uv run pytest -m integration
```

### 4. Execute as Verificações de Qualidade

```bash
# Verificar formatação, linting, tipos e Django
uv run poe check
```

Este comando executa:
- `ruff format --check` - Verifica formatação
- `ruff check` - Verifica linting
- `mypy` - Verifica tipos
- `python manage.py check` - Verifica configuração Django

### 5. Commit suas Alterações

```bash
git add .
git commit -m "feat: descrição concisa da feature"
```

Use conventional commits:
- `feat:` nova feature
- `fix:` correção de bug
- `docs:` alteração em documentação
- `refactor:` refatoração de código
- `test:` adição de testes
- `chore:` tarefas de manutenção

### 6. Push e Pull Request

```bash
git push origin feature/nome-da-feature
```

Crie uma Pull Request no GitHub com:
- Título descritivo
- Descrição detalhada das alterações
- Referência a issues relacionadas (se houver)

## 🎯 Convenções de Código

### Python

- Python 3.13+
- Type hints obrigatórios em todas as funções e classes
- Docstrings no padrão Google Style em funções/classes públicas
- Máximo 4 parâmetros por função (use dataclasses para mais)
- Arquivos com no máximo 300 linhas
- Early return para reduzir aninhamento
- Nomes descritivos (evite `data`, `temp`, `info`)

### Django

- Services em `apps/<context>/services.py`
- Views em `apps/<context>/views.py`
- Serializers em `apps/<context>/serializers.py`
- Models em `apps/<context>/models.py`
- Handlers Celery em `apps/<context>/tasks/handlers.py`

### Mensageria

- Contratos de mensagem em `apps/messaging/messages.py`
- Nunca importe services de outro contexto (enforced por import-linter)
- Use o contrato de mensagem pydantic v2

## 🧪 Testes

### Escrevendo Testes

- Use pytest
- Testes unitários devem ser rápidos e isolados
- Testes de integração devem ser marcados com `@pytest.mark.integration`
- Use factory-boy para fixtures
- Mantenha cobertura ≥ 85%

### Exemplo de Teste

```python
import pytest
from apps.orders.services import create_order

def test_create_order_success():
    """Test creating an order successfully."""
    order = create_order(
        customer_id=uuid4(),
        items=[{"sku": "PROD-001", "quantity": 2}]
    )
    assert order.status == "PENDING"
    assert len(order.items) == 1
```

## 📝 Documentação

### Quando Documentar

- Novas features: atualize README.md e ROADMAP.md
- Decisões de arquitetura: crie ADR em `docs/adr/`
- Mudanças de API: atualize docs/ARCHITECTURE.md
- Bugs conhecidos: atualize docs/TROUBLESHOOTING.md

### Formato de ADR

```markdown
# ADR-XXXX: Título da Decisão

## Status
Aceito/Rejeitado

## Contexto
Descrição do problema

## Decisão
Descrição da solução escolhida

## Consequências
Impactos positivos e negativos
```

## 🔒 Segurança

- Nunca exponha credenciais, tokens ou secrets
- Use variáveis de ambiente para secrets
- Valide e sanitize todos os inputs externos
- Reporte vulnerabilidades via private channel

## 🐛 Reportando Bugs

### Antes de Reportar

1. Verifique se o bug já foi reportado
2. Tente reproduzir com a versão mais recente
3. Colete informações relevantes:
   - Versão do Python/Django
   - Logs de erro
   - Passos para reproduzir

### Criando uma Issue

Use o template de bug report:
- Título descritivo
- Comportamento esperado
- Comportamento atual
- Passos para reproduzir
- Ambiente (OS, Python version)
- Logs relevantes

## 💡 Sugestões de Features

### Antes de Sugerir

1. Verifique se a feature já foi solicitada
2. Verifique ROADMAP.md para ver se já está planejado
3. Considere o escopo do projeto

### Criando uma Issue

Use o template de feature request:
- Título descritivo
- Descrição da feature
- Caso de uso
- Solução proposta (opcional)

## 🤝 Código de Conduta

- Seja respeitoso e inclusivo
- Foque no que é melhor para a comunidade
- Aceite críticas construtivas
- Ajude outros contribuidores

## 📞 Contato

Para dúvidas sobre contribuição:
- Abra uma issue com a label `question`
- Entre em contato via email

---

**Lembre-se**: Contribuições são bem-vindas em qualquer forma: código, documentação, testes, feedback!
