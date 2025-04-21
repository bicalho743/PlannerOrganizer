// Obter a chave da API do ambiente (injetar durante o build)
const firebaseConfig = {
  apiKey: window.FIREBASE_API_KEY || "AIzaSyA8xzYgZXCkZ-97RWQZXtMpvLVf1Jx8wjk", // Fallback para desenvolvimento
  authDomain: "planner-organizer-68a23.firebaseapp.com",
  projectId: "planner-organizer-68a23",
  storageBucket: "planner-organizer-68a23.appspot.com",
  messagingSenderId: "763383033284",
  appId: "1:763383033284:web:5a5dc3b4d3f5bc63631ce7"
};

firebase.initializeApp(firebaseConfig);