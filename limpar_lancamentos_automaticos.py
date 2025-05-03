"""
Script para excluir todos os lançamentos financeiros automáticos gerados pelo sistema
"""
import os
import psycopg2
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL não encontrada")
            return None
        return psycopg2.connect(db_url)
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {str(e)}")
        return None

def excluir_todos_lancamentos_automaticos():
    """Exclui todos os lançamentos financeiros automáticos relacionados a propostas"""
    conn = get_db_connection()
    if not conn:
        return False, "Erro ao conectar ao banco de dados"
    
    try:
        cursor = conn.cursor()
        
        # Contar quantos lançamentos serão afetados
        cursor.execute("""
            SELECT COUNT(*) FROM financeiro 
            WHERE proposta_id IS NOT NULL
            OR descricao LIKE 'Proposta #%'
        """)
        total = cursor.fetchone()[0]
        
        # Excluir todos os lançamentos relacionados a propostas
        cursor.execute("""
            DELETE FROM financeiro 
            WHERE proposta_id IS NOT NULL
            OR descricao LIKE 'Proposta #%'
        """)
        
        conn.commit()
        return True, f"Excluídos {total} lançamentos financeiros automáticos com sucesso"
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao excluir lançamentos: {e}")
        return False, f"Erro ao excluir lançamentos: {e}"
    finally:
        if conn:
            if 'cursor' in locals() and cursor:
                cursor.close()
            conn.close()

def desativar_geracao_lancamentos():
    """Modifica o código para desativar completamente a geração de lançamentos financeiros"""
    possiveis_locais = [
        "utils/proposta.py",
        "utils/financeiro.py",
        "utils/finalizar_proposta.py",
        "pages/propostas.py"
    ]
    
    arquivos_modificados = []
    
    for arquivo_path in possiveis_locais:
        if not os.path.exists(arquivo_path):
            continue
            
        try:
            # Ler conteúdo
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
            # Verificar se tem função de adicionar lançamento
            if "adicionar_lancamento_financeiro" in conteudo or "INSERT INTO financeiro" in conteudo:
                # Fazer backup
                backup_path = f"{arquivo_path}.bak"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(conteudo)
                    
                # Método 1: Substituir função adicionar_lancamento_financeiro
                if "def adicionar_lancamento_financeiro" in conteudo:
                    # Encontrar e substituir a implementação da função
                    linhas = conteudo.split('\n')
                    nova_implementacao = []
                    encontrou_func = False
                    nivel_indentacao = 0
                    
                    for i, linha in enumerate(linhas):
                        if "def adicionar_lancamento_financeiro" in linha:
                            encontrou_func = True
                            nova_implementacao.append(linha)
                            # Calcular indentação
                            nivel_indentacao = len(linha) - len(linha.lstrip())
                            # Adicionar instruções para desativar
                            espaco = ' ' * (nivel_indentacao + 4)
                            nova_implementacao.append(f"{espaco}# Função desativada para não gerar lançamentos automáticos")
                            nova_implementacao.append(f"{espaco}logger.info(f\"Geração de lançamento financeiro desativada. Descrição: {{descricao}}, Valor: {{valor}}\")")
                            nova_implementacao.append(f"{espaco}return None # Não executa o código original")
                        elif encontrou_func:
                            # Verificar se ainda estamos na mesma função
                            if linha.strip() and len(linha) - len(linha.lstrip()) <= nivel_indentacao:
                                encontrou_func = False
                                nova_implementacao.append(linha)
                            # Se ainda estamos na função, ignoramos o conteúdo
                        else:
                            nova_implementacao.append(linha)
                            
                    # Substituir no conteúdo
                    conteudo = '\n'.join(nova_implementacao)
                
                # Método 2: Interceptar chamadas para a função
                if "adicionar_lancamento_financeiro(" in conteudo:
                    conteudo = conteudo.replace(
                        "adicionar_lancamento_financeiro(",
                        "# Chamada desativada para não gerar lançamentos automáticos\n" +
                        "        logger.info(f\"Chamada para geração de lançamento financeiro ignorada\")\n" +
                        "        # adicionar_lancamento_financeiro("
                    )
                
                # Método 3: Desativar INSERT diretos
                if "INSERT INTO financeiro" in conteudo:
                    linhas = conteudo.split('\n')
                    for i, linha in enumerate(linhas):
                        if "INSERT INTO financeiro" in linha:
                            # Encontrar o início do bloco
                            inicio = i
                            while inicio > 0 and "cursor.execute" not in linhas[inicio]:
                                inicio -= 1
                                
                            # Comentar a linha com cursor.execute
                            if "cursor.execute" in linhas[inicio]:
                                indentacao = linhas[inicio][:linhas[inicio].find("cursor")]
                                linhas[inicio] = f"{indentacao}# DESATIVADO: {linhas[inicio].lstrip()}"
                                linhas.insert(inicio, f"{indentacao}logger.info(\"INSERT INTO financeiro desativado\")")
                    
                    conteudo = '\n'.join(linhas)
                
                # Garantir que o módulo logging esteja importado
                if "import logging" not in conteudo:
                    import_pos = conteudo.find("import ")
                    if import_pos >= 0:
                        # Encontrar o final do bloco de importações
                        linhas = conteudo.split('\n')
                        ultima_importacao = 0
                        for i, linha in enumerate(linhas):
                            if linha.startswith("import ") or linha.startswith("from "):
                                ultima_importacao = i
                        
                        # Adicionar import logging após a última importação
                        linhas.insert(ultima_importacao + 1, "import logging")
                        linhas.insert(ultima_importacao + 2, "logger = logging.getLogger(__name__)")
                        conteudo = '\n'.join(linhas)
                    else:
                        # Adicionar no início do arquivo
                        conteudo = "import logging\nlogger = logging.getLogger(__name__)\n\n" + conteudo
                
                # Salvar as alterações
                with open(arquivo_path, 'w', encoding='utf-8') as f:
                    f.write(conteudo)
                    
                arquivos_modificados.append(arquivo_path)
                logger.info(f"Arquivo {arquivo_path} modificado com sucesso")
                
        except Exception as e:
            logger.error(f"Erro ao modificar arquivo {arquivo_path}: {e}")
            
    return arquivos_modificados

