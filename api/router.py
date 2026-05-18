# ── ENDPOINTS DE PDF ─────────────────────────────────────────────────────────
# Adicionar esses endpoints ao final do router.py existente

import tempfile
import os
from fastapi.responses import FileResponse

@api.get("/pdf/proposta/{proposta_id}/cliente")
async def pdf_proposta_cliente(proposta_id: int, uid: str = Depends(verify_firebase_token)):
    """Gera PDF de proposta para o cliente."""
    try:
        from utils.pdf_generator_v2 import gerar_pdf_cliente
        db = get_db(uid)
        propostas = db.get_propostas()
        clientes = db.get_clientes()

        if propostas is None or propostas.empty:
            raise HTTPException(status_code=404, detail="Proposta não encontrada")

        prop = propostas[propostas['id'] == proposta_id]
        if prop.empty:
            raise HTTPException(status_code=404, detail="Proposta não encontrada")

        row = prop.iloc[0]
        cliente_id = row.get('cliente_id')
        cliente_row = clientes[clientes['id'] == cliente_id].iloc[0] if clientes is not None and not clientes.empty and cliente_id else {}

        # Buscar produtos/itens da proposta
        try:
            produtos = db.get_produtos_organizadores(proposta_id=proposta_id)
            itens = safe_records(produtos) if produtos is not None else []
        except:
            itens = []

        dados = {
            'proposta_id': proposta_id,
            'cliente': str(row.get('cliente_nome', cliente_row.get('nome', 'Cliente'))),
            'telefone': str(cliente_row.get('telefone', '')),
            'tipo': str(row.get('tipo_proposta', 'Residencial')),
            'status': str(row.get('status', '')),
            'descricao': str(row.get('descricao', '')),
            'itens': [{'descricao': i.get('nome', ''), 'total': float(i.get('valor', 0) or 0)} for i in itens],
            'total': float(row.get('valor', 0) or 0),
            'valor_base': float(row.get('valor', 0) or 0),
            'valor_adicionais': 0,
        }

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            path = tmp.name

        gerar_pdf_cliente(dados, path)
        filename = f"Proposta_{proposta_id}_{dados['cliente'].replace(' ', '_')}.pdf"
        return FileResponse(path, media_type='application/pdf', filename=filename)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/pdf/proposta/{proposta_id}/interno")
async def pdf_proposta_interno(proposta_id: int, uid: str = Depends(verify_firebase_token)):
    """Gera PDF interno da proposta."""
    try:
        from utils.pdf_generator_v2 import gerar_pdf_interno
        db = get_db(uid)
        propostas = db.get_propostas()
        clientes = db.get_clientes()

        prop = propostas[propostas['id'] == proposta_id].iloc[0]
        cliente_id = prop.get('cliente_id')
        cliente_row = clientes[clientes['id'] == cliente_id].iloc[0] if clientes is not None and not clientes.empty and cliente_id else {}

        try:
            produtos = db.get_produtos_organizadores(proposta_id=proposta_id)
            itens = safe_records(produtos) if produtos is not None else []
        except:
            itens = []

        try:
            acrescimos = db.get_acrescimos_proposta(proposta_id)
            acr_records = safe_records(acrescimos) if acrescimos is not None else []
        except:
            acr_records = []

        dados = {
            'proposta_id': proposta_id,
            'cliente': str(prop.get('cliente_nome', cliente_row.get('nome', 'Cliente'))),
            'tipo': str(prop.get('tipo_proposta', 'Residencial')),
            'status': str(prop.get('status', '')),
            'periodo': str(prop.get('data_criacao', ''))[:10],
            'itens': [{'descricao': i.get('nome', ''), 'total': float(i.get('valor', 0) or 0)} for i in itens],
            'acrescimos': [{'descricao': a.get('descricao', ''), 'total': float(a.get('valor', 0) or 0)} for a in acr_records],
            'total': float(prop.get('valor', 0) or 0),
            'custo_total': float(prop.get('valor', 0) or 0),
            'margem': 0,
        }

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            path = tmp.name

        gerar_pdf_interno(dados, path)
        filename = f"Interno_Proposta_{proposta_id}.pdf"
        return FileResponse(path, media_type='application/pdf', filename=filename)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/pdf/proposta/{proposta_id}/fornecedores")
