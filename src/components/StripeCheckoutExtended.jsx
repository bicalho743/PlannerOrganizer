import React from 'react';

// URLs diretos para checkout no Stripe - não expiram
const CHECKOUT_URLS = {
    mensal: "https://buy.stripe.com/test_28og2t34LeLJ6mQ144",
    anual: "https://buy.stripe.com/test_7sI7vRcJ56T29z8dQQ",
    vitalicio: "https://buy.stripe.com/test_eVa2bv34L1Aw29yfYZ"
};

const CheckoutExtended = () => {
    // Função simplificada que apenas redireciona para a URL
    const handleCheckout = (url) => {
        window.location.href = url;
    };

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold text-center mb-8">Planos Planner Organizer</h1>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Plano Mensal */}
                <div className="border rounded-lg p-6 shadow-md">
                    <h2 className="text-xl font-bold mb-4">Plano Mensal</h2>
                    <div className="text-3xl font-bold mb-2">R$9,70</div>
                    <div className="text-gray-500 mb-4">por mês</div>
                    
                    <ul className="list-disc pl-5 mb-6 space-y-2">
                        <li>Acesso a todos os recursos</li>
                        <li>Suporte por e-mail</li>
                        <li>Cancelamento a qualquer momento</li>
                    </ul>
                    
                    <button 
                        className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded"
                        onClick={() => handleCheckout(CHECKOUT_URLS.mensal)}
                    >
                        ASSINAR MENSAL
                    </button>
                </div>
                
                {/* Plano Anual */}
                <div className="border border-orange-500 rounded-lg p-6 shadow-lg relative">
                    <div className="absolute top-0 right-0 bg-orange-500 text-white text-xs px-3 py-1 transform rotate-45 translate-x-8 -translate-y-2">
                        RECOMENDADO
                    </div>
                    
                    <h2 className="text-xl font-bold mb-4">Plano Anual</h2>
                    <div className="text-3xl font-bold mb-2">R$97,00</div>
                    <div className="text-gray-500 mb-4">por ano</div>
                    <div className="bg-green-100 text-green-700 text-sm px-3 py-1 rounded-full text-center mb-4">
                        ECONOMIZE 17%
                    </div>
                    
                    <ul className="list-disc pl-5 mb-6 space-y-2">
                        <li>Acesso a todos os recursos</li>
                        <li>Suporte prioritário</li>
                        <li>Atualizações gratuitas</li>
                        <li>Treinamento personalizado</li>
                    </ul>
                    
                    <button 
                        className="w-full bg-orange-500 hover:bg-orange-600 text-white py-2 px-4 rounded"
                        onClick={() => handleCheckout(CHECKOUT_URLS.anual)}
                    >
                        ASSINAR ANUAL
                    </button>
                </div>
                
                {/* Plano Vitalício */}
                <div className="border rounded-lg p-6 shadow-md">
                    <h2 className="text-xl font-bold mb-4">Acesso Vitalício</h2>
                    <div className="text-3xl font-bold mb-2">R$247,00</div>
                    <div className="text-gray-500 mb-4">pagamento único</div>
                    
                    <ul className="list-disc pl-5 mb-6 space-y-2">
                        <li>Acesso permanente ao sistema</li>
                        <li>Suporte prioritário</li>
                        <li>Sem mensalidades futuras</li>
                        <li>Acesso a todas as atualizações</li>
                    </ul>
                    
                    <button 
                        className="w-full bg-amber-500 hover:bg-amber-600 text-black py-2 px-4 rounded"
                        onClick={() => handleCheckout(CHECKOUT_URLS.vitalicio)}
                    >
                        COMPRAR VITALÍCIO
                    </button>
                </div>
            </div>
            
            <div className="mt-12 text-center">
                <h2 className="text-2xl font-bold mb-4">Não está pronto para assinar?</h2>
                <p className="mb-6">Experimente grátis por 7 dias sem necessidade de cartão de crédito.</p>
                <button 
                    className="bg-gray-800 hover:bg-gray-900 text-white py-2 px-6 rounded text-lg"
                    onClick={() => window.location.href = '/iniciar-teste'}
                >
                    INICIAR TESTE GRATUITO
                </button>
            </div>
        </div>
    );
};

export default CheckoutExtended;