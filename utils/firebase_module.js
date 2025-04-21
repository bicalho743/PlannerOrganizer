// Módulo de integração Firebase para Streamlit
// Este arquivo deve ser carregado na aplicação web para habilitar a autenticação

// Inicializar o Firebase
function initializeFirebase(config) {
  // Verificar se o Firebase já foi inicializado
  if (!firebase.apps.length) {
    firebase.initializeApp(config);
    console.log("Firebase inicializado com sucesso");
  } else {
    console.log("Firebase já estava inicializado");
  }
  
  // Configurar provedores de autenticação
  const googleProvider = new firebase.auth.GoogleAuthProvider();
  const facebookProvider = new firebase.auth.FacebookAuthProvider();
  
  return {
    auth: firebase.auth(),
    googleProvider,
    facebookProvider
  };
}

// Autenticação com Google
function signInWithGoogle(auth, provider) {
  console.log("Iniciando login com Google");
  return auth.signInWithPopup(provider)
    .then((result) => {
      // O login foi bem-sucedido, retornar os dados do usuário
      const user = result.user;
      return user.getIdToken().then(idToken => {
        return {
          success: true,
          uid: user.uid,
          email: user.email,
          displayName: user.displayName,
          photoURL: user.photoURL,
          idToken: idToken
        };
      });
    })
    .catch((error) => {
      // O login falhou, retornar o erro
      console.error("Erro no login com Google:", error);
      return {
        success: false,
        errorCode: error.code,
        errorMessage: error.message
      };
    });
}

// Autenticação com Facebook
function signInWithFacebook(auth, provider) {
  console.log("Iniciando login com Facebook");
  return auth.signInWithPopup(provider)
    .then((result) => {
      // O login foi bem-sucedido, retornar os dados do usuário
      const user = result.user;
      return user.getIdToken().then(idToken => {
        return {
          success: true,
          uid: user.uid,
          email: user.email,
          displayName: user.displayName,
          photoURL: user.photoURL,
          idToken: idToken
        };
      });
    })
    .catch((error) => {
      // O login falhou, retornar o erro
      console.error("Erro no login com Facebook:", error);
      return {
        success: false,
        errorCode: error.code,
        errorMessage: error.message
      };
    });
}

// Salvar os dados do usuário no localStorage
function saveUserToLocalStorage(userData) {
  localStorage.setItem('firebase_user', JSON.stringify(userData));
  console.log("Dados do usuário salvos no localStorage");
}

// Verificar se o usuário já está autenticado
function checkUserAuthentication() {
  const userData = localStorage.getItem('firebase_user');
  if (userData) {
    try {
      return JSON.parse(userData);
    } catch (e) {
      console.error("Erro ao analisar dados do usuário:", e);
      localStorage.removeItem('firebase_user');
    }
  }
  return null;
}

// Redirecionar após autenticação
function redirectAfterAuth(userData) {
  // Adicionar parâmetros à URL
  const currentUrl = new URL(window.location.href);
  currentUrl.searchParams.set('login_success', 'true');
  currentUrl.searchParams.set('uid', userData.uid);
  currentUrl.searchParams.set('email', userData.email);
  
  // Redirecionar
  window.location.href = currentUrl.toString();
}

// Exportar o módulo
window.firebaseAuthModule = {
  initializeFirebase,
  signInWithGoogle,
  signInWithFacebook,
  saveUserToLocalStorage,
  checkUserAuthentication,
  redirectAfterAuth
};