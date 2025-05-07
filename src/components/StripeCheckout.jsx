import React, { useState } from 'react';
import axios from 'axios';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

// Componente de checkout do Stripe
const StripeCheckout = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Função assíncrona para lidar com o checkout
  const handleCheckout = async (planType) => {
    setLoading(true);
    setError(null);
    
    try {
      // Importante: use axios.post para fazer a requisição ao endpoint
      const response = await axios.post('/api/create-checkout-session', {
        plan_type: planType,
      });
      
      // Redirecionar para a URL de checkout fornecida pelo Stripe
      window.location.href = response.data.url;
    } catch (err) {
      console.error('Erro ao iniciar sessão de checkout:', err);
      setError('Ocorreu um erro ao processar seu pedido. Por favor, tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-center mb-8">Escolha seu plano</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Plano Mensal */}
        <Card className="border border-gray-200 shadow-md">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold mb-4">Plano Mensal</h2>
            <div className="text-3xl font-bold mb-2">R$9,70</div>
            <div className="text-gray-500 mb-4">por mês</div>
            
            <ul className="list-disc pl-5 mb-6 space-y-2">
              <li>Acesso a todos os recursos</li>
              <li>Suporte por e-mail</li>
              <li>Cancelamento a qualquer momento</li>
            </ul>
            
            {/* Botão com arrow function para onClick */}
            <Button 
              className="w-full"
              onClick={() => handleCheckout('mensal')}
              disabled={loading}
            >
              {loading ? 'Processando...' : 'ASSINAR MENSAL'}
            </Button>
          </CardContent>
        </Card>
        
        {/* Plano Anual */}
        <Card className="border border-orange-500 shadow-lg relative">
          <div className="absolute top-0 right-0 bg-orange-500 text-white px-3 py-1 text-xs font-bold transform rotate-45 translate-x-8 -translate-y-2 shadow-sm">
            RECOMENDADO
          </div>
          <CardContent className="p-6">
            <h2 className="text-xl font-bold mb-4">Plano Anual</h2>
            <div className="text-3xl font-bold mb-2">R$97,00</div>
            <div className="text-gray-500 mb-2">por ano</div>
            <div className="bg-green-100 text-green-700 font-medium text-sm py-1 px-3 rounded-full text-center mb-4">
              ECONOMIZE 17%
            </div>
            
            <ul className="list-disc pl-5 mb-6 space-y-2">
              <li>Acesso a todos os recursos</li>
              <li>Suporte prioritário</li>
              <li>Atualizações gratuitas</li>
              <li>Treinamento personalizado</li>
            </ul>
            
            {/* Botão com arrow function para onClick */}
            <Button 
              className="w-full bg-orange-500 hover:bg-orange-600"
              onClick={() => handleCheckout('anual')}
              disabled={loading}
            >
              {loading ? 'Processando...' : 'ASSINAR ANUAL'}
            </Button>
          </CardContent>
        </Card>
        
        {/* Plano Vitalício */}
        <Card className="border border-gray-200 shadow-md">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold mb-4">Acesso Vitalício</h2>
            <div className="text-3xl font-bold mb-2">R$247,00</div>
            <div className="text-gray-500 mb-4">pagamento único</div>
            
            <ul className="list-disc pl-5 mb-6 space-y-2">
              <li>Acesso permanente ao sistema</li>
              <li>Suporte prioritário</li>
              <li>Sem mensalidades futuras</li>
              <li>Acesso a todas as atualizações</li>
            </ul>
            
            {/* Botão com arrow function para onClick */}
            <Button 
              className="w-full bg-amber-500 hover:bg-amber-600 text-black"
              onClick={() => handleCheckout('vitalicio')}
              disabled={loading}
            >
              {loading ? 'Processando...' : 'COMPRAR VITALÍCIO'}
            </Button>
          </CardContent>
        </Card>
      </div>
      
      {error && (
        <div className="mt-6 p-4 bg-red-100 text-red-800 rounded-md">
          {error}
        </div>
      )}
      
      <div className="mt-12 text-center">
        <h2 className="text-2xl font-bold mb-4">Não está pronto para assinar?</h2>
        <p className="mb-6">Experimente grátis por 7 dias sem necessidade de cartão de crédito.</p>
        <Button 
          variant="outline" 
          size="lg"
          onClick={() => window.location.href = '/iniciar-teste'}
        >
          INICIAR TESTE GRATUITO
        </Button>
      </div>
    </div>
  );
};

export default StripeCheckout;