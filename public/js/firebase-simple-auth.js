/**
 * Módulo simples de autenticação Firebase para Streamlit
 * Este módulo fornece funções básicas para login social com o Firebase
 */

// Objeto Firebase Auth global
const firebaseSimpleAuth = {
    // Configuração
    config: null,
    
    // Referências internas
    app: null,
    auth: null,
    
    // Provedores de autenticação
    googleProvider: null,
    facebookProvider: null,
    
    /**
     * Inicializa o Firebase com a configuração fornecida
     * @param {Object} config - Configuração do Firebase
     */
    init: function(config) {
        try {
            console.log("Inicializando Firebase Simple Auth...");
            
            // Guardar configuração
            this.config = config;
            
            // Inicializar Firebase se ainda não estiver inicializado
            if (!firebase.apps.length) {
                this.app = firebase.initializeApp(config);
                console.log("Firebase inicializado com sucesso");
            } else {
                this.app = firebase.app();
                console.log("Firebase já estava inicializado");
            }
            
            // Obter auth
            this.auth = firebase.auth();
            
            // Inicializar providers
            this.googleProvider = new firebase.auth.GoogleAuthProvider();
            this.facebookProvider = new firebase.auth.FacebookAuthProvider();
            
            // Configurar opções adicionais (sugestão de conta, etc)
            this.googleProvider.setCustomParameters({
                prompt: 'select_account'
            });
            
            // Configurar listener de estado
            this.setupAuthListener();
            
            return true;
        } catch (error) {
            console.error("Erro ao inicializar Firebase:", error);
            return false;
        }
    },
    
    /**
     * Configura o listener de estado de autenticação
     */
    setupAuthListener: function() {
        this.auth.onAuthStateChanged(user => {
            if (user) {
                console.log("Usuário autenticado:", user.email);
                this.saveUserToLocalStorage(user);
            } else {
                console.log("Nenhum usuário autenticado");
            }
        });
    },
    
    /**
     * Faz login com Google
     * @returns {Promise} Promessa resolvida após login
     */
    loginWithGoogle: function() {
        console.log("Iniciando login com Google...");
        return this.auth.signInWithPopup(this.googleProvider)
            .then(result => {
                console.log("Login com Google bem-sucedido:", result.user.email);
                this.saveUserToLocalStorage(result.user);
                this.redirectAfterLogin(result.user);
                return result.user;
            })
            .catch(error => {
                console.error("Erro no login com Google:", error);
                throw error;
            });
    },
    
    /**
     * Faz login com Facebook
     * @returns {Promise} Promessa resolvida após login
     */
    loginWithFacebook: function() {
        console.log("Iniciando login com Facebook...");
        return this.auth.signInWithPopup(this.facebookProvider)
            .then(result => {
                console.log("Login com Facebook bem-sucedido:", result.user.email);
                this.saveUserToLocalStorage(result.user);
                this.redirectAfterLogin(result.user);
                return result.user;
            })
            .catch(error => {
                console.error("Erro no login com Facebook:", error);
                throw error;
            });
    },
    
    /**
     * Salva dados do usuário no localStorage
     * @param {Object} user - Objeto de usuário do Firebase
     */
    saveUserToLocalStorage: function(user) {
        // Obter token
        user.getIdToken().then(idToken => {
            // Dados a serem salvos
            const userData = {
                uid: user.uid,
                email: user.email,
                displayName: user.displayName || user.email,
                photoURL: user.photoURL,
                idToken: idToken,
                lastLogin: new Date().toISOString()
            };
            
            // Salvar no localStorage
            localStorage.setItem('firebase_user', JSON.stringify(userData));
            console.log("Dados do usuário salvos no localStorage");
        });
    },
    
    /**
     * Redireciona após login bem-sucedido
     * @param {Object} user - Objeto de usuário do Firebase
     */
    redirectAfterLogin: function(user) {
        // Criar URL com parâmetros de autenticação
        const url = new URL(window.location.href);
        url.searchParams.set('auth_success', 'true');
        url.searchParams.set('uid', user.uid);
        url.searchParams.set('email', encodeURIComponent(user.email));
        
        // Pequeno delay para garantir que o token seja salvo
        setTimeout(() => {
            console.log("Redirecionando após login bem-sucedido...");
            window.location.href = url.toString();
        }, 500);
    },
    
    /**
     * Verifica se o usuário já está autenticado
     * @returns {Object|null} Dados do usuário ou null
     */
    checkExistingAuth: function() {
        try {
            const userData = localStorage.getItem('firebase_user');
            if (userData) {
                const user = JSON.parse(userData);
                console.log("Usuário encontrado no localStorage:", user.email);
                return user;
            }
        } catch (error) {
            console.error("Erro ao verificar autenticação existente:", error);
            localStorage.removeItem('firebase_user');
        }
        return null;
    },
    
    /**
     * Faz logout do usuário atual
     */
    logout: function() {
        this.auth.signOut()
            .then(() => {
                console.log("Logout realizado com sucesso");
                localStorage.removeItem('firebase_user');
                window.location.reload();
            })
            .catch(error => {
                console.error("Erro ao fazer logout:", error);
            });
    },
    
    /**
     * Adiciona event listeners aos botões de login
     */
    setupLoginButtons: function() {
        console.log("Configurando botões de login...");
        
        // Botão de login com Google
        const googleBtn = document.getElementById('googleLoginBtn');
        if (googleBtn) {
            googleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.loginWithGoogle()
                    .catch(error => {
                        alert(`Erro ao fazer login com Google: ${error.message}`);
                    });
            });
            console.log("Event listener adicionado ao botão do Google");
        } else {
            console.warn("Botão do Google não encontrado");
        }
        
        // Botão de login com Facebook
        const fbBtn = document.getElementById('facebookLoginBtn');
        if (fbBtn) {
            fbBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.loginWithFacebook()
                    .catch(error => {
                        alert(`Erro ao fazer login com Facebook: ${error.message}`);
                    });
            });
            console.log("Event listener adicionado ao botão do Facebook");
        } else {
            console.warn("Botão do Facebook não encontrado");
        }
    }
};

// Exportar o módulo para uso global
window.firebaseSimpleAuth = firebaseSimpleAuth;