/**
 * Firebase Authentication Helper
 * Este script gerencia a autenticação com Firebase nos componentes web
 */

// Variável global para o objeto FirebaseAuth
window.firebaseAuth = {
  // Propriedades
  auth: null,
  app: null,
  db: null,
  provider: null,
  fbProvider: null,
  
  // Função para inicializar o Firebase
  init: function(config) {
    try {
      // Verificar se o Firebase já foi inicializado
      if (!firebase.apps.length) {
        // Inicializar o app Firebase
        this.app = firebase.initializeApp(config);
        console.log('Firebase inicializado com sucesso');
      } else {
        this.app = firebase.app();
        console.log('Firebase já estava inicializado');
      }
      
      // Obter instância do Auth
      this.auth = firebase.auth();
      
      // Inicializar provedores
      this.provider = new firebase.auth.GoogleAuthProvider();
      this.fbProvider = new firebase.auth.FacebookAuthProvider();
      
      // Configurar provedores
      this.provider.setCustomParameters({
        prompt: 'select_account'
      });
      
      // Configurar listeners
      this.setupListeners();
      
      return true;
    } catch (error) {
      console.error('Erro ao inicializar Firebase:', error);
      return false;
    }
  },
  
  // Configurar event listeners
  setupListeners: function() {
    try {
      // Verificar se já existe autenticação ao carregar
      this.auth.onAuthStateChanged((user) => {
        if (user) {
          console.log('Usuário autenticado:', user.email);
          this.onLoginSuccess(user);
        } else {
          console.log('Usuário não autenticado');
        }
      });
      
      // Configurar botões de login
      this.setupButtons();
    } catch (error) {
      console.error('Erro ao configurar listeners:', error);
    }
  },
  
  // Configurar botões de login do DOM
  setupButtons: function() {
    document.addEventListener('DOMContentLoaded', () => {
      // Botão do Google
      const googleBtn = document.querySelector('.google-button');
      if (googleBtn) {
        googleBtn.addEventListener('click', (e) => {
          e.preventDefault();
          this.loginWithGoogle();
        });
      }
      
      // Botão do Facebook
      const fbBtn = document.querySelector('.facebook-button');
      if (fbBtn) {
        fbBtn.addEventListener('click', (e) => {
          e.preventDefault();
          this.loginWithFacebook();
        });
      }
      
      console.log('Botões de login configurados');
    });
  },
  
  // Login com Google
  loginWithGoogle: function() {
    console.log('Iniciando login com Google...');
    this.auth.signInWithPopup(this.provider)
      .then((result) => {
        // Login bem-sucedido
        const user = result.user;
        console.log('Login com Google bem-sucedido:', user.email);
        this.onLoginSuccess(user);
      })
      .catch((error) => {
        console.error('Erro ao fazer login com Google:', error);
        this.onLoginError(error);
      });
  },
  
  // Login com Facebook
  loginWithFacebook: function() {
    console.log('Iniciando login com Facebook...');
    this.auth.signInWithPopup(this.fbProvider)
      .then((result) => {
        // Login bem-sucedido
        const user = result.user;
        console.log('Login com Facebook bem-sucedido:', user.email);
        this.onLoginSuccess(user);
      })
      .catch((error) => {
        console.error('Erro ao fazer login com Facebook:', error);
        this.onLoginError(error);
      });
  },
  
  // Callback de sucesso de login
  onLoginSuccess: function(user) {
    try {
      // Obter token ID para passagem para backend
      user.getIdToken().then((idToken) => {
        // Enviar dados para o Streamlit
        this.sendLoginInfoToStreamlit({
          idToken: idToken,
          uid: user.uid,
          displayName: user.displayName,
          email: user.email,
          photoURL: user.photoURL,
          loginTimestamp: new Date().toISOString()
        });
      });
    } catch (error) {
      console.error('Erro ao processar login bem-sucedido:', error);
    }
  },
  
  // Callback de erro de login
  onLoginError: function(error) {
    // Notificar o Streamlit sobre o erro
    this.sendErrorToStreamlit({
      code: error.code,
      message: error.message,
      timestamp: new Date().toISOString()
    });
  },
  
  // Enviar informações para o Streamlit
  sendLoginInfoToStreamlit: function(userInfo) {
    // Usar Streamlit Component API para comunicação
    if (window.parent && window.parent.streamlit) {
      // API de componentes do Streamlit
      window.parent.streamlit.setComponentValue({
        type: 'login_success',
        data: userInfo
      });
    } else {
      // Método alternativo: iFrame e localStorage
      localStorage.setItem('firebase_user', JSON.stringify(userInfo));
      
      // Redirecionar para url com parâmetros
      const redirectUrl = new URL(window.location.href);
      redirectUrl.searchParams.set('login_success', 'true');
      redirectUrl.searchParams.set('uid', userInfo.uid);
      redirectUrl.searchParams.set('email', userInfo.email);
      
      // Redirecionar
      window.location.href = redirectUrl.toString();
    }
  },
  
  // Enviar erro para o Streamlit
  sendErrorToStreamlit: function(errorInfo) {
    // Usar Streamlit Component API para comunicação de erro
    if (window.parent && window.parent.streamlit) {
      window.parent.streamlit.setComponentValue({
        type: 'login_error',
        data: errorInfo
      });
    } else {
      // Método alternativo: localStorage
      localStorage.setItem('firebase_error', JSON.stringify(errorInfo));
      
      // Atualizar URL com parâmetros
      const redirectUrl = new URL(window.location.href);
      redirectUrl.searchParams.set('login_error', 'true');
      redirectUrl.searchParams.set('error_code', errorInfo.code);
      
      // Redirecionar
      window.location.href = redirectUrl.toString();
    }
  }
};