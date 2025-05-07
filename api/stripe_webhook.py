"""
Webhook para receber e processar eventos do Stripe
"""
import json
from flask import Blueprint, request, jsonify
import os

from utils.import_assinaturas import processar_webhook_evento

stripe_webhook_bp = Blueprint('stripe_webhook', __name__)

@stripe_webhook_bp.route('/api/stripe-webhook', methods=['POST'])
def handle_stripe_webhook():
    """
    Endpoint para receber e processar eventos do Stripe
    """
    try:
        sig_header = request.headers.get('Stripe-Signature')
        payload = request.data
        
        if not sig_header:
            return jsonify({
                'success': False,
                'message': 'Cabeçalho de assinatura não fornecido'
            }), 400
            
        # Processar o evento
        resultado = processar_webhook_evento(payload, sig_header)
        
        if resultado.get('success'):
            return jsonify({
                'success': True,
                'message': resultado.get('message', 'Evento processado com sucesso')
            })
        else:
            return jsonify({
                'success': False,
                'message': resultado.get('message', 'Erro ao processar evento')
            }), 400
            
    except Exception as e:
        import traceback
        print(f"Erro ao processar webhook do Stripe: {str(e)}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500