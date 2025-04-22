// Função para inicializar firebase e autenticação com Google
function initializeFirebaseAuth(apiKey, authDomain, projectId) {
  // Inicializa o Firebase
  const firebaseConfig = {
    apiKey: apiKey,
    authDomain: authDomain,
    projectId: projectId,
  };

  // Inicializar Firebase
  firebase.initializeApp(firebaseConfig);

  // Referência ao provedor Google
  const provider = new firebase.auth.GoogleAuthProvider();

  // Configuração para popup
  provider.setCustomParameters({
    prompt: 'select_account'
  });

  return {
    signInWithGoogle: function() {
      firebase.auth().signInWithPopup(provider)
        .then((result) => {
          // Usuário logado com sucesso
          const user = result.user;
          // Obter token de ID
          user.getIdToken().then((idToken) => {
            // Enviar token para Streamlit via parâmetros de URL
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('auth_provider', 'google');
            currentUrl.searchParams.set('id_token', idToken);
            
            // Redirecionar para a URL atualizada
            window.location.href = currentUrl.toString();
          });
        }).catch((error) => {
          console.error("Erro na autenticação com Google:", error);
          alert("Erro na autenticação com Google: " + error.message);
        });
    }
  };
}