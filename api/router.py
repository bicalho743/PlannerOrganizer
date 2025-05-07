
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import pandas as pd
import json
from utils.database import Database
from utils.import_assinaturas import criar_sessao_checkout
from utils.assinatura_db import registrar_assinatura
import os
from datetime import datetime, timedelta

# Importação do router de checkout
from api.checkout import router as checkout_router

api = FastAPI(
    title="Personal Organizer API",
    description="API para sistema de gestão Personal Organizer",
    version="1.0.0"
)

# Incluir o router de checkout
api.include_router(checkout_router)

db = Database()

@api.get("/clientes")
async def get_clientes():
    """
    Retorna lista de todos os clientes cadastrados
    """
    try:
        clientes = db.get_clientes()
        return JSONResponse(content=clientes.to_dict(orient='records'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.get("/propostas")
async def get_propostas():
    """
    Retorna lista de todas as propostas
    """
    try:
        propostas = db.get_propostas()
        return JSONResponse(content=propostas.to_dict(orient='records'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.get("/financeiro")
async def get_financeiro():
    """
    Retorna dados financeiros
    """
    try:
        financeiro = db.get_financeiro()
        return JSONResponse(content=financeiro.to_dict(orient='records'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/api/criar_checkout")
async def api_criar_checkout(request: Request):
    """
    Endpoint para criar uma sessão de checkout do Stripe
    """
    try:
        # Extrair dados do corpo da requisição
        data = await request.json()
        
        if not data:
            raise HTTPException(status_code=400, detail="Dados não fornecidos")
        
        # Obter dados necessários
        price_id = data.get('price_id')
        usuario_id = data.get('usuario_id')
        usuario_nome = data.get('usuario_nome', 'Usuário')
        usuario_email = data.get('usuario_email', 'email@exemplo.com')
        success_url = data.get('success_url', None)
        cancel_url = data.get('cancel_url', None)
        
        # Validar dados obrigatórios
        if not price_id:
            raise HTTPException(status_code=400, detail="ID do preço não fornecido")
        
        if not usuario_id:
            raise HTTPException(status_code=400, detail="ID do usuário não fornecido")
        
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
            return {
                'success': True,
                'checkout_url': resultado.get('checkout_url'),
                'session_id': resultado.get('session_id')
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=resultado.get('message', 'Erro desconhecido')
            )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@api.get("/api/checkout/mensal")
async def checkout_mensal(request: Request):
    """
    Endpoint para criar uma sessão de checkout para o plano mensal
    """
    try:
        # Verificar se há sessão de usuário
        usuario_id = None
        usuario_email = "novo.cliente@exemplo.com"
        usuario_nome = "Novo Cliente"
        
        session_data = getattr(request, "session", {})
        if session_data and 'email' in session_data:
            # Se usuário estiver logado, usar seus dados
            usuario_email = session_data.get('email')
            usuario_nome = session_data.get('nome', 'Usuário')
            usuario_id = session_data.get('id')
            
            if not usuario_id:
                # Tentar obter pelo e-mail se o ID não estiver na sessão
                usuario = db.get_usuario_by_email(usuario_email)
                if usuario is not None:
                    usuario_id = usuario.get('id')
        
        # URLs de redirecionamento padrão - mesmo sem login, redirecionar para cadastro após pagamento
        success_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=success"
        cancel_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/login?status=cancel"
        
        # Criar checkout para o plano Mensal
        price_id = os.environ.get('STRIPE_PRICE_ID_MENSAL')
        
        # Validar price_id
        if not price_id:
            return JSONResponse(
                content={"error": "ID do preço mensal não configurado."},
                status_code=500
            )
        
        # Criar sessão de checkout - funciona mesmo sem ID de usuário
        resultado = criar_sessao_checkout(
            price_id=price_id,
            usuario_id=usuario_id,  # Pode ser None para usuários não logados
            usuario_email=usuario_email,
            usuario_nome=usuario_nome,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        # Redirecionar para URL do checkout se for bem-sucedido
        if resultado.get('success'):
            return JSONResponse(
                content={"redirect": resultado.get('checkout_url')},
                status_code=302
            )
        else:
            return JSONResponse(
                content={"error": resultado.get('message', 'Erro desconhecido')},
                status_code=500
            )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@api.get("/api/checkout/anual")
async def checkout_anual(request: Request):
    """
    Endpoint para criar uma sessão de checkout para o plano anual
    """
    try:
        # Verificar se há sessão de usuário
        usuario_id = None
        usuario_email = "novo.cliente@exemplo.com"
        usuario_nome = "Novo Cliente"
        
        session_data = getattr(request, "session", {})
        if session_data and 'email' in session_data:
            # Se usuário estiver logado, usar seus dados
            usuario_email = session_data.get('email')
            usuario_nome = session_data.get('nome', 'Usuário')
            usuario_id = session_data.get('id')
            
            if not usuario_id:
                # Tentar obter pelo e-mail se o ID não estiver na sessão
                usuario = db.get_usuario_by_email(usuario_email)
                if usuario is not None:
                    usuario_id = usuario.get('id')
        
        # URLs de redirecionamento padrão - mesmo sem login, redirecionar para cadastro após pagamento
        success_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=success"
        cancel_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/login?status=cancel"
        
        # Criar checkout para o plano Anual
        price_id = os.environ.get('STRIPE_PRICE_ID_ANUAL')
        
        # Validar price_id
        if not price_id:
            return JSONResponse(
                content={"error": "ID do preço anual não configurado."},
                status_code=500
            )
        
        # Criar sessão de checkout - funciona mesmo sem ID de usuário
        resultado = criar_sessao_checkout(
            price_id=price_id,
            usuario_id=usuario_id,  # Pode ser None para usuários não logados
            usuario_email=usuario_email,
            usuario_nome=usuario_nome,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        # Redirecionar para URL do checkout se for bem-sucedido
        if resultado.get('success'):
            return JSONResponse(
                content={"redirect": resultado.get('checkout_url')},
                status_code=302
            )
        else:
            return JSONResponse(
                content={"error": resultado.get('message', 'Erro desconhecido')},
                status_code=500
            )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@api.get("/api/checkout/vitalicio")
async def checkout_vitalicio(request: Request):
    """
    Endpoint para criar uma sessão de checkout para o plano vitalício
    """
    try:
        # Verificar se há sessão de usuário
        usuario_id = None
        usuario_email = "novo.cliente@exemplo.com"
        usuario_nome = "Novo Cliente"
        
        session_data = getattr(request, "session", {})
        if session_data and 'email' in session_data:
            # Se usuário estiver logado, usar seus dados
            usuario_email = session_data.get('email')
            usuario_nome = session_data.get('nome', 'Usuário')
            usuario_id = session_data.get('id')
            
            if not usuario_id:
                # Tentar obter pelo e-mail se o ID não estiver na sessão
                usuario = db.get_usuario_by_email(usuario_email)
                if usuario is not None:
                    usuario_id = usuario.get('id')
        
        # URLs de redirecionamento padrão - mesmo sem login, redirecionar para cadastro após pagamento
        success_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=success"
        cancel_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/login?status=cancel"
        
        # Criar checkout para o plano Vitalício
        price_id = os.environ.get('STRIPE_PRICE_ID_VITALICIO')
        
        # Validar price_id
        if not price_id:
            return JSONResponse(
                content={"error": "ID do preço vitalício não configurado."},
                status_code=500
            )
        
        # Criar sessão de checkout - funciona mesmo sem ID de usuário
        resultado = criar_sessao_checkout(
            price_id=price_id,
            usuario_id=usuario_id,  # Pode ser None para usuários não logados
            usuario_email=usuario_email,
            usuario_nome=usuario_nome,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        # Redirecionar para URL do checkout se for bem-sucedido
        if resultado.get('success'):
            return JSONResponse(
                content={"redirect": resultado.get('checkout_url')},
                status_code=302
            )
        else:
            return JSONResponse(
                content={"error": resultado.get('message', 'Erro desconhecido')},
                status_code=500
            )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@api.get("/api/iniciar_teste")
@api.post("/api/iniciar_teste")
async def iniciar_periodo_teste(request: Request):
    """
    Endpoint para iniciar um período de teste gratuito de 7 dias
    Aceita requisições GET e POST
    """
    try:
        # Obter dados do usuário da sessão
        session_data = request.session
        if not session_data or 'email' not in session_data:
            # Redirecionar para login se não estiver autenticado
            return JSONResponse(
                content={"redirect": "/login?redirect=/planos"},
                status_code=302
            )
        
        usuario_email = session_data.get('email')
        usuario_nome = session_data.get('nome', 'Usuário')
        usuario_id = session_data.get('id')  # Supondo que o ID é armazenado na sessão
        
        if not usuario_id:
            # Tentar obter pelo e-mail se o ID não estiver na sessão
            usuario = db.get_usuario_by_email(usuario_email)
            if usuario is not None:
                usuario_id = usuario.get('id')
            else:
                return JSONResponse(
                    content={"error": "Usuário não identificado. Por favor, faça login novamente."},
                    status_code=400
                )
        
        # Verificar se já existe uma assinatura ativa
        from utils.assinatura_db import verificar_assinatura_ativa
        resultado_verificacao = verificar_assinatura_ativa(usuario_id)
        
        if resultado_verificacao.get('sucesso') and resultado_verificacao.get('assinatura_ativa'):
            return JSONResponse(
                content={"redirect": "/minha_assinatura?mensagem=Você já possui uma assinatura ativa."},
                status_code=302
            )
        
        # Calcular datas
        data_inicio = datetime.now()
        data_fim = data_inicio + timedelta(days=7)
        
        # Registrar assinatura de teste
        resultado = registrar_assinatura(
            usuario_id=usuario_id,
            plano='Teste',
            status='trial',
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        if resultado.get('sucesso'):
            # Enviar e-mail de confirmação
            try:
                from utils.email_sender import enviar_confirmacao_teste
                enviar_confirmacao_teste(
                    destinatario=usuario_email,
                    nome=usuario_nome,
                    data_fim=data_fim.strftime('%d/%m/%Y')
                )
            except Exception as e:
                print(f"Erro ao enviar e-mail de confirmação: {str(e)}")
            
            # Para requisições AJAX, retornar JSON com status
            if request.headers.get('content-type') == 'application/json':
                return JSONResponse(
                    content={"sucesso": True, "mensagem": "Período de teste iniciado com sucesso"},
                    status_code=200
                )
            else:
                # Para requisições normais, redirecionar para a página de sucesso
                return JSONResponse(
                    content={"redirect": "/minha_assinatura?status=trial_success"},
                    status_code=302
                )
        else:
            # Para requisições AJAX, retornar JSON com erro
            if request.headers.get('content-type') == 'application/json':
                return JSONResponse(
                    content={"sucesso": False, "mensagem": resultado.get('mensagem', 'Erro desconhecido')},
                    status_code=200
                )
            else:
                # Para requisições normais, retornar erro
                return JSONResponse(
                    content={"error": resultado.get('mensagem', 'Erro desconhecido')},
                    status_code=500
                )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )
