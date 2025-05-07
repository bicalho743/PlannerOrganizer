"""
API para processamento de checkout do Stripe
"""
import json
from flask import Blueprint, request, jsonify
import os

from utils.import_assinaturas import criar_sessao_checkout

checkout_bp = Blueprint('checkout', __name__)

@checkout_bp.route('/api/criar_checkout', methods=['POST'])
def criar_checkout():
    """
    Endpoint para criar uma sessão de checkout do Stripe
    """
    try:
        # Extrair dados do corpo da requisição
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dados não fornecidos'
            }), 400
        
        # Obter dados necessários
        price_id = data.get('price_id')
        usuario_id = data.get('usuario_id')
        usuario_nome = data.get('usuario_nome', 'Usuário')
        usuario_email = data.get('usuario_email', 'email@exemplo.com')
        success_url = data.get('success_url', os.environ.get('APP_URL', 'http://localhost:5000') + '/minha_assinatura?status=success')
        cancel_url = data.get('cancel_url', os.environ.get('APP_URL', 'http://localhost:5000') + '/minha_assinatura?status=cancel')
        
        # Validar dados obrigatórios
        if not price_id:
            return jsonify({
                'success': False,
                'message': 'ID do preço não fornecido'
            }), 400
        
        if not usuario_id:
            return jsonify({
                'success': False,
                'message': 'ID do usuário não fornecido'
            }), 400
        
        # Criar sessão de checkout
        resultado = criar_sessao_checkout(
            price_id=price_id,
            usuario_id=usuario_id,
            usuario_email=usuario_email,
            usuario_nome=usuario_nome,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        # Retornar resultado
        if resultado.get('success'):
            return jsonify({
                'success': True,
                'checkout_url': resultado.get('checkout_url'),
                'session_id': resultado.get('session_id')
            })
        else:
            return jsonify({
                'success': False,
                'message': resultado.get('message', 'Erro desconhecido')
            }), 500
    
    except Exception as e:
        import traceback
        print(f"Erro ao criar sessão de checkout: {str(e)}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500