def criar_script_sql():
    """Cria script SQL para limpar e desabilitar lançamentos automáticos"""
    sql_script = """
-- Script para limpar e desabilitar lançamentos financeiros automáticos

-- 1. Remover todos os lançamentos relacionados a propostas
DELETE FROM financeiro 
WHERE proposta_id IS NOT NULL
   OR descricao LIKE 'Proposta #%';

-- 2. Criar uma função SQL que sempre retorna TRUE para bloquear novos lançamentos
CREATE OR REPLACE FUNCTION ja_existe_lancamento_proposta(proposta_id_param INTEGER) 
RETURNS BOOLEAN AS $$
BEGIN
    -- Sempre retorna TRUE para bloquear criação de novos lançamentos
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- 3. Criar um trigger para impedir inserções com proposta_id
CREATE OR REPLACE FUNCTION bloquear_lancamento_proposta() 
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.proposta_id IS NOT NULL THEN
        RAISE NOTICE 'Tentativa de inserção de lançamento automático bloqueada para proposta %', NEW.proposta_id;
        RETURN NULL; -- Não permite a inserção
    END IF;
    
    -- Verificar pela descrição também
    IF NEW.descricao LIKE 'Proposta #%' THEN
        RAISE NOTICE 'Tentativa de inserção de lançamento automático bloqueada: %', NEW.descricao;
        RETURN NULL; -- Não permite a inserção
    END IF;
    
    RETURN NEW; -- Permite outros lançamentos
END;
$$ LANGUAGE plpgsql;

-- Verificar se o trigger já existe antes de criar
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'impedir_lancamento_proposta'
    ) THEN
        CREATE TRIGGER impedir_lancamento_proposta
        BEFORE INSERT ON financeiro
        FOR EACH ROW
        EXECUTE FUNCTION bloquear_lancamento_proposta();
    END IF;
END $$;
"""
    
    try:
        with open('desativar_lancamentos_automaticos.sql', 'w') as f:
            f.write(sql_script)
        logger.info("Script SQL criado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar script SQL: {e}")
        return False

def executar_script_sql():
    """Executa o script SQL para limpar e desabilitar lançamentos automaticamente"""
    conn = get_db_connection()
    if not conn:
        return False, "Erro ao conectar ao banco de dados"
    
    try:
        cursor = conn.cursor()
        
        # Ler o script SQL
        with open('desativar_lancamentos_automaticos.sql', 'r') as f:
            sql = f.read()
            
        # Executar script
        cursor.execute(sql)
        conn.commit()
        
        return True, "Script SQL executado com sucesso"
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao executar script SQL: {e}")
        return False, f"Erro ao executar script SQL: {e}"
    finally:
        if conn:
            if 'cursor' in locals() and cursor:
                cursor.close()
            conn.close()

def main():
    """Função principal"""
    print("=== REMOVENDO TODOS OS LANÇAMENTOS FINANCEIROS AUTOMÁTICOS ===")
    
    # 1. Excluir todos os lançamentos existentes
    print("\n1. Excluindo lançamentos financeiros automáticos existentes...")
    sucesso, mensagem = excluir_todos_lancamentos_automaticos()
    if sucesso:
        print(f"✅ {mensagem}")
    else:
        print(f"❌ {mensagem}")
    
    # 2. Criar script SQL
    print("\n2. Criando script SQL para bloquear novos lançamentos...")
    if criar_script_sql():
        print("✅ Script SQL criado com sucesso")
    else:
        print("❌ Erro ao criar script SQL")
    
    # 3. Executar script SQL
    print("\n3. Executando script SQL...")
    sucesso, mensagem = executar_script_sql()
    if sucesso:
        print(f"✅ {mensagem}")
    else:
        print(f"❌ {mensagem}")
    
    # 4. Desativar geração de lançamentos no código
    print("\n4. Desativando geração de lançamentos no código...")
    arquivos_modificados = desativar_geracao_lancamentos()
    
    if arquivos_modificados:
        print("✅ Arquivos modificados com sucesso:")
        for arquivo in arquivos_modificados:
            print(f"  - {arquivo} (backup em {arquivo}.bak)")
    else:
        print("❌ Nenhum arquivo modificado")
    
    print("\n=== CONCLUSÃO ===")
    if sucesso and arquivos_modificados:
        print("✅ TODOS OS LANÇAMENTOS FINANCEIROS AUTOMÁTICOS FORAM REMOVIDOS E DESATIVADOS")
        print("✅ Novas propostas NÃO gerarão lançamentos financeiros automáticos")
    else:
        print("⚠️ Processo concluído com alertas. Verifique as mensagens acima.")

if __name__ == "__main__":
    main()