"""
Versão super simplificada da recuperação de senha
Focada apenas na funcionalidade de enviar o email de recuperação
"""
import streamlit as st
import os

# Configuração básica da página
st.set_page_config(
    page_title="Recuperar Senha",
    page_icon="🔑",
    layout="centered"
)

# Estilo CSS minimalista
st.markdown("""
<style>
.main-container {
    max-width: 500px;
    margin: 0 auto;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    background-color: white;
}
.title {
    color: #2557D6;
    text-align: center;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# Firebase - apenas configuração e função de reset
st.markdown("""
<script src="https://www.gstatic.com/firebasejs/9.6.10/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.6.10/firebase-auth-compat.js"></script>

<script>
// Configuração do Firebase
const firebaseConfig = {
  apiKey: "%s",
  authDomain: "planner-organizer-68a23.firebaseapp.com",
  projectId: "planner-organizer-68a23",
  storageBucket: "planner-organizer-68a23.appspot.com",
  messagingSenderId: "763383033284",
  appId: "1:763383033284:web:5a5dc3b4d3f5bc63631ce7"
};

// Inicializar Firebase
firebase.initializeApp(firebaseConfig);

// Função para enviar email de recuperação de senha
function resetPassword(email) {
  firebase.auth().sendPasswordResetEmail(email)
    .then(() => {
      // Sucesso - criar um elemento para comunicar com Streamlit
      const successElement = document.createElement('div');
      successElement.id = 'password-reset-success';
      successElement.textContent = email;
      document.body.appendChild(successElement);
      
      // Alertar o usuário
      alert('Email de recuperação enviado com sucesso para ' + email);
    })
    .catch((error) => {
      // Erro - criar um elemento para comunicar com Streamlit
      const errorElement = document.createElement('div');
      errorElement.id = 'password-reset-error';
      errorElement.textContent = error.message;
      document.body.appendChild(errorElement);
      
      // Alertar o usuário sobre o erro
      alert('Erro: ' + error.message);
    });
}

// Função para ser chamada pelo botão
window.sendPasswordReset = function() {
  const emailInput = document.getElementById('reset-email');
  if (emailInput && emailInput.value) {
    resetPassword(emailInput.value);
  } else {
    alert('Por favor, insira um email válido.');
  }
};
</script>
""" % (os.environ.get("FIREBASE_API_KEY") or "AIzaSyAVDx4NuQQbWzxdqEb1-4c9Xc2uyHntG0E"), unsafe_allow_html=True)

# Título da página
st.markdown("<h1 class='title'>Recuperação de Senha</h1>", unsafe_allow_html=True)

# Container principal
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

# Formulário de recuperação de senha
st.markdown("""
<p style="margin-bottom: 20px;">
    Informe seu email cadastrado abaixo para receber um link de recuperação de senha.
</p>

<div style="margin-bottom: 15px;">
    <label for="reset-email" style="display: block; margin-bottom: 5px; font-weight: 500;">Email</label>
    <input type="email" id="reset-email" placeholder="seu.email@exemplo.com" 
           style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
</div>

<button onclick="window.sendPasswordReset()" 
        style="width: 100%; padding: 10px 15px; background-color: #2557D6; color: white; 
               border: none; border-radius: 4px; cursor: pointer; font-weight: 500;">
    Enviar Link de Recuperação
</button>

<div style="margin-top: 20px; text-align: center;">
    <a href="/" style="color: #2557D6; text-decoration: none;">Voltar para o login</a>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Componente para verificar o resultado da operação
result_placeholder = st.empty()

# Rodapé
st.markdown("""
<div style="text-align: center; margin-top: 30px; color: #666; font-size: 0.8rem;">
    © 2025 Planner Organizer. Todos os direitos reservados.
</div>
""", unsafe_allow_html=True)