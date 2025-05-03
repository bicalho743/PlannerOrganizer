"""
Script para aplicar a correção do erro de lançamentos duplicados
Este script modifica diretamente os arquivos necessários para corrigir o problema.
"""
import os
import logging
import psycopg2

# Configurar logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verificar_arquivo(caminho):
    """Verifica se um arquivo existe"""
    return os.path.exists(caminho)

def ler_arquivo(caminho):
    """Lê o conteúdo de um arquivo"""
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Erro ao ler arquivo {caminho}: {e}")
        return None

def escrever_arquivo(caminho, conteudo):
    """Escreve conteúdo em um arquivo"""
    try:
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        return True
    except Exception as e:
        logger.error(f"Erro ao escrever no arquivo {caminho}: {e}")
        return False

def fazer_backup(caminho):
    """Cria um backup do arquivo"""
    try:
        conteudo = ler_arquivo(caminho)
        if conteudo:
            backup_path = f"{caminho}.bak"
            escrever_arquivo(backup_path, conteudo)
            logger.info(f"Backup criado em {backup_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Erro ao fazer backup do arquivo {caminho}: {e}")
        return False

def localizar_arquivo_finalizar_proposta():
    """Localiza o arquivo com a função finalizar_proposta"""
    possiveis_locais = [
        "utils/proposta.py",
        "utils/financeiro.py",
        "utils/finalizar_proposta.py",
        "pages/propostas.py"
    ]
    
    for arquivo in possiveis_locais:
        if verificar_arquivo(arquivo):
            conteudo = ler_arquivo(arquivo)
            if conteudo and ("def finalizar_proposta" in conteudo or 
                            "def finalizar_proposta_segura" in conteudo):
                return arquivo
    
    return None

def criar_funcao_sql():
    """Cria função SQL para verificar se já existe lançamento financeiro para uma proposta"""
    try:
        # Conectar ao banco de dados
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("Variável DATABASE_URL não encontrada")
            return False
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Criar função SQL
        sql = """
        CREATE OR REPLACE FUNCTION ja_existe_lancamento_proposta(proposta_id_param INTEGER) 
        RETURNS BOOLEAN AS $$
        DECLARE
            existe BOOLEAN;
        BEGIN
            SELECT EXISTS(
                SELECT 1 FROM financeiro 
                WHERE proposta_id = proposta_id_param
                AND tipo = 'receita_a_receber'
            ) INTO existe;
            
            RETURN existe;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        cursor.execute(sql)
        conn.commit()
        logger.info("Função SQL criada com sucesso")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao criar função SQL: {e}")
        return False

def modificar_funcao_finalizar(arquivo_path):
    """Modifica a função finalizar_proposta para verificar se já existe lançamento antes de criar"""
    if not verificar_arquivo(arquivo_path):
        logger.error(f"Arquivo {arquivo_path} não encontrado")
        return False
    
    conteudo = ler_arquivo(arquivo_path)
    if not conteudo:
        return False
    
    # Fazer backup antes de modificar
    fazer_backup(arquivo_path)
    
    # Verificar qual função estamos modificando
    if "def finalizar_proposta_segura" in conteudo:
        funcao_name = "finalizar_proposta_segura"
    else:
        funcao_name = "finalizar_proposta"
    
    logger.info(f"Modificando função {funcao_name} em {arquivo_path}")
    
    # Identificar o padrão usado para criar lançamentos financeiros
    if "adicionar_lancamento_financeiro" in conteudo:
        # Versão com função específica para adicionar lançamento
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
                while j < len(linhas) and ("cursor.execute" in linhas[j] or "RETURNING" in linhas[j]):
                    linhas[j] = indentacao + "    " + linhas[j].lstrip()
                    j += 1
                
                # Adicionar else após o bloco SQL
                linhas.insert(j, f"{indentacao}else:")
                linhas.insert(j+1, f"{indentacao}    logger.info(f\"Proposta #{{proposta_id}} já possui lançamento financeiro, não será criado outro\")")
                break
                
        novo_conteudo = '\n'.join(linhas)
    else:
        logger.error(f"Não foi possível identificar o padrão para modificar em {arquivo_path}")
        return False
    
    # Garantir que o módulo logging esteja importado
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
    
    # Salvar as alterações
    if escrever_arquivo(arquivo_path, novo_conteudo):
        logger.info(f"Arquivo {arquivo_path} modificado com sucesso")
        return True
    else:
        logger.error(f"Erro ao modificar arquivo {arquivo_path}")
        return False

def main():
    """Função principal"""
    print("Iniciando correção para evitar lançamentos duplicados na finalização...")
    
    # 1. Criar função SQL para verificar se já existe lançamento
    print("Criando função SQL de verificação...")
    if criar_funcao_sql():
        print("✅ Função SQL criada com sucesso")
    else:
        print("❌ Erro ao criar função SQL")
        return False
    
    # 2. Localizar arquivo com função finalizar_proposta
    print("Localizando arquivo com função de finalização...")
    arquivo_finalizar = localizar_arquivo_finalizar_proposta()
    if not arquivo_finalizar:
        print("❌ Não foi possível localizar o arquivo com a função de finalização")
        
        # Solicitar caminho manual
        arquivo_finalizar = input("Por favor, informe o caminho do arquivo que contém a função finalizar_proposta: ")
        if not arquivo_finalizar or not verificar_arquivo(arquivo_finalizar):
            print("❌ Arquivo não encontrado")
            return False
    else:
        print(f"✅ Arquivo encontrado: {arquivo_finalizar}")
    
    # 3. Modificar código para não criar lançamento na finalização
    print("Modificando código de finalização...")
    if modificar_funcao_finalizar(arquivo_finalizar):
        print("✅ Código modificado com sucesso")
        print("\n⭐ CORREÇÃO APLICADA COM SUCESSO! ⭐")
        print(f"Backup do arquivo original em: {arquivo_finalizar}.bak")
        print("Agora o sistema não criará lançamentos duplicados na finalização de propostas.")
        return True
    else:
        print("❌ Erro ao modificar código")
        return False

if __name__ == "__main__":
    main()