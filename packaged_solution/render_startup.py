"""
Script de inicialização automática para o ambiente Render
Este script é executado automaticamente quando a aplicação é iniciada no Render
e aplica todas as correções necessárias para o funcionamento correto no ambiente.
"""
import os
import sys
import logging
import datetime
import time
from pathlib import Path

# Configurar logging
LOG_FILE = "render_startup.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def log_message(message, level='info'):
    """Registra uma mensagem no log e imprime no console"""
    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")
    if level.lower() == 'info':
        logger.info(message)
    elif level.lower() == 'error':
        logger.error(message)
    elif level.lower() == 'warning':
        logger.warning(message)

def is_render_environment():
    """Verifica se o script está sendo executado no ambiente Render"""
    return os.environ.get('RENDER') == 'true'

def apply_database_fixes():
    """Aplica correções no banco de dados"""
    try:
        # Importar e executar o script de correções no banco de dados
        log_message("Aplicando correções no banco de dados...")
        
        # Método 1: Importar como módulo
        try:
            import fix_render_type_errors
            fix_render_type_errors.main()
            log_message("Correções no banco de dados aplicadas com sucesso (via módulo)")
            return True
        except ImportError:
            log_message("Módulo fix_render_type_errors não encontrado, tentando executar diretamente", 'warning')
        except Exception as e:
            log_message(f"Erro ao aplicar correções via módulo: {str(e)}", 'error')
        
        # Método 2: Executar como script separado
        try:
            log_message("Tentando executar script fix_render_type_errors.py diretamente...")
            if os.path.exists('fix_render_type_errors.py'):
                result = os.system('python fix_render_type_errors.py')
                if result == 0:
                    log_message("Correções no banco de dados aplicadas com sucesso (via script)")
                    return True
                else:
                    log_message(f"Erro ao executar script fix_render_type_errors.py: código {result}", 'error')
            else:
                log_message("Arquivo fix_render_type_errors.py não encontrado", 'error')
        except Exception as e:
            log_message(f"Erro ao executar script fix_render_type_errors.py: {str(e)}", 'error')
        
        return False
    except Exception as e:
        log_message(f"Erro ao aplicar correções no banco de dados: {str(e)}", 'error')
        return False

def apply_code_fixes():
    """Aplica correções no código"""
    try:
        # Aplicar correções no código
        log_message("Aplicando correções no código...")
        
        # Método 1: Importar como módulo
        try:
            import modifica_propostas
            result = modifica_propostas.modificar_arquivo_propostas()
            if result:
                log_message("Correções no código aplicadas com sucesso (via módulo)")
                return True
            else:
                log_message("Falha ao aplicar correções no código via módulo", 'warning')
        except ImportError:
            log_message("Módulo modifica_propostas não encontrado, tentando executar diretamente", 'warning')
        except Exception as e:
            log_message(f"Erro ao aplicar correções via módulo: {str(e)}", 'error')
        
        # Método 2: Executar como script separado
        try:
            log_message("Tentando executar script modifica_propostas.py diretamente...")
            if os.path.exists('modifica_propostas.py'):
                result = os.system('python modifica_propostas.py')
                if result == 0:
                    log_message("Correções no código aplicadas com sucesso (via script)")
                    return True
                else:
                    log_message(f"Erro ao executar script modifica_propostas.py: código {result}", 'error')
            else:
                log_message("Arquivo modifica_propostas.py não encontrado", 'error')
        except Exception as e:
            log_message(f"Erro ao executar script modifica_propostas.py: {str(e)}", 'error')
        
        return False
    except Exception as e:
        log_message(f"Erro ao aplicar correções no código: {str(e)}", 'error')
        return False

def verify_environment():
    """Verifica o ambiente e suas configurações"""
    try:
        log_message("Verificando ambiente...")
        
        # Verificar variáveis de ambiente
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            log_message("Variável de ambiente DATABASE_URL não encontrada", 'error')
        else:
            log_message("Variável de ambiente DATABASE_URL encontrada")
        
        # Verificar arquivos necessários
        utils_dir = Path('utils')
        if not utils_dir.exists():
            log_message("Diretório utils/ não encontrado", 'error')
        else:
            log_message("Diretório utils/ encontrado")
        
        fix_module = utils_dir / 'finalizar_proposta_fix.py'
        if not fix_module.exists():
            log_message("Arquivo utils/finalizar_proposta_fix.py não encontrado", 'error')
        else:
            log_message("Arquivo utils/finalizar_proposta_fix.py encontrado")
        
        pages_dir = Path('pages')
        if not pages_dir.exists():
            log_message("Diretório pages/ não encontrado", 'error')
        else:
            log_message("Diretório pages/ encontrado")
        
        propostas_file = pages_dir / 'propostas.py'
        if not propostas_file.exists():
            log_message("Arquivo pages/propostas.py não encontrado", 'error')
        else:
            log_message("Arquivo pages/propostas.py encontrado")
        
        log_message("Verificação de ambiente concluída")
    except Exception as e:
        log_message(f"Erro ao verificar ambiente: {str(e)}", 'error')

def main():
    """Função principal"""
    start_time = time.time()
    
    log_message("\n" + "="*60)
    log_message("INICIANDO CORREÇÕES AUTOMÁTICAS PARA O AMBIENTE RENDER")
    log_message("="*60 + "\n")
    
    # Verificar se estamos no ambiente Render
    if not is_render_environment():
        log_message("Este script deve ser executado apenas no ambiente Render.", 'warning')
        log_message("Executando mesmo assim para fins de teste...")
    
    # Verificar ambiente
    verify_environment()
    
    # Aplicar correções no banco de dados
    db_success = apply_database_fixes()
    
    # Aplicar correções no código
    code_success = apply_code_fixes()
    
    # Verificar resultado final
    if db_success and code_success:
        log_message("\n" + "="*60)
        log_message("TODAS AS CORREÇÕES FORAM APLICADAS COM SUCESSO")
        log_message("="*60 + "\n")
    else:
        log_message("\n" + "="*60)
        log_message("ATENÇÃO: ALGUMAS CORREÇÕES FALHARAM", 'error')
        log_message("Por favor, verifique o log para mais detalhes")
        log_message("="*60 + "\n")
    
    end_time = time.time()
    duration = end_time - start_time
    log_message(f"Tempo total de execução: {duration:.2f} segundos")
    
    return db_success and code_success

if __name__ == "__main__":
    main()