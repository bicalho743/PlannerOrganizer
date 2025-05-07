import React from 'react';

/**
 * SOLUÇÃO DEFINITIVA PARA O ERRO REACT #231
 * Este componente usa a sintaxe correta para manipuladores onClick em React
 * utilize este componente em vez de qualquer outro que esteja causando o erro
 */
const PlanosSolucao = () => {
  // URLs do Stripe para os planos
  const CHECKOUT_URLS = {
    mensal: "https://buy.stripe.com/test_28og2t34LeLJ6mQ144",
    anual: "https://buy.stripe.com/test_7sI7vRcJ56T29z8dQQ",
    vitalicio: "https://buy.stripe.com/test_eVa2bv34L1Aw29yfYZ"
  };

  // Função que apenas redireciona para a URL (sem async/await)
  const handleCheckout = (url) => {
    window.location.href = url;
  };

  return (
    <div className="planos-container">
      <h1>Planos Planner Organizer</h1>
      <p>Escolha o plano ideal para sua organização</p>

      <div className="cards-wrapper">
        {/* Plano Mensal */}
        <div className="plano-card">
          <h2>Plano Mensal</h2>
          <div className="preco">R$9,70</div>
          <div className="periodo">por mês</div>
          
          <ul className="recursos">
            <li>Acesso a todos os recursos</li>
            <li>Suporte por e-mail</li>
            <li>Cancelamento a qualquer momento</li>
          </ul>
          
          {/* SINTAXE CORRETA: function arrow no onClick */}
          <button 
            className="btn-assinar"
            onClick={() => handleCheckout(CHECKOUT_URLS.mensal)}
          >
            ASSINAR MENSAL
          </button>
        </div>
        
        {/* Plano Anual */}
        <div className="plano-card destaque">
          <div className="badge">RECOMENDADO</div>
          <h2>Plano Anual</h2>
          <div className="preco">R$97,00</div>
          <div className="periodo">por ano</div>
          <div className="economia">ECONOMIZE 17%</div>
          
          <ul className="recursos">
            <li>Acesso a todos os recursos</li>
            <li>Suporte prioritário</li>
            <li>Atualizações gratuitas</li>
            <li>Treinamento personalizado</li>
          </ul>
          
          {/* SINTAXE CORRETA: function arrow no onClick */}
          <button 
            className="btn-assinar anual"
            onClick={() => handleCheckout(CHECKOUT_URLS.anual)}
          >
            ASSINAR ANUAL
          </button>
        </div>
        
        {/* Plano Vitalício */}
        <div className="plano-card">
          <h2>Acesso Vitalício</h2>
          <div className="preco">R$247,00</div>
          <div className="periodo">pagamento único</div>
          
          <ul className="recursos">
            <li>Acesso permanente ao sistema</li>
            <li>Suporte prioritário</li>
            <li>Sem mensalidades futuras</li>
            <li>Acesso a todas as atualizações</li>
          </ul>
          
          {/* SINTAXE CORRETA: function arrow no onClick */}
          <button 
            className="btn-assinar vitalicio"
            onClick={() => handleCheckout(CHECKOUT_URLS.vitalicio)}
          >
            COMPRAR VITALÍCIO
          </button>
        </div>
      </div>
      
      <div className="teste-gratuito">
        <h2>Não está pronto para assinar?</h2>
        <p>Experimente grátis por 7 dias sem necessidade de cartão de crédito.</p>
        
        {/* SINTAXE CORRETA: function arrow no onClick */}
        <button 
          className="btn-teste"
          onClick={() => window.location.href = '/iniciar-teste'}
        >
          INICIAR TESTE GRATUITO
        </button>
      </div>
    </div>
  );
};

export default PlanosSolucao;