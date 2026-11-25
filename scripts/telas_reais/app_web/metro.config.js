const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');
const config = getDefaultConfig(__dirname);
const FALSOS = {
  'firebase/auth': path.join(__dirname, 'falsos/auth.js'),
  'react-native-purchases': path.join(__dirname, 'falsos/vazio.js'),
  '@react-native-google-signin/google-signin': path.join(__dirname, 'falsos/vazio.js'),
  'expo-apple-authentication': path.join(__dirname, 'falsos/vazio.js'),
  'expo-speech-recognition': path.join(__dirname, 'falsos/vazio.js'),
  'expo-store-review': path.join(__dirname, 'falsos/vazio.js'),
  'react-native-fbsdk-next': path.join(__dirname, 'falsos/vazio.js'),
};
const original = config.resolver.resolveRequest;
config.resolver.resolveRequest = (ctx, nome, plataforma) => {
  if (plataforma === 'web' && FALSOS[nome]) return { type: 'sourceFile', filePath: FALSOS[nome] };
  return (original || ctx.resolveRequest)(ctx, nome, plataforma);
};
module.exports = config;
