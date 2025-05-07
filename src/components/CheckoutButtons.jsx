import React from 'react';

// URLs do Stripe para os planos
const CHECKOUT_URLS = {
  mensal: "https://buy.stripe.com/test_28og2t34LeLJ6mQ144",
  anual: "https://buy.stripe.com/test_7sI7vRcJ56T29z8dQQ",
  vitalicio: "https://buy.stripe.com/test_eVa2bv34L1Aw29yfYZ"
};

/**
 * Componente de botões de checkout para o Stripe
 * Utiliza a sintaxe correta para manipuladores onClick em React
 */
const CheckoutButtons = () => {
  // Função simples que apenas redireciona para a URL do Stripe
  const handleCheckout = (url) => {
    window.location.href = url;
  };

  return (
    <div className="flex flex-col space-y-4">
      <button
        onClick={() => handleCheckout(CHECKOUT_URLS.mensal)}
        className="w-full text-white bg-blue-500 hover:bg-blue-600 rounded-xl py-2"
      >
        Assinar Mensal
      </button>

      <button
        onClick={() => handleCheckout(CHECKOUT_URLS.anual)}
        className="w-full text-white bg-red-500 hover:bg-red-600 rounded-xl py-2"
      >
        Assinar Anual
      </button>

      <button
        onClick={() => handleCheckout(CHECKOUT_URLS.vitalicio)}
        className="w-full text-white bg-green-500 hover:bg-green-600 rounded-xl py-2"
      >
        Comprar Vitalício
      </button>
    </div>
  );
};

export default CheckoutButtons;