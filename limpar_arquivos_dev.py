"""
Script para limpar arquivos de desenvolvimento e ferramentas de diagnóstico
"""
import os
import shutil
import logging
import streamlit as st
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LimpadorArquivos:
    def __init__(self):
        """Inicializa o limpador de arquivos"""
        # Diretório para backup
        self.diretorio_backup = "backup_arquivos_dev_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Lista de arquivos que não são necessários em produção
        self.arquivos_para_excluir = [
            # Ferramentas de diagnóstico e correção
            'diagnostico_banco.py',
            'correcao_banco.py',
            'corrigir_cache_interface.sql',
            'corrigir_erro_finalizacao.py',
            'corrigir_finalizacao.py',
            'corrigir_propostas_render.py',
            'corrigir_propostas_streamlit.py',
            'check_database.py',
            'check_port.py',
            'disable_debug.py',
            'fix_render_database.sql',
            'fix_render_database_query.py',
            'fix_render_direct.zip',
            'fix_render_direto.zip',
            'fix_render_final.base64',
            'fix_render_final.zip',
            'fix_render_final.zip.check',
            'fix_render_imports.js',
            'fix_render_proposta_sql.sql',
            'fix_render_schema.py',
            'fix_render_type_errors.py',
            
            # Ferramentas de importação/limpeza
            'importacao_direta.py',
            'importar_clientes.py',
            'importar_propostas.py',
            'importar_propostas_v2.py',
            'limpar_clientes.py',
            'limpar_propostas.py',
            'limpar_vendas.py',
            'excluir_venda_direto.py',
            'excluir_venda_simples.py',
            'excluir_vendas_standalone.py',
            'teste_importacao.py',
            
            # Ferramentas de correção específicas
            'ajustar_data_proposta.py',
            'aplicar_correcao_finalizar.py',
            'atualizar_categorias_financeiro.py',
            'create_deployment_zip.py',
            'download_alteracoes.py',
            'download_finalizacao_fix.py',
            'download_fix_direct.py',
            'download_fix_direto.py',
            'download_fix_duplicate_proposal_entries.py',
            'download_fix_duplicated_entries.py',
            'download_fix_financial_entries.py',
            'download_fix_lancamentos.py',
            'download_fix_proposta.py',
            'download_fix_render_console.py',
            'download_fix_render_db.py',
            'download_fix_render_final.py',
            'download_fix_standalone.py',
            'download_icons.py',
            'download_pacote_render.py',
            'download_raw.html',
            'download_render_fix.py',
            'download_solucao_final.py',
            'download_solucao_render.py',
            'examinar_tabela_propostas.py',
            'finalizar_proposta_direto.py',
            
            # Diretórios temporários e de backup
            'backup_files',
            'backups',
            'solucao_render',
            'temp_files',
            'deploy_render',
            'downloads',
            'packaged_solution'
        ]
    
    def criar_backup(self):
        """Cria backup dos arquivos antes de removê-los"""
        try:
            # Criar diretório de backup
            os.makedirs(self.diretorio_backup, exist_ok=True)
            logger.info(f"Diretório de backup criado: {self.diretorio_backup}")
            
            # Copiar arquivos para o backup
            arquivos_copiados = 0
            for arquivo in self.arquivos_para_excluir:
                if os.path.exists(arquivo):
                    destino = os.path.join(self.diretorio_backup, arquivo)
                    
                    # Criar estrutura de diretórios necessária
                    if not os.path.exists(os.path.dirname(destino)) and os.path.dirname(destino):
                        os.makedirs(os.path.dirname(destino), exist_ok=True)
                    
                    # Copiar arquivo ou diretório
                    if os.path.isdir(arquivo):
                        shutil.copytree(arquivo, destino, dirs_exist_ok=True)
                    else:
                        shutil.copy2(arquivo, destino)
                    
                    arquivos_copiados += 1
                    logger.info(f"Backup criado: {arquivo}")
            
            logger.info(f"Total de {arquivos_copiados} arquivos/diretórios com backup criado")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            return False
    
    def remover_arquivos(self):
        """Remove os arquivos desnecessários para produção"""
        try:
            arquivos_removidos = 0
            for arquivo in self.arquivos_para_excluir:
                if os.path.exists(arquivo):
                    # Remover arquivo ou diretório
                    if os.path.isdir(arquivo):
                        shutil.rmtree(arquivo)
                    else:
                        os.remove(arquivo)
                    
                    arquivos_removidos += 1
                    logger.info(f"Arquivo removido: {arquivo}")
            
            logger.info(f"Total de {arquivos_removidos} arquivos/diretórios removidos")
            return True
        except Exception as e:
            logger.error(f"Erro ao remover arquivos: {e}")
            return False
    
    def desativar_modo_desenvolvedor(self):
        """Desativa flags de modo desenvolvedor nos arquivos de configuração"""
        try:
            # Arquivos que podem conter flags de desenvolvimento
            arquivos_configuracao = [
                'app.py',
                'utils/config.py',
                'utils/database.py',
                'utils/auth.py',
                'utils/firebase_auth.py'
            ]
            
            arquivos_modificados = 0
            for arquivo in arquivos_configuracao:
                if os.path.exists(arquivo):
                    # Backup do arquivo original
                    backup_path = os.path.join(self.diretorio_backup, arquivo.replace('/', '_'))
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(arquivo, backup_path)
                    
                    # Ler conteúdo do arquivo
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                    
                    # Substituir flags de desenvolvimento
                    conteudo_modificado = conteudo
                    substituicoes = [
                        ('DEBUG = True', 'DEBUG = False'),
                        ('DESENVOLVIMENTO = True', 'DESENVOLVIMENTO = False'),
                        ('AMBIENTE_DEV = True', 'AMBIENTE_DEV = False'),
                        ('modo_teste = True', 'modo_teste = False'),
                        ('modo_dev = True', 'modo_dev = False'),
                        ('dev_mode = True', 'dev_mode = False'),
                        ('ambiente_desenvolvimento = True', 'ambiente_desenvolvimento = False'),
                        ('mostrar_ferramentas_dev = True', 'mostrar_ferramentas_dev = False')
                    ]
                    
                    for antigo, novo in substituicoes:
                        if antigo in conteudo:
                            conteudo_modificado = conteudo_modificado.replace(antigo, novo)
                    
                    # Salvar alterações se houve modificação
                    if conteudo != conteudo_modificado:
                        with open(arquivo, 'w', encoding='utf-8') as f:
                            f.write(conteudo_modificado)
                        
                        arquivos_modificados += 1
                        logger.info(f"Modo desenvolvedor desativado em: {arquivo}")
            
            logger.info(f"Total de {arquivos_modificados} arquivos com modo desenvolvedor desativado")
            return True
        except Exception as e:
            logger.error(f"Erro ao desativar modo desenvolvedor: {e}")
            return False
    
    def executar_limpeza(self):
        """Executa a limpeza completa dos arquivos"""
        # 1. Criar backup dos arquivos
        sucesso_backup = self.criar_backup()
        if not sucesso_backup:
            return False, "Falha ao criar backup dos arquivos"
        
        # 2. Desativar modo desenvolvedor
        sucesso_dev_mode = self.desativar_modo_desenvolvedor()
        if not sucesso_dev_mode:
            logger.warning("Falha ao desativar modo desenvolvedor")
            # Continuamos mesmo com falha
        
        # 3. Remover arquivos desnecessários
        sucesso_remocao = self.remover_arquivos()
        if not sucesso_remocao:
            return False, "Falha ao remover arquivos desnecessários"
        
        return True, f"Limpeza concluída com sucesso! Backup criado em {self.diretorio_backup}"

