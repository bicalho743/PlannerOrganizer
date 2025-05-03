"""
Script simples para remover a criação de lançamento financeiro na finalização da proposta.
Este script modifica apenas a função de finalização de proposta.
"""

import os
import psycopg2
import logging
from datetime import datetime

# Configuração de logging
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

def localizar_arquivo_finalizar_proposta():
    """Tenta localizar o arquivo que contém a função finalizar_proposta"""
    possiveis_locais = [
        "utils/proposta.py",
        "utils/financeiro.py",
        "utils/finalizar_proposta.py",
        "pages/propostas.py"
    ]
    
    for local in possiveis_locais:
        if os.path.exists(local):
            try:
                with open(local, 'r') as f:
                    conteudo = f.read()
                    if "def finalizar_proposta" in conteudo or "def finalizar_proposta_segura" in conteudo:
                        return local
            except Exception as e:
                logger.error(f"Erro ao ler arquivo {local}: {e}")
    
    return None

def verificar_ja_existe_funcao():
    """Cria função SQL para verificar se já existe lançamento para a proposta"""
    conn = get_db_connection()
    if not conn:
        return False, "Erro ao conectar ao banco de dados"
    
    try:
        cursor = conn.cursor()
        
        # Criar função SQL para verificar se já existe lançamento para a proposta
        cursor.execute("""
            CREATE OR REPLACE FUNCTION ja_existe_lancamento_proposta(proposta_id_param INTEGER)
            RETURNS BOOLEAN AS $$
            DECLARE
                existe BOOLEAN;
            BEGIN
                SELECT EXISTS (
                    SELECT 1 FROM financeiro
                    WHERE proposta_id = proposta_id_param
                    AND tipo = 'receita_a_receber'
                ) INTO existe;
                
                RETURN existe;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        conn.commit()
        return True, "Função de verificação criada com sucesso"
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao criar função SQL: {e}")
        return False, f"Erro ao criar função SQL: {e}"
    finally:
        if conn:
            if 'cursor' in locals() and cursor:
                cursor.close()
            conn.close()

def modificar_codigo_finalizar(arquivo_path):
    """Modifica o código da função finalizar_proposta para não criar lançamento financeiro na finalização"""
    if not os.path.exists(arquivo_path):
        return False, f"Arquivo {arquivo_path} não encontrado"
    
    try:
        with open(arquivo_path, 'r') as f:
            conteudo = f.read()
        
        # Fazer backup do arquivo original
        with open(f"{arquivo_path}.bak", 'w') as f:
            f.write(conteudo)
            
        # Verificar se existe a versão segura ou a normal
        if "def finalizar_proposta_segura" in conteudo:
            funcao_name = "finalizar_proposta_segura"
        else:
            funcao_name = "finalizar_proposta"
        
        # Localizar a parte que cria lançamentos financeiros
        if "adicionar_lancamento_financeiro" in conteudo:
            # Versão com função separada para adicionar lançamento
            # Substitui a chamada direta pela versão com verificação
            novo_conteudo = conteudo.replace(
                "adicionar_lancamento_financeiro(",
                "# Verificar se já existe lançamento para esta proposta\n" +
                "        cursor.execute(\"SELECT ja_existe_lancamento_proposta(%s)\", (proposta_id,))\n" +
                "        ja_existe = cursor.fetchone()[0]\n" +
                "        \n" +
                "        # Criar lançamento financeiro apenas se não existir\n" +
                "        if not ja_existe:\n" +
                "            adicionar_lancamento_financeiro("
            )
            
            # Adicionar indentação ao fechamento da condição if
            linhas = novo_conteudo.split('\n')
            for i, linha in enumerate(linhas):
                if "adicionar_lancamento_financeiro(" in linha:
                    # Encontrar a linha com o fechamento do parêntese
                    j = i
                    parenteses = 1
                    while j < len(linhas) and parenteses > 0:
                        j += 1
                        if j < len(linhas):
                            linha_atual = linhas[j]
                            parenteses += linha_atual.count('(')
                            parenteses -= linha_atual.count(')')
                    
                    if j < len(linhas):
                        # Adicionar else após o fechamento do parêntese
                        linhas[j] = linhas[j] + "\n        else:\n            logger.info(f\"Proposta #{proposta_id} já possui lançamento financeiro, não será criado outro\")"
                        break
                        
            novo_conteudo = '\n'.join(linhas)
        elif "INSERT INTO financeiro" in conteudo:
            # Versão com SQL direto para adicionar lançamento
            # Envolve o bloco de código SQL em uma verificação
            linhas = conteudo.split('\n')
            for i, linha in enumerate(linhas):
                if "INSERT INTO financeiro" in linha:
                    # Encontrar o início do bloco SQL
                    inicio = i
                    # Voltar até encontrar o início do bloco
                    while inicio > 0 and "cursor.execute" not in linhas[inicio]:
                        inicio -= 1
                    
                    # Adicionar a verificação antes do INSERT
                    indentacao = linhas[inicio][:linhas[inicio].find("cursor")]
                    linhas.insert(inicio, f"{indentacao}# Verificar se já existe lançamento para esta proposta")
                    linhas.insert(inicio+1, f"{indentacao}cursor.execute(\"SELECT ja_existe_lancamento_proposta(%s)\", (proposta_id,))")
                    linhas.insert(inicio+2, f"{indentacao}ja_existe = cursor.fetchone()[0]")
                    linhas.insert(inicio+3, f"{indentacao}")
                    linhas.insert(inicio+4, f"{indentacao}# Criar lançamento financeiro apenas se não existir")
                    linhas.insert(inicio+5, f"{indentacao}if not ja_existe:")
                    
                    # Adicionar indentação ao bloco SQL existente
                    j = inicio + 6
                    while j < len(linhas) and "cursor.execute" in linhas[j] or "RETURNING" in linhas[j]:
                        linhas[j] = indentacao + "    " + linhas[j].lstrip()
                        j += 1
                    
                    # Adicionar else após o bloco SQL
                    linhas.insert(j, f"{indentacao}else:")
                    linhas.insert(j+1, f"{indentacao}    logger.info(f\"Proposta #{{proposta_id}} já possui lançamento financeiro, não será criado outro\")")
                    break
                    
            novo_conteudo = '\n'.join(linhas)
        else:
            return False, f"Não foi possível identificar o padrão de criação de lançamentos financeiros no arquivo {arquivo_path}"
        
        # Verificar se é necessário importar o módulo logging
        if "import logging" not in novo_conteudo:
            import_pos = novo_conteudo.find("import ")
            if import_pos >= 0:
                # Encontrar o final do bloco de importações
                linhas = novo_conteudo.split('\n')
                ultima_importacao = 0
                for i, linha in enumerate(linhas):
                    if linha.startswith("import ") or linha.startswith("from "):
                        ultima_importacao = i
                
                # Adicionar import logging após a última importação
                linhas.insert(ultima_importacao + 1, "import logging")
                linhas.insert(ultima_importacao + 2, "logger = logging.getLogger(__name__)")
                novo_conteudo = '\n'.join(linhas)
            else:
                # Adicionar no início do arquivo
                novo_conteudo = "import logging\nlogger = logging.getLogger(__name__)\n\n" + novo_conteudo
        
        # Salvar o arquivo modificado
        with open(arquivo_path, 'w') as f:
            f.write(novo_conteudo)
        
        return True, f"Arquivo {arquivo_path} modificado com sucesso"
    except Exception as e:
        logger.error(f"Erro ao modificar arquivo {arquivo_path}: {e}")
        return False, f"Erro ao modificar arquivo {arquivo_path}: {e}"

def main():
    """Função principal"""
    print("Iniciando processo para remover criação de lançamento financeiro na finalização da proposta...")
    
    # 1. Criar função SQL para verificar se já existe lançamento
    sucesso, mensagem = verificar_ja_existe_funcao()
    if not sucesso:
        print(f"❌ {mensagem}")
        return
    else:
        print(f"✅ {mensagem}")
    
    # 2. Localizar arquivo com função finalizar_proposta
    arquivo_finalizar = localizar_arquivo_finalizar_proposta()
    if not arquivo_finalizar:
        print("❌ Não foi possível localizar o arquivo com a função finalizar_proposta")
        
        # Solicitar caminho manual
        arquivo_finalizar = input("Por favor, informe o caminho do arquivo que contém a função finalizar_proposta: ")
        if not arquivo_finalizar or not os.path.exists(arquivo_finalizar):
            print("❌ Arquivo não encontrado")
            return
    
    # 3. Modificar código para não criar lançamento na finalização
    sucesso, mensagem = modificar_codigo_finalizar(arquivo_finalizar)
    if sucesso:
        print(f"✅ {mensagem}")
        print(f"\nArquivo original salvo como {arquivo_finalizar}.bak")
        print("Agora o sistema não criará lançamentos financeiros duplicados na finalização de propostas!")
    else:
        print(f"❌ {mensagem}")

if __name__ == "__main__":
    main()