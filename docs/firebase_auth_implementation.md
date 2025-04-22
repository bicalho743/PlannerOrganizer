# Implementação da Autenticação com Google Firebase

Este documento descreve os passos necessários para implementar corretamente a autenticação com Google usando Firebase no aplicativo Planner Organizer.

## Requisitos

1. **HTTPS Obrigatório**
   - O Google OAuth2 exige HTTPS para funcionar corretamente
   - Em ambiente de desenvolvimento, usar `localhost` (não endereços IP)
   - Para produção, garantir que o domínio tenha um certificado SSL válido

2. **Configuração no Firebase Console**
   - Adicionar os domínios autorizados (incluindo localhost para desenvolvimento)
   - Configurar corretamente o OAuth (Authorized origins e Authorized redirect URIs)
   - Habilitar o provedor "Google" nas opções de autenticação do Firebase

3. **Firebase JavaScript SDK**
   - Usar a versão mais recente do Firebase SDK (v9+) 
   - Implementar o método `signInWithPopup` para melhor experiência do usuário
   - Fazer o correto tratamento de erros e respostas

## Implementação Atual

A implementação atual tem algumas limitações:

- Usa um método mais antigo de redirecionamento em vez de popup
- Tem problemas com a formação da URL de autenticação
- Não funciona corretamente em ambientes sem HTTPS

## Solução Proposta

1. **Implementação Moderna com Popup**:
   ```javascript
   import { getAuth, signInWithPopup, GoogleAuthProvider } from "firebase/auth";

   const auth = getAuth();
   const provider = new GoogleAuthProvider();

   signInWithPopup(auth, provider)
     .then((result) => {
       const credential = GoogleAuthProvider.credentialFromResult(result);
       const token = credential.idToken;
       const user = result.user;
       // Enviar token para o backend Streamlit
     })
     .catch((error) => {
       console.error("Erro no login com Google:", error);
     });
   ```

2. **Backend Streamlit para Processamento do Token**:
   - Criar um endpoint para receber e validar o token
   - Verificar o token com Admin SDK do Firebase
   - Armazenar o usuário na sessão Streamlit

3. **Configuração para Produção**:
   - Domínio: `www.plannerorganiza.com.br`
   - Garantir HTTPS ativo
   - Adicionar ao Firebase console como domínio autorizado
   - Configurar corretamente as URIs de redirecionamento

## Próximos Passos

1. Implementar API para processamento de tokens no backend
2. Atualizar a interface com componente de popup funcional
3. Criar fluxo para estado de autenticação na sessão Streamlit
4. Testar em diversos navegadores e dispositivos

## Observações Importantes

- O popup pode ser bloqueado por bloqueadores de popup do navegador
- Em dispositivos móveis, o comportamento pode ser diferente
- É essencial fornecer uma alternativa (como login por email/senha)
- Considerar implementar outros provedores no futuro (Apple, Microsoft, etc)