async def pdf_proposta_fornecedores(proposta_id: int, uid: str = Depends(verify_firebase_token)):
    """Gera PDF de fornecedores da proposta."""
    try:
        from utils.pdf_generator_v2 import gerar_pdf_fornecedores
        db = get_db(uid)
        propostas = db.get_propostas()
        clientes = db.get_clientes()

        prop = propostas[propostas['id'] == proposta_id].iloc[0]
        cliente_id = prop.get('cliente_id')
        cliente_row = clientes[clientes['id'] == cliente_id].iloc[0] if clientes is not None and not clientes.empty and cliente_id else {}

        try:
            produtos = db.get_produtos_organizadores(proposta_id=proposta_id)
            prod_records = safe_records(produtos) if produtos is not None else []
            itens_forn = []
            for prod in prod_records:
                try:
                    forn = db.get_produto_fornecedores(prod['id'])
                    forn_records = safe_records(forn) if forn is not None else []
                    for f in forn_records:
                        itens_forn.append({'descricao': f.get('fornecedor_nome', prod.get('nome', '')), 'total': float(f.get('valor', 0) or 0)})
                except:
                    pass
        except:
            itens_forn = []

        dados = {
            'proposta_id': proposta_id,
            'cliente': str(prop.get('cliente_nome', cliente_row.get('nome', 'Cliente'))),
            'telefone': str(cliente_row.get('telefone', '')),
            'tipo': str(prop.get('tipo_proposta', 'Residencial')),
            'status': str(prop.get('status', '')),
            'itens': itens_forn,
            'total': sum(i['total'] for i in itens_forn),
        }

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            path = tmp.name

        gerar_pdf_fornecedores(dados, path)
        filename = f"Fornecedores_Proposta_{proposta_id}.pdf"
        return FileResponse(path, media_type='application/pdf', filename=filename)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/pdf/venda/{venda_id}")
async def pdf_venda(venda_id: int, uid: str = Depends(verify_firebase_token)):
    """Gera PDF de relatório de venda."""
    try:
        from utils.pdf_generator_v2 import gerar_pdf_venda_v2
        import pandas as pd
        db = get_db(uid)
        vendas = db.get_vendas()
        clientes = db.get_clientes()

        if vendas is None or vendas.empty:
            raise HTTPException(status_code=404, detail="Venda não encontrada")

        venda = vendas[vendas['id'] == venda_id]
        if venda.empty:
            raise HTTPException(status_code=404, detail="Venda não encontrada")

        venda_row = venda.iloc[0]
        cliente_id = venda_row.get('cliente_id')
        cliente_row = clientes[clientes['id'] == cliente_id].iloc[0] if clientes is not None and not clientes.empty and cliente_id else {}

        try:
            # Buscar itens da venda
            from utils.database import VendaItem
            session = db.session
            itens = session.query(VendaItem).filter(VendaItem.venda_id == venda_id).all()
            itens_data = [{'produto_nome': i.produto.nome if i.produto else '', 'quantidade': i.quantidade, 'preco_unitario': float(i.preco_unitario), 'subtotal': i.quantidade * float(i.preco_unitario)} for i in itens]
            itens_df = pd.DataFrame(itens_data)
        except:
            itens_df = pd.DataFrame()

        venda_dados = {
            'id': venda_id,
            'valor_total': float(venda_row.get('valor_total', 0) or 0),
            'forma_pagamento': str(venda_row.get('forma_pagamento', '')),
            'data_venda': str(venda_row.get('data_venda', ''))[:10],
            'status': str(venda_row.get('status', '')),
            'observacoes': str(venda_row.get('observacoes', '') or ''),
        }
        cliente_dados = {
            'nome': str(cliente_row.get('nome', 'Cliente')),
            'telefone': str(cliente_row.get('telefone', '')),
            'email': str(cliente_row.get('email', '')),
        }

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            path = tmp.name

        gerar_pdf_venda_v2(venda_dados, cliente_dados, itens_df, path)
        filename = f"Venda_{venda_id}_{cliente_dados['nome'].replace(' ', '_')}.pdf"
        return FileResponse(path, media_type='application/pdf', filename=filename)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