# Interface Streamlit
def main():
    st.set_page_config(
        page_title="Limpeza de Arquivos de Desenvolvimento",
        page_icon="🧹",
        layout="wide"
    )
    
    st.title("🧹 Limpeza de Arquivos de Desenvolvimento")
    
    st.markdown("""
    Este assistente irá limpar os arquivos de desenvolvimento e ferramentas de diagnóstico do sistema.
    
    ### O que será feito:
    
    1. **Backup dos arquivos** - Todos os arquivos serão copiados para um diretório de backup antes de serem removidos
    2. **Desativação do modo desenvolvedor** - Flags de desenvolvimento serão desativadas nos arquivos de configuração
    3. **Remoção de arquivos desnecessários** - Ferramentas de diagnóstico, importação e correção serão removidas
    
    ⚠️ **ATENÇÃO:** Este processo não pode ser desfeito automaticamente, mas os arquivos estarão disponíveis no backup.
    """)
    
    limpador = LimpadorArquivos()
    
    st.subheader("Arquivos que serão removidos:")
    
    # Mostrar lista de arquivos que serão removidos, agrupados por categoria
    categorias = {
        "Ferramentas de diagnóstico e correção": [a for a in limpador.arquivos_para_excluir if a.startswith(('diagnostico', 'correcao', 'corrigir', 'check', 'fix', 'disable'))],
        "Ferramentas de importação/limpeza": [a for a in limpador.arquivos_para_excluir if a.startswith(('importa', 'limpar', 'excluir', 'teste'))],
        "Ferramentas de correção específicas": [a for a in limpador.arquivos_para_excluir if a.startswith(('ajustar', 'aplicar', 'atualizar', 'create', 'download', 'examinar', 'finalizar'))],
        "Diretórios temporários e de backup": [a for a in limpador.arquivos_para_excluir if os.path.isdir(a) or a in ['backup_files', 'backups', 'solucao_render', 'temp_files', 'deploy_render', 'downloads', 'packaged_solution']]
    }
    
    # Pedir confirmação
    for categoria, arquivos in categorias.items():
        with st.expander(f"{categoria} ({len(arquivos)} itens)"):
            for arquivo in arquivos:
                if os.path.exists(arquivo):
                    st.text(f"✓ {arquivo}")
                else:
                    st.text(f"✗ {arquivo} (não encontrado)")
    
    if st.button("Iniciar Limpeza de Arquivos", type="primary"):
        with st.spinner("Limpando arquivos de desenvolvimento..."):
            sucesso, mensagem = limpador.executar_limpeza()
            
            if sucesso:
                st.success(mensagem)
                st.balloons()
            else:
                st.error(mensagem)

if __name__ == "__main__":
    main()