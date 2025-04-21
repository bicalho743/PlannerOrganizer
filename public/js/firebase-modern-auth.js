/**
 * Módulo moderno de autenticação Firebase (v9 API) para Streamlit
 * Este arquivo usa a API modular do Firebase para autenticação
 */

// Importar funções do Firebase
import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js';
import { 
  getAuth, 
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  sendPasswordResetEmail,
  sendEmailVerification,
  signOut
} from 'https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js';

// Objeto de autenticação global
let auth = null;
let app = null;

// Função para inicializar o Firebase
function initializeFirebase(config) {
  try {
    console.log("Inicializando Firebase com API modular...");
    
    // Inicializar Firebase se ainda não estiver inicializado
    if (!app) {
      app = initializeApp(config);
      console.log("Firebase inicializado com sucesso");
    } else {
      console.log("Firebase já estava inicializado");
    }
    
    // Obter auth
    auth = getAuth(app);
    return true;
  } catch (error) {
    console.error("Erro ao inicializar Firebase:", error);
    return false;
  }
}

// Login com email e senha
async function loginWithEmail(email, password) {
  console.log("Tentando login com email:", email);
  
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    console.log("Login bem-sucedido para:", user.email);
    
    // Verificar se o email está verificado
    if (user.emailVerified) {
      console.log("Email verificado, redirecionando...");
      saveUserAndRedirect(user);
    } else {
      console.log("Email não verificado. Exibindo alerta.");
      alert("Por favor, verifique seu email antes de fazer login. Se não recebeu o email de verificação, use a opção 'Reenviar'.");
      
      // Salvar usuário mesmo sem verificação para permitir reenvio
      localStorage.setItem('firebase_user_temp', JSON.stringify({
        uid: user.uid,
        email: user.email,
        emailVerified: user.emailVerified
      }));
    }
    return user;
  } catch (error) {
    console.error("Erro ao fazer login:", error);
    
    let mensagem = "Erro ao fazer login. Verifique suas credenciais.";
    if (error.code === 'auth/user-not-found') {
      mensagem = "Email não cadastrado. Crie uma conta primeiro.";
    } else if (error.code === 'auth/wrong-password') {
      mensagem = "Senha incorreta. Tente novamente ou use a opção 'Esqueci minha senha'.";
    } else if (error.code === 'auth/too-many-requests') {
      mensagem = "Muitas tentativas de login. Tente novamente mais tarde ou redefina sua senha.";
    }
    
    alert(mensagem);
    throw error;
  }
}

// Criar nova conta
async function createAccount(email, password) {
  console.log("Criando nova conta para:", email);
  
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    console.log("Conta criada com sucesso para:", user.email);
    
    // Enviar email de verificação
    try {
      await sendEmailVerification(user);
      console.log("Email de verificação enviado");
      alert("Conta criada com sucesso! Um email de verificação foi enviado para " + email + ". Por favor, verifique sua caixa de entrada e confirme seu email antes de fazer login.");
    } catch (verifyError) {
      console.error("Erro ao enviar email de verificação:", verifyError);
      alert("Conta criada, mas não foi possível enviar o email de verificação. Tente fazer login e reenviar o email de verificação.");
    }
    
    return user;
  } catch (error) {
    console.error("Erro ao criar conta:", error);
    
    let mensagem = "Erro ao criar conta.";
    if (error.code === 'auth/email-already-in-use') {
      mensagem = "Este email já está em uso. Tente fazer login ou recuperar sua senha.";
    } else if (error.code === 'auth/invalid-email') {
      mensagem = "Email inválido. Por favor, verifique o formato do email.";
    } else if (error.code === 'auth/weak-password') {
      mensagem = "Senha fraca. Use pelo menos 6 caracteres.";
    }
    
    alert(mensagem);
    throw error;
  }
}

// Reenviar email de verificação
async function resendVerificationEmail() {
  console.log("Reenviando email de verificação...");
  
  const user = auth.currentUser;
  if (user) {
    try {
      await sendEmailVerification(user);
      console.log("Email de verificação reenviado com sucesso");
      alert("Um novo email de verificação foi enviado para " + user.email);
    } catch (error) {
      console.error("Erro ao reenviar email de verificação:", error);
      alert("Erro ao reenviar email de verificação: " + error.message);
      throw error;
    }
  } else {
    console.error("Nenhum usuário autenticado para reenviar verificação");
    alert("Você precisa estar logado para reenviar o email de verificação");
  }
}

// Recuperação de senha
async function resetPassword(email) {
  console.log("Enviando email de recuperação para:", email);
  
  // Configuração para o email de recuperação
  const actionCodeSettings = {
    // URL de redirecionamento após recuperação
    url: window.location.origin + window.location.pathname,
    // Manipular código como código de recuperação de senha
    handleCodeInApp: false
  };
  
  console.log("ActionCodeSettings:", actionCodeSettings);
  
  try {
    await sendPasswordResetEmail(auth, email, actionCodeSettings);
    console.log("Email de recuperação enviado com sucesso");
    alert("Um email de recuperação de senha foi enviado para " + email + ". Por favor, verifique sua caixa de entrada e siga as instruções para redefinir sua senha.");
  } catch (error) {
    console.error("Erro ao enviar email de recuperação:", error);
    
    let mensagem = "Erro ao enviar email de recuperação: " + error.message;
    if (error.code === 'auth/user-not-found') {
      mensagem = "Email não encontrado. Verifique se o email está correto ou crie uma nova conta.";
    } else if (error.code === 'auth/invalid-email') {
      mensagem = "Email inválido. Por favor, verifique o formato do email.";
    }
    
    alert(mensagem);
    throw error;
  }
}

// Salvar dados do usuário e redirecionar
function saveUserAndRedirect(user) {
  // Salvar no localStorage 
  localStorage.setItem('firebase_user', JSON.stringify({
    uid: user.uid,
    email: user.email,
    emailVerified: user.emailVerified,
    lastLogin: new Date().toISOString()
  }));
  
  // Redirecionar com parâmetros para o Streamlit
  let url = new URL(window.location.href);
  url.searchParams.set('auth_success', 'true');
  url.searchParams.set('uid', user.uid);
  url.searchParams.set('email', user.email);
  
  // Redirecionar
  console.log("Redirecionando para:", url.toString());
  window.location.href = url.toString();
}

// Sair
async function performSignOut() {
  console.log("Encerrando sessão...");
  
  try {
    await signOut(auth);
    console.log("Logout realizado com sucesso");
    localStorage.removeItem('firebase_user');
    
    // Redirecionar para a página de login
    window.location.href = window.location.pathname;
  } catch (error) {
    console.error("Erro ao encerrar sessão:", error);
    throw error;
  }
}

// Exportar funções
window.firebaseModernAuth = {
  initialize: initializeFirebase,
  loginWithEmail: loginWithEmail,
  createAccount: createAccount,
  resendVerificationEmail: resendVerificationEmail,
  resetPassword: resetPassword,
  signOut: performSignOut
};