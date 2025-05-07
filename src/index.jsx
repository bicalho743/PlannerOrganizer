import React from 'react';
import ReactDOM from 'react-dom';
import CheckoutButtons from './components/CheckoutButtons';

// Renderizar o componente correto quando a página for carregada
document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('checkout-container');
  if (container) {
    ReactDOM.render(<CheckoutButtons />, container);
  }
});