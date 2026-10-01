# Regras de Mensageria

## Trigger

Aplicável a arquivos em `outbox/` e `handlers/`.

## Regras

1. **Transactional Outbox**
   - Gravar OutboxEvent na MESMA transação da mudança de estado
   - Nunca publicar fora da transação
   - Usar SELECT ... FOR UPDATE SKIP LOCKED no relay

2. **Idempotência**
   - API: header Idempotency-Key + hash do corpo
   - Consumidores: tabela Inbox com UNIQUE(consumer, message_id)
   - Gravar Inbox na mesma transação do efeito

3. **Retry**
   - Apenas para erros transitórios (ConnectionError, Timeout)
   - Erros de negócio NÃO fazem retry (ex.: PaymentDeclined)
   - Backoff exponencial + jitter
   - Máximo configurável

4. **DLQ**
   - Esgotado de retry → grava DeadLetter no banco
   - Rejeitar sem requeue → DLX → fila <consumidor>.dlq
   - Replay com o MESMO message_id

5. **Contrato de Mensagem**
   - Usar pydantic v2 versionado
   - Campos obrigatórios: message_id, type, version, occurred_at, correlation_id, causation_id, aggregate_id, traceparent, payload
   - Versionamento: "order.created.v1"

6. **Transações**
   - Nunca misturar I/O, lógica de negócio e mensageria
   - Transações curtas e específicas
   - Rollback em caso de erro

7. **Traceparent**
   - Gravar traceparent da request no outbox
   - Restaurar traceparent no relay
   - Propagar em todas as mensagens

8. **Celery**
   - task_default_queue_type="quorum"
   - broker_transport_options={"confirm_publish": True}
   - acks_late=True
   - prefetch=1
   - Sem autoscale (incompatível com quorum)
