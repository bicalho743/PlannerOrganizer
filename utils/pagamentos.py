import os
import stripe
from datetime import datetime
from utils.database import Database

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')

class GerenciadorPagamentos:
    def __init__(self, db):
        self.db = db

    def criar_pagamento(self, proposta_id, valor, descricao=None):
        """
        Cria uma intenção de pagamento no Stripe
        """
        try:
            # Criar PaymentIntent no Stripe
            intent = stripe.PaymentIntent.create(
                amount=int(valor * 100),  # Stripe usa centavos
                currency='brl',
                payment_method_types=['card'],
                metadata={'proposta_id': proposta_id}
            )

            # Registrar no banco de dados
            self.db._safe_query(lambda: self.db.session.execute(
                """
                INSERT INTO pagamentos 
                (proposta_id, stripe_payment_intent_id, valor, descricao)
                VALUES (:proposta_id, :payment_intent_id, :valor, :descricao)
                """,
                {
                    'proposta_id': proposta_id,
                    'payment_intent_id': intent.id,
                    'valor': valor,
                    'descricao': descricao
                }
            ))

            return {
                'clientSecret': intent.client_secret,
                'publishableKey': STRIPE_PUBLISHABLE_KEY
            }
        except Exception as e:
            raise Exception(f"Erro ao criar pagamento: {str(e)}")

    def atualizar_status_pagamento(self, stripe_payment_intent_id, status):
        """
        Atualiza o status de um pagamento
        """
        try:
            self.db._safe_query(lambda: self.db.session.execute(
                """
                UPDATE pagamentos 
                SET status = :status,
                    data_pagamento = CASE 
                        WHEN :status = 'pago' THEN CURRENT_TIMESTAMP
                        ELSE data_pagamento
                    END
                WHERE stripe_payment_intent_id = :payment_intent_id
                """,
                {
                    'status': status,
                    'payment_intent_id': stripe_payment_intent_id
                }
            ))
            return True
        except Exception as e:
            raise Exception(f"Erro ao atualizar status do pagamento: {str(e)}")

    def get_pagamentos_proposta(self, proposta_id):
        """
        Retorna todos os pagamentos de uma proposta
        """
        try:
            result = self.db._safe_query(lambda: self.db.session.execute(
                """
                SELECT * FROM pagamentos 
                WHERE proposta_id = :proposta_id
                ORDER BY data_criacao DESC
                """,
                {'proposta_id': proposta_id}
            ))
            return [dict(row) for row in result]
        except Exception as e:
            raise Exception(f"Erro ao buscar pagamentos: {str(e)}")

    def webhook_handler(self, event):
        """
        Processa webhooks do Stripe
        """
        try:
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                self.atualizar_status_pagamento(payment_intent['id'], 'pago')
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                self.atualizar_status_pagamento(payment_intent['id'], 'falhou')
            return True
        except Exception as e:
            raise Exception(f"Erro ao processar webhook: {str(e)}")
