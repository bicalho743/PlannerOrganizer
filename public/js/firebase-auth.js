/**
 * Firebase Authentication Manager
 * Este script gerencia o estado de autenticação do usuário e integração com o Stripe
 */

// Inicializar o Firebase (estas configurações serão carregadas dinamicamente)
function initFirebase(config) {
  // Inicializar Firebase
  if (!firebase.apps.length) {
    firebase.initializeApp(config);
  }
  console.log("Firebase inicializado com sucesso");
  
  // Configurar listener de estado de autenticação
  firebase.auth().onAuthStateChanged((user) => {
    if (user) {
      console.log("Usuário logado:", user.email);
      handleLoggedInUser(user);
    } else {
      console.log("Usuário não logado");
      handleLoggedOutUser();
    }
  });
}

// Função para lidar com usuário logado
function handleLoggedInUser(user) {
  // Verificar se temos um token de sessão
  const sessionToken = localStorage.getItem('stripe_session_id');
  const isCheckoutReturn = window.location.href.includes('session_id=');
  
  // Se o usuário acabou de retornar do checkout ou pagamentos
  if (isCheckoutReturn || sessionToken) {
    // Capturar parâmetros
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id') || sessionToken;
    
    if (sessionId) {
      // Se tivermos um ID de sessão, verificar com o servidor
      checkPaymentStatus(sessionId, user.uid);
    }
  }
  
  // Se estamos na página de login, redirecionar para a dashboard
  if (window.location.pathname === '/login' || window.location.pathname === '/') {
    redirectToDashboard();
  }
  
  // Mostrar elementos para usuários logados
  showLoggedInElements();
}

// Função para lidar com usuário deslogado
function handleLoggedOutUser() {
  // Se não for a página de login e estamos numa página protegida, redirecionar
  if (window.location.pathname !== '/login' && window.location.pathname !== '/' 
      && requiresAuth(window.location.pathname)) {
    redirectToLogin();
  }
  
  // Mostrar elementos para usuários não logados
  showLoggedOutElements();
}

// Verificar se uma página requer autenticação
function requiresAuth(pathname) {
  // Lista de caminhos que requerem autenticação
  const protectedPaths = [
    '/dashboard',
    '/propostas',
    '/clientes',
    '/vendas',
    '/financeiro',
    '/configuracoes'
  ];
  
  // Verificar se o caminho atual está na lista ou começa com algum dos caminhos
  return protectedPaths.some(path => 
    pathname === path || pathname.startsWith(path + '/')
  );
}

// Redirecionar para a dashboard
function redirectToDashboard() {
  window.location.href = '/dashboard';
}

// Redirecionar para o login
function redirectToLogin() {
  window.location.href = '/login';
}

// Verificar status de pagamento ou assinatura
function checkPaymentStatus(sessionId, userId) {
  // Salvar ID da sessão localmente
  localStorage.setItem('stripe_session_id', sessionId);
  
  // Requisição para o servidor para verificar o status
  fetch(`/api/check-payment-status?session_id=${sessionId}&user_id=${userId}`)
    .then(response => response.json())
    .then(data => {
      console.log("Status do pagamento:", data);
      
      // Se o pagamento foi bem-sucedido, remover o token da sessão
      if (data.status === 'success') {
        localStorage.removeItem('stripe_session_id');
        
        // Se estamos na página de sucesso, mostrar mensagem
        if (window.location.pathname === '/sucesso') {
          showPaymentSuccessMessage(data);
        } else {
          // Redirecionar para dashboard
          redirectToDashboard();
        }
      } 
      // Se o pagamento falhou ou está pendente
      else if (data.status === 'pending') {
        // Mostrar mensagem
        showPaymentPendingMessage();
      }
      else {
        // Mostrar mensagem de erro
        showPaymentErrorMessage(data.message);
      }
    })
    .catch(error => {
      console.error("Erro ao verificar pagamento:", error);
      showPaymentErrorMessage("Erro ao verificar status do pagamento. Por favor, tente novamente mais tarde.");
    });
}

// Funções para modificar a interface com base no estado de autenticação
function showLoggedInElements() {
  // Ocultar elementos de login/signup
  document.querySelectorAll('.logged-out-only').forEach(el => {
    el.style.display = 'none';
  });
  
  // Mostrar elementos para usuários logados
  document.querySelectorAll('.logged-in-only').forEach(el => {
    el.style.display = 'block';
  });
}

