"""
Script para automatizar a modificação do arquivo pages/propostas.py no Render
Este script deve ser executado diretamente no ambiente Render.
"""
import os
import re

def modificar_arquivo_propostas():
    """
    Modifica o arquivo pages/propostas.py para utilizar a função finalizar_proposta_sql
    do módulo utils.finalizar_proposta_fix
    """
    arquivo = 'pages/propostas.py'
    
    # Verificar se o arquivo existe
    if not os.path.exists(arquivo):
        print(f"ERRO: Arquivo {arquivo} não encontrado")
        return False
    
    # Fazer backup do arquivo original
    backup = arquivo + '.bak'
    try:
        with open(arquivo, 'r') as f_in:
            conteudo_original = f_in.read()
            
        with open(backup, 'w') as f_out:
            f_out.write(conteudo_original)
            
        print(f"Backup criado em {backup}")
    except Exception as e:
        print(f"ERRO ao criar backup: {str(e)}")
        return False
    
    # Modificar o conteúdo
    try:
        # Adicionar import
        import_pattern = r'(import streamlit as st\n)'
        import_replacement = r'\1from utils.finalizar_proposta_fix import finalizar_proposta_sql\n'
        
        conteudo_modificado = re.sub(import_pattern, import_replacement, conteudo_original)
        
        # Substituir código de finalização por nova função
        # Padrão para buscar o botão "Finalizar Proposta"
        botao_pattern = r'(if st\.button\("✅ Finalizar Proposta", key=f"finalizar_\{proposta_id\}"\):.*?)(st\.experimental_rerun\(\))'
        
        # Novo código para finalização usando finalizar_proposta_sql
        botao_replacement = r'''if st.button("✅ Finalizar Proposta", key=f"finalizar_{proposta_id}"):
            with st.spinner("Finalizando proposta..."):
                sucesso, mensagem = finalizar_proposta_sql(proposta_id, st.session_state.user_info.get('localId'))
                if sucesso:
                    st.success(mensagem)
                    time.sleep(1)
                    \2
                else:
                    st.error(mensagem)'''
        
        # Aplicar substituição, tratando múltiplas linhas com re.DOTALL
        conteudo_modificado = re.sub(botao_pattern, botao_replacement, conteudo_modificado, flags=re.DOTALL)
        
        # Se não encontrou com o padrão exato, tentar um mais genérico
        if conteudo_modificado == conteudo_original:
            print("Padrão exato não encontrado, tentando um mais genérico...")
            
            # Buscar apenas o botão e substituir por versão completa
            botao_pattern = r'if st\.button\("✅ Finalizar Proposta", key=f"finalizar_\{proposta_id\}"\):'
            
            # Verificar se o padrão existe
            if re.search(botao_pattern, conteudo_original):
                print("Padrão genérico encontrado, procedendo com substituição...")
                
                # Novo código para finalização (versão mais genérica)
                botao_replacement = r'''if st.button("✅ Finalizar Proposta", key=f"finalizar_{proposta_id}"):
            with st.spinner("Finalizando proposta..."):
                sucesso, mensagem = finalizar_proposta_sql(proposta_id, st.session_state.user_info.get('localId'))
                if sucesso:
                    st.success(mensagem)
                    time.sleep(1)
                    st.experimental_rerun()  # Recarregar a página para mostrar as mudanças
                else:
                    st.error(mensagem)'''
                
                # Substituir o botão
                conteudo_modificado = re.sub(botao_pattern, botao_replacement, conteudo_original)
            else:
                print("AVISO: Padrão de botão não encontrado")
                return False
        
        # Escrever arquivo modificado
        with open(arquivo, 'w') as f_out:
            f_out.write(conteudo_modificado)
            
        print(f"Arquivo {arquivo} modificado com sucesso")
        return True
    except Exception as e:
        print(f"ERRO ao modificar arquivo: {str(e)}")
        
        # Restaurar backup em caso de erro
        try:
            with open(backup, 'r') as f_in:
                with open(arquivo, 'w') as f_out:
                    f_out.write(f_in.read())
            print(f"Backup restaurado de {backup}")
        except Exception as backup_error:
            print(f"ERRO ao restaurar backup: {str(backup_error)}")
            
        return False

if __name__ == "__main__":
    print("Iniciando modificação do arquivo propostas.py...")
    resultado = modificar_arquivo_propostas()
    if resultado:
        print("Modificação concluída com sucesso!")
    else:
        print("Modificação não concluída. Verifique os erros acima.")