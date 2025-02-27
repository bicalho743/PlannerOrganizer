import streamlit as st
import random

CELEBRATION_MESSAGES = [
    "🎉 Parabéns! Mais uma conquista alcançada!",
    "⭐ Excelente trabalho! Continue assim!",
    "🌟 Você está arrasando! Muito bem!",
    "🎯 Meta alcançada com sucesso!",
    "🏆 Mais uma vitória no seu histórico!",
    "✨ Incrível! Você fez acontecer!"
]

CELEBRATION_GIFS = [
    "https://media.giphy.com/media/3oz8xAFtqoOUUrsh7W/giphy.gif",
    "https://media.giphy.com/media/g9582DNuQppxC/giphy.gif",
    "https://media.giphy.com/media/26u4cqiYI30juCOGY/giphy.gif",
    "https://media.giphy.com/media/xT0BKBOzy7ASIA82ZO/giphy.gif",
    "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif"
]

def show_celebration(task_name=None, custom_message=None):
    """
    Exibe uma tela de celebração personalizada.
    
    Args:
        task_name (str, optional): Nome da tarefa concluída
        custom_message (str, optional): Mensagem personalizada para exibir
    """
    message = custom_message or random.choice(CELEBRATION_MESSAGES)
    gif_url = random.choice(CELEBRATION_GIFS)
    
    # Container para centralizar o conteúdo
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Título da celebração
            if task_name:
                st.markdown(f"### ✅ {task_name}")
            
            # Mensagem de celebração
            st.markdown(f"## {message}")
            
            # GIF de celebração
            st.markdown(
                f'<div style="display: flex; justify-content: center;"><img src="{gif_url}" width="300"></div>',
                unsafe_allow_html=True
            )
            
            # Botão para continuar
            if st.button("🎯 Continuar", key="celebration_continue"):
                st.session_state.show_celebration = False
                st.rerun()

def toggle_celebration(show=True, task_name=None, custom_message=None):
    """
    Ativa ou desativa a exibição da tela de celebração.
    
    Args:
        show (bool): Se True, mostra a celebração
        task_name (str, optional): Nome da tarefa concluída
        custom_message (str, optional): Mensagem personalizada
    """
    if show:
        st.session_state.show_celebration = True
        st.session_state.celebration_task = task_name
        st.session_state.celebration_message = custom_message
    else:
        st.session_state.show_celebration = False
        st.session_state.celebration_task = None
        st.session_state.celebration_message = None
