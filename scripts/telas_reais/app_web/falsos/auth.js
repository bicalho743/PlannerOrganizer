// Firebase Auth falso para gravar as telas reais do app no navegador (conta de demonstração, sem login de verdade)
const usuario = { uid: 'demo_landing', email: 'ana@exemplo.com', displayName: 'Ana Ribeiro', getIdToken: async () => 'demo', providerData: [] };
export const initializeAuth = () => ({ currentUser: usuario });
export const getAuth = () => ({ currentUser: usuario });
export const getReactNativePersistence = () => ({});
export const onAuthStateChanged = (_a, cb) => { setTimeout(() => cb(usuario), 0); return () => {}; };
export const signOut = async () => {};
export class GoogleAuthProvider { static credential() { return {}; } }
export class OAuthProvider { credential() { return {}; } }
export class EmailAuthProvider { static credential() { return {}; } }
export const reauthenticateWithCredential = async () => {};
export const deleteUser = async () => {};
export const signInWithEmailAndPassword = async () => ({ user: usuario });
export const createUserWithEmailAndPassword = async () => ({ user: usuario });
export const signInWithCredential = async () => ({ user: usuario });
export const sendPasswordResetEmail = async () => {};
export const updateProfile = async () => {};
export const sendEmailVerification = async () => {};
export const User = null;
export const AuthCredential = null;
