from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pandas as pd
import os
import requests
from utils.database import Database

api = FastAPI(
    title="Planner Organizer API",
    description="API para sistema de gestão Personal Organizer",
    version="2.0.0"
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY', 'AIzaSyAtuIO-4oyI99rQSl9dAMu756FI4q10kcY')


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


def get_db(usuario_id: str) -> Database:
    return Database(usuario_id=usuario_id)


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


@api.get("/api/status")
async def api_status():
    return {"status": "online", "versão": "2.0.0", "mensagem": "API com auth Firebase ativa"}


@api.get("/dashboard")
async def get_dashboard(usuario_id: str = Depends(verify_firebase_token)):
    try:
        db = get_db(usuario_id)
        clientes_df = db.get_clientes()
        propostas_df = db.get_propostas()
        financeiro_df = db.get_financeiro()

        total_clientes = len(clientes_df) if clientes_df is not None and not clientes_df.empty else 0
        total_propostas = len(propostas_df) if propostas_df is not None and not propostas_df.empty else 0

        propostas_abertas = []
        if propostas_df is not None and not propostas_df.empty and 'status' in propostas_df.columns:
            abertas = propostas_df[propostas_df['status'].isin(['em_elaboracao', 'aguardando', 'enviada'])]
            propostas_abertas = safe_records(abertas)

        receita = 0.0
        despesas = 0.0
        if financeiro_df is not None and not financeiro_df.empty and 'tipo' in financeiro_df.columns:
            receita = float(financeiro_df[financeiro_df['tipo'].isin(['receita', 'entrada'])]['valor'].sum())
            despesas = float(financeiro_df[financeiro_df['tipo'].isin(['despesa', 'saida'])]['valor'].sum())

        aniversariantes_hoje = []
        aniversariantes_mes = []
        hoje = datetime.now()
        if clientes_df is not None and not clientes_df.empty:
            for col in ['data_nascimento', 'aniversario', 'nascimento']:
                if col in clientes_df.columns:
                    for _, row in clientes_df.iterrows():
                        try:
                            dt = pd.to_datetime(row[col])
                            nome = row.get('nome', '')
                            tel = row.get('telefone', '')
                            if dt.month == hoje.month and dt.day == hoje.day:
                                aniversariantes_hoje.append({'nome': nome, 'telefone': tel})
                            elif dt.month == hoje.month:
                                aniversariantes_mes.append({'nome': nome, 'dia': int(dt.day), 'telefone': tel})
                        except:
                            pass
                    break

        return JSONResponse(content={
            "total_clientes": total_clientes,
            "total_propostas": total_propostas,
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


@api.get("/clientes")
async def get_clientes(usuario_id: str = Depends(verify_firebase_token)):
    try:
        db = get_db(usuario_id)
        clientes = db.get_clientes()
        return JSONResponse(content=safe_records(clientes))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/propostas")
async def get_propostas(usuario_id: str = Depends(verify_firebase_token)):
    try:
        db = get_db(usuario_id)
        propostas = db.get_propostas()
        return JSONResponse(content=safe_records(propostas))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/financeiro")
async def get_financeiro(usuario_id: str = Depends(verify_firebase_token)):
    try:
        db = get_db(usuario_id)
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


@api.get("/vendas")
async def get_vendas(usuario_id: str = Depends(verify_firebase_token)):
    try:
        db = get_db(usuario_id)
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


@api.get("/pos-organizacao")
async def get_pos_organizacao(usuario_id: str = Depends(verify_firebase_token)):
    try:
        db = get_db(usuario_id)
        try:
            pos = db.get_pos_organizacao() if hasattr(db, 'get_pos_organizacao') else None
            records = safe_records(pos) if pos is not None else []
        except:
            propostas = db.get_propostas()
            if propostas is not None and not propostas.empty:
                finalizadas = propostas[propostas['status'] == 'finalizada']
                records = safe_records(finalizadas)
            else:
                records = []
        return JSONResponse(content=records)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/relatorios")
async def get_relatorios(usuario_id: str = Depends(verify_firebase_token)):
    try:
        db = get_db(usuario_id)
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

        return JSONResponse(content={
            "mes_atual": {
                "receita": get_receita_mes(fin_records, mes_atual, ano_atual),
                "servicos": len(propostas[propostas['status'].isin(['aprovada', 'finalizada'])]) if propostas is not None and not propostas.empty else 0,
                "novos_clientes": len(clientes) if clientes is not None and not clientes.empty else 0
            },
            "mes_anterior": {
                "receita": get_receita_mes(fin_records, mes_anterior, ano_anterior),
                "servicos": 0,
                "novos_clientes": 0
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/perfil")
async def get_perfil(usuario_id: str = Depends(verify_firebase_token)):
    try:
        db = get_db(usuario_id)
        try:
            perfil = db.get_perfil_usuario()
            if perfil is not None:
                if hasattr(perfil, 'to_dict'):
                    return JSONResponse(content=perfil.to_dict())
                return JSONResponse(content=perfil if isinstance(perfil, dict) else {})
        except:
            pass
        return JSONResponse(content={"usuario_id": usuario_id, "nome": "", "email": "", "telefone": "", "cidade": ""})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
