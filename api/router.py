from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional
import pandas as pd
import os
import requests
from pydantic import BaseModel
from utils.database import Database

api = FastAPI(title="Planner Organizer API", version="3.0.0")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY', 'AIzaSyAtuIO-4oyI99rQSl9dAMu756FI4q10kcY')

# ── AUTH ──────────────────────────────────────────────────────────────────────

def verify_firebase_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    id_token = auth_header.replace("Bearer ", "").strip()
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_API_KEY}"
        response = requests.post(url, json={"idToken": id_token}, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Token inválido")
        data = response.json()
        users = data.get("users", [])
        if not users:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return users[0]["localId"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Erro auth: {str(e)}")

def get_db(uid: str) -> Database:
    return Database(usuario_id=uid)

def safe_records(df):
    if df is None or (hasattr(df, 'empty') and df.empty):
        return []
    try:
        records = df.to_dict(orient='records')
        for record in records:
            for key, value in record.items():
                if hasattr(value, 'isoformat'):
                    record[key] = value.isoformat()
                elif not isinstance(value, (list, dict, str, int, float, bool, type(None))):
                    record[key] = str(value)
                elif isinstance(value, float) and pd.isna(value):
                    record[key] = None
        return records
    except Exception:
        return []

# ── MODELS ────────────────────────────────────────────────────────────────────

class ClienteCreate(BaseModel):
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    estado: Optional[str] = None
    cidade: Optional[str] = None
    bairro: Optional[str] = None
    endereco: Optional[str] = None
    data_aniversario: Optional[str] = None
    origem_cliente: Optional[str] = None
    observacoes: Optional[str] = None

class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    estado: Optional[str] = None
    cidade: Optional[str] = None
    bairro: Optional[str] = None
    endereco: Optional[str] = None
    data_aniversario: Optional[str] = None
    origem_cliente: Optional[str] = None
    observacoes: Optional[str] = None

class PropostaCreate(BaseModel):
    cliente_id: int
    descricao: str
    valor: float
    status: str = 'em_elaboracao'
    tipo_proposta: Optional[str] = None
    ambiente: Optional[str] = None

class PropostaUpdate(BaseModel):
    descricao: Optional[str] = None
    valor: Optional[float] = None
    status: Optional[str] = None
    ambiente: Optional[str] = None

class TransacaoCreate(BaseModel):
    tipo: str
    descricao: str
    valor: float
    categoria: str
    tipo_receita: Optional[str] = None
    data: Optional[str] = None

class TransacaoUpdate(BaseModel):
    tipo: Optional[str] = None
    descricao: Optional[str] = None
    valor: Optional[float] = None
    categoria: Optional[str] = None

class PosOrganizacaoUpdate(BaseModel):
    status: Optional[bool] = None
    observacao: Optional[str] = None
    data_retorno: Optional[str] = None

# ── STATUS ────────────────────────────────────────────────────────────────────

@api.get("/api/status")
async def api_status():
    return {"status": "online", "versão": "3.0.0", "mensagem": "API CRUD completa"}

# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@api.get("/dashboard")
async def get_dashboard(uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        clientes_df = db.get_clientes()
        propostas_df = db.get_propostas()
        financeiro_df = db.get_financeiro()

        total_clientes = len(clientes_df) if clientes_df is not None and not clientes_df.empty else 0
        propostas_abertas = []
        if propostas_df is not None and not propostas_df.empty and 'status' in propostas_df.columns:
            abertas = propostas_df[propostas_df['status'].isin(['em_elaboracao', 'aguardando', 'enviada'])]
            propostas_abertas = safe_records(abertas)

        receita = despesas = 0.0
        if financeiro_df is not None and not financeiro_df.empty and 'tipo' in financeiro_df.columns:
            receita = float(financeiro_df[financeiro_df['tipo'].isin(['receita','entrada'])]['valor'].sum())
            despesas = float(financeiro_df[financeiro_df['tipo'].isin(['despesa','saida'])]['valor'].sum())

        aniversariantes_hoje = []
        aniversariantes_mes = []
        hoje = datetime.now()
        if clientes_df is not None and not clientes_df.empty:
            for col in ['data_nascimento', 'aniversario', 'data_aniversario']:
                if col in clientes_df.columns:
                    for _, row in clientes_df.iterrows():
                        try:
                            raw = str(row[col])
                            if '/' in raw and len(raw) <= 6:
                                parts = raw.split('/')
                                day, month = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
                            else:
                                dt = pd.to_datetime(raw)
                                day, month = dt.day, dt.month
                            nome = row.get('nome', '')
                            tel = row.get('telefone', '')
                            if month == hoje.month and day == hoje.day:
                                aniversariantes_hoje.append({'nome': nome, 'telefone': tel})
                            elif month == hoje.month:
                                aniversariantes_mes.append({'nome': nome, 'dia': day, 'telefone': tel})
                        except:
                            pass
                    break

        return JSONResponse(content={
            "total_clientes": total_clientes,
            "total_propostas": len(propostas_df) if propostas_df is not None and not propostas_df.empty else 0,
            "propostas_abertas": len(propostas_abertas),
            "receita_mes": round(receita, 2),
            "despesas_mes": round(despesas, 2),
            "saldo": round(receita - despesas, 2),
            "ultimas_propostas": propostas_abertas[:5],
            "aniversariantes_hoje": aniversariantes_hoje,
            "aniversariantes_mes": sorted(aniversariantes_mes, key=lambda x: x.get('dia', 0))
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── CLIENTES ──────────────────────────────────────────────────────────────────

@api.get("/clientes")
async def get_clientes(uid: str = Depends(verify_firebase_token)):
    try:
        return JSONResponse(content=safe_records(get_db(uid).get_clientes()))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/clientes")
async def create_cliente(body: ClienteCreate, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        db.add_cliente(
            nome=body.nome, email=body.email, telefone=body.telefone,
            estado=body.estado, cidade=body.cidade, bairro=body.bairro,
            endereco=body.endereco, data_aniversario=body.data_aniversario,
            origem_cliente=body.origem_cliente, observacoes=body.observacoes
        )
        return JSONResponse(content={"success": True, "message": "Cliente cadastrado!"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.put("/clientes/{cliente_id}")
async def update_cliente(cliente_id: int, body: ClienteUpdate, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        db.update_cliente(
            cliente_id=cliente_id, nome=body.nome, email=body.email,
            telefone=body.telefone, estado=body.estado, cidade=body.cidade,
            bairro=body.bairro, endereco=body.endereco,
            data_aniversario=body.data_aniversario, origem_cliente=body.origem_cliente,
            observacoes=body.observacoes
        )
        return JSONResponse(content={"success": True, "message": "Cliente atualizado!"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.delete("/clientes/{cliente_id}")
async def delete_cliente(cliente_id: int, uid: str = Depends(verify_firebase_token)):
    try:
        get_db(uid).delete_cliente(cliente_id)
        return JSONResponse(content={"success": True, "message": "Cliente excluído!"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── PROPOSTAS ─────────────────────────────────────────────────────────────────

@api.get("/propostas")
async def get_propostas(uid: str = Depends(verify_firebase_token)):
    try:
        return JSONResponse(content=safe_records(get_db(uid).get_propostas()))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/propostas")
async def create_proposta(body: PropostaCreate, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        db.add_proposta(
            cliente_id=body.cliente_id, descricao=body.descricao,
            valor=body.valor, status=body.status, tipo_proposta=body.tipo_proposta
        )
        return JSONResponse(content={"success": True, "message": "Proposta criada!"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.put("/propostas/{proposta_id}")
async def update_proposta(proposta_id: int, body: PropostaUpdate, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        if body.status:
            db.update_proposta_status(proposta_id, body.status)
        if body.descricao or body.valor or body.ambiente:
            db.update_proposta(
                proposta_id=proposta_id, descricao=body.descricao,
                valor=body.valor
            )
        return JSONResponse(content={"success": True, "message": "Proposta atualizada!"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── FINANCEIRO ────────────────────────────────────────────────────────────────

@api.get("/financeiro")
async def get_financeiro(uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        financeiro = db.get_financeiro()
        records = safe_records(financeiro)
        receitas = sum(float(r.get('valor', 0) or 0) for r in records if r.get('tipo') in ['receita', 'entrada'])
        despesas = sum(float(r.get('valor', 0) or 0) for r in records if r.get('tipo') in ['despesa', 'saida'])
        return JSONResponse(content={
            "transacoes": records,
            "saldo": round(receitas - despesas, 2),
            "receitas": round(receitas, 2),
            "despesas": round(despesas, 2)
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/financeiro")
async def create_transacao(body: TransacaoCreate, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        db.add_transacao(
            tipo=body.tipo, descricao=body.descricao,
            valor=body.valor, categoria=body.categoria,
            tipo_receita=body.tipo_receita
        )
        return JSONResponse(content={"success": True, "message": "Transação registrada!"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.put("/financeiro/{transacao_id}")
async def update_transacao(transacao_id: int, body: TransacaoUpdate, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        db.update_transacao(
            transacao_id=transacao_id, tipo=body.tipo,
            descricao=body.descricao, valor=body.valor, categoria=body.categoria
        )
        return JSONResponse(content={"success": True, "message": "Transação atualizada!"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.delete("/financeiro/{transacao_id}")
async def delete_transacao(transacao_id: int, uid: str = Depends(verify_firebase_token)):
    try:
        get_db(uid).delete_transacao(transacao_id)
        return JSONResponse(content={"success": True, "message": "Transação excluída!"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── VENDAS ────────────────────────────────────────────────────────────────────

@api.get("/vendas")
async def get_vendas(uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        try:
            vendas = db.get_historico_pagamentos()
            records = safe_records(vendas)
        except:
            propostas = db.get_propostas()
            if propostas is not None and not propostas.empty:
                vendas_df = propostas[propostas['status'].isin(['aprovada', 'finalizada', 'pago'])]
                records = safe_records(vendas_df)
            else:
                records = []
        total_pago = sum(float(r.get('valor', 0) or 0) for r in records if r.get('status') in ['pago', 'aprovada', 'finalizada'])
        total_pendente = sum(float(r.get('valor', 0) or 0) for r in records if r.get('status') in ['pendente', 'aguardando'])
        return JSONResponse(content={"vendas": records, "total_pago": round(total_pago, 2), "total_pendente": round(total_pendente, 2)})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── PÓS-ORGANIZAÇÃO ───────────────────────────────────────────────────────────

@api.get("/pos-organizacao")
async def get_pos_organizacao(uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        try:
            pos = db.get_pos_organizacao() if hasattr(db, 'get_pos_organizacao') else None
            records = safe_records(pos) if pos is not None else []
        except:
            propostas = db.get_propostas()
            if propostas is not None and not propostas.empty:
                finalizadas = propostas[propostas['status'].isin(['finalizada', 'aprovada'])]
                records = safe_records(finalizadas)
            else:
                records = []
        return JSONResponse(content=records)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── RELATÓRIOS ────────────────────────────────────────────────────────────────

@api.get("/relatorios")
async def get_relatorios(uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        financeiro = db.get_financeiro()
        propostas = db.get_propostas()
        clientes = db.get_clientes()
        hoje = datetime.now()
        fin_records = safe_records(financeiro)

        def get_receita_mes(records, mes, ano):
            total = 0.0
            for r in records:
                if r.get('tipo') in ['receita', 'entrada']:
                    try:
                        data_str = r.get('data') or r.get('data_lancamento', '')
                        if data_str:
                            dt = datetime.fromisoformat(str(data_str)[:10])
                            if dt.month == mes and dt.year == ano:
                                total += float(r.get('valor', 0) or 0)
                    except:
                        pass
            return round(total, 2)

        mes_atual = hoje.month
        ano_atual = hoje.year
        mes_anterior = mes_atual - 1 if mes_atual > 1 else 12
        ano_anterior = ano_atual if mes_atual > 1 else ano_atual - 1

        servicos_atual = 0
        if propostas is not None and not propostas.empty and 'status' in propostas.columns:
            servicos_atual = len(propostas[propostas['status'].isin(['aprovada', 'finalizada'])])

        # Top categorias de receita
        top_categorias = []
        from collections import defaultdict
        cat_totais = defaultdict(float)
        for r in fin_records:
            if r.get('tipo') in ['receita', 'entrada'] and r.get('categoria'):
                cat_totais[r['categoria']] += float(r.get('valor', 0) or 0)
        top_categorias = [{'categoria': k, 'total': round(v, 2)} for k, v in sorted(cat_totais.items(), key=lambda x: -x[1])[:5]]

        return JSONResponse(content={
            "mes_atual": {
                "receita": get_receita_mes(fin_records, mes_atual, ano_atual),
                "servicos": servicos_atual,
                "novos_clientes": len(clientes) if clientes is not None and not clientes.empty else 0
            },
            "mes_anterior": {
                "receita": get_receita_mes(fin_records, mes_anterior, ano_anterior),
                "servicos": 0,
                "novos_clientes": 0
            },
            "top_categorias": top_categorias
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── PERFIL ────────────────────────────────────────────────────────────────────

@api.get("/perfil")
async def get_perfil(uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        try:
            perfil = db.get_perfil_usuario()
            if perfil is not None:
                if hasattr(perfil, 'to_dict'):
                    return JSONResponse(content=perfil.to_dict())
                return JSONResponse(content=perfil if isinstance(perfil, dict) else {})
        except:
            pass
        return JSONResponse(content={"usuario_id": uid, "nome": "", "email": "", "telefone": "", "cidade": ""})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
