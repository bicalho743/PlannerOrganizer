// Módulo nativo sem versão para navegador: tudo vira função vazia
const f = () => {};
const p = new Proxy(function () {}, { get: (_t, k) => (k === '__esModule' ? true : k === 'default' ? p : k === 'then' ? undefined : p), apply: () => Promise.resolve(null), construct: () => p });
module.exports = p;
