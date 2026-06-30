-- Normaliza propostas.status_execucao para o vocabulário canônico.
-- Canônico: 'Não iniciada', 'Em execução', 'Finalizada', 'Cancelada'.
-- Idempotente: pode ser executada várias vezes sem efeito colateral.

UPDATE propostas
SET status_execucao = 'Finalizada'
WHERE lower(trim(status_execucao)) IN ('concluida', 'concluída', 'vendida', 'finalizada')
  AND status_execucao <> 'Finalizada';

UPDATE propostas
SET status_execucao = 'Em execução'
WHERE lower(trim(status_execucao)) IN ('iniciada', 'em execucao', 'em execução')
  AND status_execucao <> 'Em execução';

UPDATE propostas
SET status_execucao = 'Não iniciada'
WHERE lower(trim(status_execucao)) IN ('nao iniciada', 'não iniciada')
  AND status_execucao <> 'Não iniciada';

UPDATE propostas
SET status_execucao = 'Cancelada'
WHERE lower(trim(status_execucao)) = 'cancelada'
  AND status_execucao <> 'Cancelada';
