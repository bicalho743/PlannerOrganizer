# Checklist de Preparação para Produção

## 1. Limpeza do Ambiente

### Arquivos para Remover
- [x] Ferramentas de diagnóstico e correção (use listar_arquivos_dev.py para ver a lista)
- [x] Ferramentas de download e distribuição
- [x] Ferramentas de teste e verificação
- [x] Versões alternativas e apps não essenciais
- [x] Diretórios temporários e de backup

### Arquivos para Preservar
- [x] Importação de clientes (importar_clientes.py)
- [x] Importação de propostas (importar_propostas.py, importar_propostas_v2.py)
- [x] Funcionalidade de backup (criar_ponto_backup.py)
- [x] Páginas de login e planos (login.py, login_simples.py, planos_*.py)

## 2. Preparação do Banco de Dados

### Migração e Verificações
- [x] Remover dados de teste e exemplos
- [x] Verificar integridade referencial
- [x] Executar script migracao_stripe.sql para adicionar novas colunas/tabelas
- [x] Criar índices para otimização de consultas
- [x] Verificar se view vw_status_assinatura está funcionando corretamente

## 3. Segurança e Acesso

### Configurações e Credenciais
- [x] Desativar modos de debug e desenvolvimento em todos os arquivos
- [x] Configurar variáveis de ambiente seguras (STRIPE_API_KEY, etc.)
- [x] Verificar se todos arquivos sensíveis estão no .gitignore
- [x] Garantir que chaves de API estão seguras e não hard-coded
- [x] Configurar tempo de expiração de sessão adequado
- [x] Verificar isolamento de dados entre inquilinos (multi-tenant)

## 4. Integração com Stripe

### Implementação e Testes
- [x] Verificar se módulo utils/stripe_integration.py está completo
- [x] Adicionar página pages/stripe_webhook.py para processar webhooks 
- [x] Criar página pages/minha_assinatura.py para gerenciar assinatura
- [x] Implementar limites baseados nos planos (número de clientes, propostas, etc.)
- [x] Testar fluxo completo de assinatura (checkout, portal do cliente, cancelamento)
- [x] Verificar se plano é atualizado corretamente após pagamento

## 5. Interface do Usuário

### Ajustes e Melhorias
- [x] Integrar página de planos com o resto da aplicação
- [x] Exibir informações da assinatura no painel do usuário
- [x] Implementar barras de progresso para mostrar uso atual vs limites do plano
- [x] Adicionar alertas quando o usuário está próximo dos limites do plano
- [x] Garantir que todas as páginas são responsivas e acessíveis

## 6. Testes Finais

### Verificações de Qualidade
- [ ] Testar sistema completo em um ambiente limpo
- [ ] Verificar se todas as funcionalidades principais funcionam como esperado
- [ ] Testar diferentes navegadores e dispositivos
- [ ] Verificar desempenho e tempos de carregamento
- [ ] Executar teste de carga básico para verificar a robustez do sistema

## 7. Documentação e Suporte

### Materiais e Recursos
- [ ] Atualizar documentação do usuário com novas funcionalidades
- [ ] Criar FAQ para questões comuns relacionadas a assinaturas
- [ ] Documentar processos de suporte para questões de faturamento
- [ ] Preparar materiais de comunicação para anunciar novos planos e recursos
- [ ] Verificar se todos os contatos e links de suporte estão atualizados

---

**Nota:** Após concluir este checklist, execute o script `preparar_para_stripe.py` que verificará automaticamente vários destes itens e criará um backup final antes do lançamento.