function showLoggedOutElements() {
  // Ocultar elementos para usuários logados
  document.querySelectorAll('.logged-in-only').forEach(el => {
    el.style.display = 'none';
  });
  
  // Mostrar elementos de login/signup
  document.querySelectorAll('.logged-out-only').forEach(el => {
    el.style.display = 'block';
  });
}

// Funções para mostrar mensagens relacionadas ao pagamento
function showPaymentSuccessMessage(data) {
  const messageContainer = document.getElementById('payment-message-container');
  if (messageContainer) {
    messageContainer.innerHTML = `
      <div class="success-message">
        <h2>Pagamento Confirmado!</h2>
        <p>Sua assinatura do ${data.plan_name} foi ativada com sucesso.</p>
        <p>Você agora tem acesso completo ao sistema.</p>
        <button onclick="redirectToDashboard()" class="primary-button">Ir para Dashboard</button>
      </div>
    `;
  }
}

function showPaymentPendingMessage() {
  const messageContainer = document.getElementById('payment-message-container');
  if (messageContainer) {
    messageContainer.innerHTML = `
      <div class="pending-message">
        <h2>Pagamento em Processamento</h2>
        <p>Seu pagamento está sendo processado pela operadora.</p>
        <p>Assim que confirmado, sua assinatura será ativada automaticamente.</p>
        <button onclick="redirectToDashboard()" class="primary-button">Continuar</button>
      </div>
    `;
  }
}

function showPaymentErrorMessage(message) {
  const messageContainer = document.getElementById('payment-message-container');
  if (messageContainer) {
    messageContainer.innerHTML = `
      <div class="error-message">
        <h2>Erro no Pagamento</h2>
        <p>${message}</p>
        <button onclick="window.location.reload()" class="secondary-button">Tentar Novamente</button>
      </div>
    `;
  }
}

// Funções de autenticação
function loginWithEmailPassword(email, password) {
  return firebase.auth().signInWithEmailAndPassword(email, password)
    .catch(error => {
      console.error("Erro no login:", error);
      throw error;
    });
}

function registerWithEmailPassword(email, password, displayName) {
  return firebase.auth().createUserWithEmailAndPassword(email, password)
    .then(userCredential => {
      // Atualizar nome de exibição
      return userCredential.user.updateProfile({
        displayName: displayName
      }).then(() => userCredential);
    })
    .catch(error => {
      console.error("Erro no registro:", error);
      throw error;
    });
}

function logout() {
  return firebase.auth().signOut()
    .catch(error => {
      console.error("Erro ao deslogar:", error);
    });
}

function resetPassword(email) {
  return firebase.auth().sendPasswordResetEmail(email)
    .catch(error => {
      console.error("Erro ao resetar senha:", error);
      throw error;
    });
}

// Verificar status da assinatura do usuário
function checkSubscriptionStatus() {
  const user = firebase.auth().currentUser;
  if (!user) return Promise.reject("Usuário não autenticado");
  
  return fetch(`/api/check-subscription?user_id=${user.uid}`)
    .then(response => response.json());
}

// Função para criar checkout e redirecionar para Stripe
function createCheckoutSession(planId) {
  const user = firebase.auth().currentUser;
  if (!user) {
    // Se não tiver usuário logado, salvar plano na sessão e redirecionar para login
    localStorage.setItem('selected_plan', planId);
    window.location.href = '/login?redirect=checkout';
    return Promise.reject("Usuário não autenticado");
  }
  
  // Criar sessão de checkout
  return fetch('/api/create-checkout-session', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      plan_id: planId,
      user_id: user.uid,
      email: user.email
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.url) {
      // Salvar ID da sessão
      localStorage.setItem('stripe_session_id', data.id);
      // Redirecionar para checkout
      window.location.href = data.url;
    } else {
      throw new Error(data.error || "Erro ao criar sessão de checkout");
    }
  });
}

// Exportar funções
window.firebaseAuth = {
  init: initFirebase,
  login: loginWithEmailPassword,
  register: registerWithEmailPassword,
  logout: logout,
  resetPassword: resetPassword,
  checkSubscriptionStatus: checkSubscriptionStatus,
  createCheckoutSession: createCheckoutSession
};