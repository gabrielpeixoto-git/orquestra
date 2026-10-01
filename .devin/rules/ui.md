# Regras de UI

## Trigger

Aplicável a arquivos em `templates/` e `static/`.

## Regras

1. **Acessibilidade**
   - Contraste AA mínimo (WCAG 2.1)
   - Foco visível em todos os elementos interativos
   - aria-live em atualizações dinâmicas
   - Respeitar prefers-reduced-motion

2. **Responsividade**
   - Testar em 375px, 768px e 1280px
   - Mobile-first
   - Sem layout shift (CLS < 0.1)

3. **Performance**
   - Zero asset 404
   - Zero erro no console
   - Imagens com dimensões explícitas
   - Skeletons durante loading

4. **Componentes**
   - KPIs com sparkline SVG
   - Pipeline animado com pulso
   - Tabela viva com htmx polling (2s)
   - Timeline vertical com tentativas e latência
   - Toasts para feedback
   - Empty states descritivos
   - Estados de erro claros

5. **Design**
   - Escala de espaçamento de 4px
   - Hierarquia tipográfica clara
   - Cores semânticas (verde/âmbar/rosa)
   - Fonte do sistema (system-ui)
   - ui-monospace para IDs e código

6. **Validação**
   - Validar no Preview do Devin Desktop
   - Capturar erros do console
   - Verificar contrastes
   - Testar foco e navegação por teclado
