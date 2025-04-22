// Configuração do Firebase
const firebaseConfig = {
  apiKey: "AIzaSyC-2FV8sfqd31Dn9_X9p71GKFX_LfHESS0",
  authDomain: "planner-organizer-68a23.firebaseapp.com",
  projectId: "planner-organizer-68a23",
  storageBucket: "planner-organizer-68a23.appspot.com",
  messagingSenderId: "843210812211",
  appId: "1:843210812211:web:23fc36e58e9cda4f0b1d74",
  databaseURL: "https://planner-organizer-68a23-default-rtdb.firebaseio.com"
};

// Inicializar Firebase
firebase.initializeApp(firebaseConfig);

// Função para login com Google
function loginWithGoogle() {
  const provider = new firebase.auth.GoogleAuthProvider();
  
  firebase.auth().signInWithPopup(provider)
    .then((result) => {
      // Sucesso no login
      const user = result.user;
      console.log("Login com Google realizado com sucesso:", user);
      
      // Salvar token no localStorage
      user.getIdToken().then(token => {
        localStorage.setItem('firebaseToken', token);
        localStorage.setItem('userEmail', user.email);
        localStorage.setItem('userName', user.displayName);
        
        // Redirecionar para o aplicativo principal
        window.opener.postMessage({
          type: 'LOGIN_SUCCESS',
          token: token,
          email: user.email,
          name: user.displayName
        }, '*');
        
        // Mudar o texto para indicar sucesso
        document.getElementById('login-status').textContent = 'Login realizado com sucesso! Redirecionando...';
        document.getElementById('login-status').className = 'success';
        
        // Fechar popup após 3 segundos
        setTimeout(() => {
          window.close();
        }, 3000);
      });
    })
    .catch((error) => {
      console.error("Erro no login com Google:", error);
      document.getElementById('login-status').textContent = 'Erro ao fazer login. Tente novamente.';
      document.getElementById('login-status').className = 'error';
    });
}

// Função para login com Facebook
function loginWithFacebook() {
  const provider = new firebase.auth.FacebookAuthProvider();
  
  firebase.auth().signInWithPopup(provider)
    .then((result) => {
      // Sucesso no login
      const user = result.user;
      console.log("Login com Facebook realizado com sucesso:", user);
      
      // Salvar token no localStorage
      user.getIdToken().then(token => {
        localStorage.setItem('firebaseToken', token);
        localStorage.setItem('userEmail', user.email);
        localStorage.setItem('userName', user.displayName);
        
        // Redirecionar para o aplicativo principal
        window.opener.postMessage({
          type: 'LOGIN_SUCCESS',
          token: token,
          email: user.email,
          name: user.displayName
        }, '*');
        
        // Mudar o texto para indicar sucesso
        document.getElementById('login-status').textContent = 'Login realizado com sucesso! Redirecionando...';
        document.getElementById('login-status').className = 'success';
        
        // Fechar popup após 3 segundos
        setTimeout(() => {
          window.close();
        }, 3000);
      });
    })
    .catch((error) => {
      console.error("Erro no login com Facebook:", error);
      document.getElementById('login-status').textContent = 'Erro ao fazer login. Tente novamente.';
      document.getElementById('login-status').className = 'error';
    });
}

// Adicionar listeners após o carregamento da página
document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('google-login-btn').addEventListener('click', loginWithGoogle);
  document.getElementById('facebook-login-btn').addEventListener('click', loginWithFacebook);
});