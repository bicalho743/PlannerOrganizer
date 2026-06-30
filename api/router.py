from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional
import pandas as pd
import os
import requests
import stripe
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

def get_perfil_dados(uid: str) -> dict:
    """Busca dados do perfil do usuário para personalizar PDFs."""
    try:
        db = get_db(uid)
        perfil = db.get_perfil_usuario()
        if perfil:
            return perfil if isinstance(perfil, dict) else {}
    except Exception:
        pass
    return {}

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

class TransacaoUpdate(BaseModel):
    tipo: Optional[str] = None
    descricao: Optional[str] = None
    valor: Optional[float] = None
    categoria: Optional[str] = None

class VendaCreate(BaseModel):
    cliente_id: int
    itens: list
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None
    data_venda: Optional[str] = None

# ── STATUS ────────────────────────────────────────────────────────────────────

@api.get("/api/status")
async def api_status():
    return {"status": "online", "versão": "3.0.0"}

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
            for col in ['data_nascimento', 'data_aniversario', 'aniversario']:
                if col in clientes_df.columns:
                    for _, row in clientes_df.iterrows():
                        try:
                            raw = str(row.get(col, '') or '').strip()
                            if not raw or raw in ('None', 'nan', ''):
                                continue
                            day, month = None, None
                            # Formato DD/MM ou DD/MM/YYYY
                            if '/' in raw:
                                parts = raw.split('/')
                                day = int(parts[0])
                                month = int(parts[1]) if len(parts) > 1 else 0
                            # Formato MM-DD (ex: 06-15)
                            elif '-' in raw and len(raw) <= 5:
                                parts = raw.split('-')
                                month = int(parts[0])
                                day = int(parts[1])
                            # Formato YYYY-MM-DD ou data completa
                            else:
                                dt = pd.to_datetime(raw, errors='coerce')
                                if pd.notna(dt):
                                    day, month = dt.day, dt.month
                            if day and month and month > 0:
                                nome = str(row.get('nome', ''))
                                tel = str(row.get('telefone', '') or '')
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
        get_db(uid).add_cliente(
            nome=body.nome, email=body.email, telefone=body.telefone,
            estado=body.estado, cidade=body.cidade, bairro=body.bairro,
            endereco=body.endereco, data_aniversario=body.data_aniversario,
            origem_cliente=body.origem_cliente, observacoes=body.observacoes
        )
        return JSONResponse(content={"success": True})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.put("/clientes/{cliente_id}")
async def update_cliente(cliente_id: int, body: ClienteUpdate, uid: str = Depends(verify_firebase_token)):
    try:
        get_db(uid).update_cliente(
            cliente_id=cliente_id, nome=body.nome, email=body.email,
            telefone=body.telefone, estado=body.estado, cidade=body.cidade,
            bairro=body.bairro, endereco=body.endereco,
            data_aniversario=body.data_aniversario, origem_cliente=body.origem_cliente,
            observacoes=body.observacoes
        )
        return JSONResponse(content={"success": True})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.delete("/clientes/{cliente_id}")
async def delete_cliente(cliente_id: int, uid: str = Depends(verify_firebase_token)):
    try:
        get_db(uid).delete_cliente(cliente_id)
        return JSONResponse(content={"success": True})
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
        get_db(uid).add_proposta(
            cliente_id=body.cliente_id, descricao=body.descricao,
            valor=body.valor, status=body.status, tipo_proposta=body.tipo_proposta
        )
        return JSONResponse(content={"success": True})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.put("/propostas/{proposta_id}")
async def update_proposta(proposta_id: int, body: PropostaUpdate, uid: str = Depends(verify_firebase_token)):
    try:
        import psycopg2 as _pg2, os as _os
        if body.status:
            from utils.proposta_status import normalize_strict as _norm_status_strict
            from utils.status_execucao import derive_exec_from_status as _derive_exec
            # Gravar sempre o status canônico e manter status_execucao alinhado
            # (regra "proposta finalizada = dois campos"). REJEITA status fora
            # do vocabulário para não persistir valor inválido.
            try:
                _status_canon = _norm_status_strict(body.status) or body.status
            except ValueError as _ve:
                raise HTTPException(status_code=422, detail=str(_ve))
            _exec_implicito = _derive_exec(_status_canon)
            _conn = _pg2.connect(_os.environ.get("DATABASE_URL"))
            _cur = _conn.cursor()
            try:
                _cur.execute(
                    "UPDATE propostas SET status = %s WHERE id = %s",
                    (_status_canon, proposta_id)
                )
                if _status_canon == 'em_execucao':
                    _cur.execute(
                        "UPDATE propostas SET status_execucao = %s, data_inicio_execucao = COALESCE(data_inicio, CURRENT_DATE) WHERE id = %s",
                        ('Em execução', proposta_id)
                    )
                elif _exec_implicito is not None:
                    _cur.execute(
                        "UPDATE propostas SET status_execucao = %s WHERE id = %s",
                        (_exec_implicito, proposta_id)
                    )
                _conn.commit()
                rows = _cur.rowcount
                print(f"[update_proposta] status={_status_canon} id={proposta_id} rows={rows}")
            finally:
                _cur.close()
                _conn.close()
            if rows == 0:
                raise HTTPException(status_code=404, detail="Proposta não encontrada")
            # Invalidar cache do ORM para garantir dados frescos
            try:
                db = get_db(uid)
                db.invalidar_cache()
            except Exception:
                pass
            # Lançamento financeiro ao aprovar
            if _status_canon == 'aprovada':
                try:
                    import psycopg2 as _pg2b, os as _osb
                    _conn2 = _pg2b.connect(_osb.environ.get("DATABASE_URL"))
                    _cur2 = _conn2.cursor()
                    try:
                        _cur2.execute("SELECT valor, numero, descricao, tipo_proposta, cliente_id, usuario_id FROM propostas WHERE id = %s", (proposta_id,))
                        _row = _cur2.fetchone()
                        if _row:
                            _valor, _num, _desc, _tipo, _cli_id, _uid = _row
                            _valor = float(_valor or 0)
                            _cur2.execute("SELECT COUNT(*) FROM financeiro WHERE proposta_id = %s AND origem_tipo = 'proposta_aprovacao'", (proposta_id,))
                            if _cur2.fetchone()[0] == 0 and _valor > 0:
                                _cur2.execute(
                                    "INSERT INTO financeiro (descricao, valor, data, categoria, subcategoria, tipo, origem_id, origem_tipo, proposta_id, status, classificacao, usuario_id) VALUES (%s,%s,CURRENT_DATE,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                    (f"Proposta #{_num} — {_desc or 'Servico'} (Aprovacao)", _valor, "Servicos de organizacao", _tipo or "Organizacao", "Receita", _cli_id, "proposta_aprovacao", proposta_id, "Pendente", "contas_a_receber", _uid)
                                )
                                _conn2.commit()
                                print(f"[aprovacao] lancamento R${_valor} proposta #{_num}")
                    finally:
                        _cur2.close()
                        _conn2.close()
                except Exception as _ae:
                    print(f"[aprovacao] erro: {_ae}")

            # Disparar lançamentos financeiros ao finalizar
            if _status_canon == 'finalizada':
                try:
                    from utils.finalizar_proposta_v2 import finalizar_proposta_v2
                    finalizar_proposta_v2(proposta_id)
                except Exception as _fe:
                    print(f"[finalizar] erro nao critico: {_fe}")
        if body.descricao or body.valor:
            db = get_db(uid)
            db.update_proposta(proposta_id=proposta_id, descricao=body.descricao, valor=body.valor)
        return JSONResponse(content={"success": True})
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
        get_db(uid).add_transacao(
            tipo=body.tipo, descricao=body.descricao,
            valor=body.valor, categoria=body.categoria,
            tipo_receita=body.tipo_receita
        )
        return JSONResponse(content={"success": True})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.put("/financeiro/{transacao_id}")
async def update_transacao(transacao_id: int, body: TransacaoUpdate, uid: str = Depends(verify_firebase_token)):
    try:
        get_db(uid).update_transacao(
            transacao_id=transacao_id, tipo=body.tipo,
            descricao=body.descricao, valor=body.valor, categoria=body.categoria
        )
        return JSONResponse(content={"success": True})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.delete("/financeiro/{transacao_id}")
async def delete_transacao(transacao_id: int, uid: str = Depends(verify_firebase_token)):
    try:
        get_db(uid).delete_transacao(transacao_id)
        return JSONResponse(content={"success": True})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── VENDAS ────────────────────────────────────────────────────────────────────

@api.get("/vendas")
async def get_vendas(uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        vendas = db.get_vendas()
        records = safe_records(vendas)
        total_pago = sum(float(r.get('valor_total', 0) or 0) for r in records if str(r.get('status', '')).lower() in ['confirmada', 'pago', 'concluida'])
        total_pendente = sum(float(r.get('valor_total', 0) or 0) for r in records if str(r.get('status', '')).lower() in ['pendente', 'aberto'])
        return JSONResponse(content={
            "vendas": records,
            "total_pago": round(total_pago, 2),
            "total_pendente": round(total_pendente, 2)
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/vendas")
async def create_venda(body: VendaCreate, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        data_venda = None
        if body.data_venda:
            try:
                data_venda = datetime.strptime(body.data_venda, '%Y-%m-%d').date()
            except:
                pass
        venda_id = db.add_venda(
            cliente_id=body.cliente_id,
            itens=body.itens,
            forma_pagamento=body.forma_pagamento,
            observacoes=body.observacoes,
            data_venda=data_venda
        )
        return JSONResponse(content={"success": True, "venda_id": venda_id})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.get("/produtos")
async def get_produtos(uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        produtos = db.get_produtos()
        return JSONResponse(content=safe_records(produtos))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── PÓS-ORGANIZAÇÃO ───────────────────────────────────────────────────────────

@api.get("/pos-organizacao")
async def get_pos_organizacao(uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        pos = db.get_post_organizations()
        return JSONResponse(content=safe_records(pos))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.get("/pos-organizacao/{pos_id}/acoes")
async def get_pos_acoes(pos_id: int, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        acoes = db.get_post_organization_actions(pos_id)
        return JSONResponse(content=safe_records(acoes))
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
        vendas = db.get_vendas()
        hoje = datetime.now()
        fin_records = safe_records(financeiro)
        vendas_records = safe_records(vendas)

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

        from collections import defaultdict
        cat_totais = defaultdict(float)
        for r in fin_records:
            if r.get('tipo') in ['receita', 'entrada'] and r.get('categoria'):
                cat_totais[r['categoria']] += float(r.get('valor', 0) or 0)
        top_categorias = [{'categoria': k, 'total': round(v, 2)} for k, v in sorted(cat_totais.items(), key=lambda x: -x[1])[:5]]

        total_vendas = sum(float(r.get('valor_total', 0) or 0) for r in vendas_records)

        # Status de propostas
        status_propostas = []
        if propostas is not None and not propostas.empty and 'status' in propostas.columns:
            for status, grupo in propostas.groupby('status'):
                valor_total = float(grupo['valor'].sum()) if 'valor' in grupo.columns else 0
                status_propostas.append({
                    'status': str(status),
                    'quantidade': len(grupo),
                    'valor_total': round(valor_total, 2)
                })

        # Origem dos clientes
        origens_clientes = []
        if clientes is not None and not clientes.empty and 'origem_cliente' in clientes.columns:
            for origem, grupo in clientes.groupby('origem_cliente'):
                if origem and str(origem) != 'nan':
                    origens_clientes.append({'origem': str(origem), 'quantidade': len(grupo)})
            origens_clientes.sort(key=lambda x: -x['quantidade'])

        # Ticket médio
        ticket_medio = 0.0
        prop_records = safe_records(propostas)
        valores = [float(r.get('valor', 0) or 0) for r in prop_records if r.get('valor')]
        if valores:
            ticket_medio = round(sum(valores) / len(valores), 2)

        # Propostas por cliente
        propostas_por_cliente = 0.0
        total_cli = len(clientes) if clientes is not None and not clientes.empty else 0
        total_prop = len(propostas) if propostas is not None and not propostas.empty else 0
        if total_cli > 0:
            propostas_por_cliente = round(total_prop / total_cli, 1)

        return JSONResponse(content={
            "mes_atual": {
                "receita": get_receita_mes(fin_records, mes_atual, ano_atual),
                "servicos": servicos_atual,
                "novos_clientes": total_cli,
                "total_vendas": round(total_vendas, 2)
            },
            "mes_anterior": {
                "receita": get_receita_mes(fin_records, mes_anterior, ano_anterior),
                "servicos": 0,
                "novos_clientes": 0
            },
            "top_categorias": top_categorias,
            "status_propostas": status_propostas,
            "origens_clientes": origens_clientes[:10],
            "ticket_medio": ticket_medio,
            "propostas_por_cliente": propostas_por_cliente
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
                    perfil = perfil.to_dict()
                if isinstance(perfil, dict):
                    # Serializar datas e outros tipos não-JSON para string
                    for k, v in perfil.items():
                        if hasattr(v, 'isoformat'):
                            perfil[k] = v.isoformat()
                        elif v is not None and not isinstance(v, (str, int, float, bool, list, dict)):
                            perfil[k] = str(v)
                    return JSONResponse(content=perfil)
        except Exception as _pe:
            print(f"[perfil] erro: {_pe}")
        return JSONResponse(content={"usuario_id": uid})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── ENDPOINTS DE PDF ─────────────────────────────────────────────────────────
import tempfile
import os
import traceback
from fastapi.responses import FileResponse

def _get_proposta_cliente(db, proposta_id):
    """Helper: busca proposta e cliente."""
    propostas = db.get_propostas()
    clientes = db.get_clientes()
    if propostas is None or propostas.empty:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    prop_found = propostas[propostas['id'] == int(proposta_id)]
    if prop_found.empty:
        raise HTTPException(status_code=404, detail=f"Proposta #{proposta_id} não encontrada")
    prop = prop_found.iloc[0].to_dict()
    cliente_id = int(prop.get('cliente_id', 0))
    cliente = {}
    if clientes is not None and not clientes.empty:
        cli_found = clientes[clientes['id'] == cliente_id]
        if not cli_found.empty:
            cliente = cli_found.iloc[0].to_dict()
    return prop, cliente


@api.get("/pdf/proposta/{proposta_id}/cliente")
async def pdf_proposta_cliente(proposta_id: int, uid: str = Depends(verify_firebase_token)):
    """Gera PDF de fechamento para o cliente — igual ao web."""
    try:
        from utils.pdf_generator_v2 import gerar_pdf_cliente
        db = get_db(uid)
        prop, cliente = _get_proposta_cliente(db, proposta_id)

        # Buscar produtos da proposta
        itens = []
        try:
            produtos_df = db.get_produtos_organizadores(proposta_id)
            if produtos_df is not None and not produtos_df.empty:
                for _, p in produtos_df.iterrows():
                    nome = str(p.get('nome', ''))
                    qtd = float(p.get('quantidade', 1) or 1)
                    valor = float(p.get('valor', 0) or 0)
                    if qtd > 1:
                        nome = f"{nome} ({int(qtd)}x)"
                    itens.append({'descricao': nome, 'total': qtd * valor})
        except Exception:
            pass

        # Buscar acréscimos (exceto fornecedores e assistentes)
        try:
            acrescimos = db.get_acrescimos_proposta(proposta_id)
            if acrescimos is not None and not acrescimos.empty:
                for _, ac in acrescimos.iterrows():
                    tipo_ac = str(ac.get('tipo', '')).lower()
                    if tipo_ac in ('fornecedor', 'assistente'):
                        continue
                    desc = str(ac.get('descricao', '') or ac.get('fornecedor', '') or 'Item')
                    val = float(ac.get('valor', 0) or 0)
                    itens.append({'descricao': desc, 'total': val})
        except Exception:
            pass

        valor_base = float(prop.get('valor', 0) or 0)
        total = valor_base + sum(i['total'] for i in itens if 'Personal Organizer' not in i.get('descricao', ''))
        
        # Item principal
        tipo_prop = str(prop.get('tipo_proposta', 'Organização'))
        itens_final = [{'descricao': f"Personal Organizer - {tipo_prop}", 'total': valor_base}] + itens

        # Calcular valor adicionais
        valor_adicionais = sum(i['total'] for i in itens)
        total_final = valor_base + valor_adicionais

        dados = {
            'proposta_id': prop.get('numero', proposta_id),
            'cliente': str(cliente.get('nome', prop.get('cliente_nome', 'Cliente'))),
            'telefone': str(cliente.get('telefone', '') or ''),
            'tipo': tipo_prop,
            'status': str(prop.get('status', '')).capitalize(),
            'descricao': str(prop.get('descricao', '') or ''),
            'itens': itens_final,
            'total': total_final,
            'valor_base': valor_base,
            'valor_adicionais': valor_adicionais,
        }

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False, dir='/tmp') as tmp:
            path = tmp.name

        gerar_pdf_cliente(dados, path, perfil=get_perfil_dados(uid))
        nome_cli = str(cliente.get('nome', 'cliente')).replace(' ', '_').lower()
        num = prop.get('numero', proposta_id)
        return FileResponse(path, media_type='application/pdf',
                           filename=f"Relatorio_FechamentoCliente_{nome_cli}_{num}.pdf")

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/pdf/proposta/{proposta_id}/interno")
async def pdf_proposta_interno(proposta_id: int, uid: str = Depends(verify_firebase_token)):
    """Gera PDF interno — exatamente igual ao web (gerar_pdf_interno_proposta)."""
    try:
        from utils.pdf_generator_v2 import gerar_pdf_interno
        db = get_db(uid)
        prop, cliente = _get_proposta_cliente(db, proposta_id)

        valor_base = float(prop.get('valor', 0) or 0)
        acrescimos_df = None
        try:
            acrescimos_df = db.get_acrescimos_proposta(proposta_id)
        except Exception:
            pass

        # Catálogo de produtos para cálculo de lucro
        catalogo = {}
        try:
            cat_df = db.get_produtos()
            if cat_df is not None and not cat_df.empty:
                for _, p in cat_df.iterrows():
                    nome_n = str(p.get('nome', '')).strip().upper()
                    catalogo[nome_n] = {
                        'preco_custo': float(p.get('preco_custo', 0) or 0),
                        'preco_venda': float(p.get('preco_venda', 0) or 0),
                    }
        except Exception:
            pass

        # Produtos da proposta
        total_produtos_venda = 0
        lucro_produtos = 0
        try:
            prod_df = db.get_produtos_organizadores(proposta_id)
            if prod_df is not None and not prod_df.empty:
                for _, p in prod_df.iterrows():
                    nome_p = str(p.get('nome', '')).strip()
                    qtd = float(p.get('quantidade', 1) or 1)
                    val = float(p.get('valor', 0) or 0)
                    total_produtos_venda += qtd * val
                    cat = catalogo.get(nome_p.upper())
                    if cat:
                        lucro_produtos += (cat['preco_venda'] - cat['preco_custo']) * qtd
        except Exception:
            pass

        # Catálogo de fornecedores para comissões
        fornecedores_catalogo = {}
        try:
            forn_df = db.get_fornecedores()
            if forn_df is not None and not forn_df.empty:
                for _, f in forn_df.iterrows():
                    nome_f = str(f.get('descricao', f.get('nome', ''))).strip().upper()
                    pct = float(f.get('percentual_comissao', 0) or 0)
                    fornecedores_catalogo[nome_f] = pct
        except Exception:
            pass

        # Processar acréscimos
        total_fornecedores = total_assistentes = total_comissoes = total_outros = 0
        lista_assistentes = []
        if acrescimos_df is not None and not acrescimos_df.empty:
            for _, ac in acrescimos_df.iterrows():
                tipo_ac = str(ac.get('tipo', '')).upper()
                val_ac = float(ac.get('valor', 0) or 0)
                if tipo_ac == 'FORNECEDOR':
                    total_fornecedores += val_ac
                    nome_f = str(ac.get('fornecedor', '')).strip().upper()
                    pct = fornecedores_catalogo.get(nome_f, 0)
                    if pct > 0:
                        total_comissoes += val_ac * pct / 100
                elif tipo_ac == 'ASSISTENTE':
                    total_assistentes += val_ac
                    nome_a = str(ac.get('fornecedor', '') or 'Assistente').strip().title()
                    lista_assistentes.append((nome_a, val_ac))
                else:
                    total_outros += val_ac

        total_custo_cliente = valor_base + total_produtos_venda + total_fornecedores + total_outros
        receita = valor_base + total_comissoes + lucro_produtos + total_outros - total_assistentes

        itens_custo = [
            ("Personal Organizer", valor_base, False),
            ("Produtos", total_produtos_venda, False),
            ("Fornecedores", total_fornecedores, False),
            ("Outros", total_outros, False),
        ]
        itens_receita = [
            ("Personal Organizer", valor_base, False),
            ("Comissões", total_comissoes, False),
            ("Lucro em Produtos", lucro_produtos, False),
            ("Outros", total_outros, False),
        ]
        if lista_assistentes:
            for nome_a, val_a in lista_assistentes:
                itens_receita.append((f"Assistente: {nome_a}", val_a, True))
        elif total_assistentes > 0:
            itens_receita.append(("Pagamento Assistentes", total_assistentes, True))

        # Período
        periodo_str = ''
        di = prop.get('data_inicio', prop.get('data_criacao', ''))
        df = prop.get('data_fim', prop.get('data_conclusao', ''))
        if di and df:
            periodo_str = f"{str(di)[:10]} – {str(df)[:10]}"
        elif di:
            periodo_str = str(di)[:10]

        dados_pdf = {
            'proposta_id': prop.get('numero', proposta_id),
            'cliente': str(cliente.get('nome', prop.get('cliente_nome', 'Cliente'))),
            'tipo': str(prop.get('tipo_proposta', 'Organização')),
            'status': str(prop.get('status', '')).capitalize(),
            'periodo': periodo_str,
            'itens_custo': itens_custo,
            'total_custo': total_custo_cliente,
            'itens_receita': itens_receita,
            'total_receita': receita,
        }

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False, dir='/tmp') as tmp:
            path = tmp.name

        gerar_pdf_interno(dados_pdf, path, perfil=get_perfil_dados(uid))
        nome_cli = str(cliente.get('nome', 'cliente')).replace(' ', '_').lower()
        num = prop.get('numero', proposta_id)
        return FileResponse(path, media_type='application/pdf',
                           filename=f"Relatorio_Interno_{nome_cli}_{num}.pdf")

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/pdf/proposta/{proposta_id}/fornecedores")
async def pdf_proposta_fornecedores(proposta_id: int, uid: str = Depends(verify_firebase_token)):
    """Gera PDF de fornecedores — igual ao web."""
    try:
        from utils.pdf_generator_v2 import gerar_pdf_fornecedores
        db = get_db(uid)
        prop, cliente = _get_proposta_cliente(db, proposta_id)

        itens_forn = []
        try:
            acrescimos_df = db.get_acrescimos_proposta(proposta_id)
            if acrescimos_df is not None and not acrescimos_df.empty:
                for _, ac in acrescimos_df.iterrows():
                    if str(ac.get('tipo', '')).upper() == 'FORNECEDOR':
                        nome = str(ac.get('fornecedor', 'Fornecedor'))
                        val = float(ac.get('valor', 0) or 0)
                        itens_forn.append({'descricao': f"Fornecimento De {nome}", 'total': val})
        except Exception:
            pass

        dados = {
            'proposta_id': prop.get('numero', proposta_id),
            'cliente': str(cliente.get('nome', prop.get('cliente_nome', 'Cliente'))),
            'telefone': str(cliente.get('telefone', '') or ''),
            'tipo': str(prop.get('tipo_proposta', 'Organização')),
            'status': str(prop.get('status', '')).capitalize(),
            'itens': itens_forn,
            'total': sum(i['total'] for i in itens_forn),
        }

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False, dir='/tmp') as tmp:
            path = tmp.name

        gerar_pdf_fornecedores(dados, path, perfil=get_perfil_dados(uid))
        nome_cli = str(cliente.get('nome', 'cliente')).replace(' ', '_').lower()
        num = prop.get('numero', proposta_id)
        return FileResponse(path, media_type='application/pdf',
                           filename=f"Relatorio_Fornecedores_{nome_cli}_{num}.pdf")

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/pdf/proposta/{proposta_id}/produtos")
async def pdf_proposta_produtos(proposta_id: int, uid: str = Depends(verify_firebase_token)):
    """Gera PDF de venda de produtos da proposta — igual ao web (gerar_pdf_venda_proposta)."""
    try:
        from utils.pdf_generator_v2 import gerar_pdf_venda_v2
        import pandas as pd
        db = get_db(uid)
        prop, cliente = _get_proposta_cliente(db, proposta_id)

        itens_data = []
        try:
            prod_df = db.get_produtos_organizadores(proposta_id)
            if prod_df is not None and not prod_df.empty:
                for _, p in prod_df.iterrows():
                    nome = str(p.get('nome', ''))
                    qtd = float(p.get('quantidade', 1) or 1)
                    val = float(p.get('valor', 0) or 0)
                    itens_data.append({
                        'produto_nome': nome,
                        'quantidade': int(qtd),
                        'preco_unitario': val,
                        'subtotal': qtd * val,
                    })
        except Exception:
            pass

        itens_df = pd.DataFrame(itens_data) if itens_data else pd.DataFrame()
        total = sum(i['subtotal'] for i in itens_data)
        num = prop.get('numero', proposta_id)
        nome_cli = str(cliente.get('nome', 'Cliente'))

        venda_dados = {
            'id': proposta_id,
            'valor_total': total,
            'forma_pagamento': 'N/A',
            'data_venda': str(prop.get('data_criacao', ''))[:10],
            'status': 'Proposta',
            'observacoes': f"Produtos Proposta #{num} - {nome_cli}",
        }
        cliente_dados = {
            'nome': nome_cli,
            'telefone': str(cliente.get('telefone', '') or ''),
            'email': str(cliente.get('email', '') or ''),
        }

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False, dir='/tmp') as tmp:
            path = tmp.name

        gerar_pdf_venda_v2(venda_dados, cliente_dados, itens_df, path, perfil=get_perfil_dados(uid))
        nome_file = nome_cli.replace(' ', '_').lower()
        return FileResponse(path, media_type='application/pdf',
                           filename=f"Relatorio_Produtos_{nome_file}_{num}.pdf")

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/pdf/venda/{venda_id}")
async def pdf_venda(venda_id: int, uid: str = Depends(verify_firebase_token)):
    """Gera PDF de venda avulsa."""
    try:
        from utils.pdf_generator_v2 import gerar_pdf_venda_v2
        import pandas as pd
        db = get_db(uid)
        vendas = db.get_vendas()
        clientes = db.get_clientes()

        if vendas is None or vendas.empty:
            raise HTTPException(status_code=404, detail="Venda não encontrada")

        venda_found = vendas[vendas['id'] == venda_id]
        if venda_found.empty:
            raise HTTPException(status_code=404, detail=f"Venda #{venda_id} não encontrada")

        venda_row = venda_found.iloc[0].to_dict()
        cliente_id = int(venda_row.get('cliente_id', 0))
        cliente = {}
        if clientes is not None and not clientes.empty:
            cli_found = clientes[clientes['id'] == cliente_id]
            if not cli_found.empty:
                cliente = cli_found.iloc[0].to_dict()

        # Buscar itens da venda via ORM
        itens_data = []
        try:
            from utils.database import VendaItem
            session = db.session
            itens = session.query(VendaItem).filter(VendaItem.venda_id == venda_id).all()
            for i in itens:
                nome = i.produto.nome if i.produto else ''
                qtd = int(i.quantidade)
                preco = float(i.preco_unitario)
                itens_data.append({
                    'produto_nome': nome,
                    'quantidade': qtd,
                    'preco_unitario': preco,
                    'subtotal': qtd * preco,
                })
        except Exception:
            pass

        itens_df = pd.DataFrame(itens_data) if itens_data else pd.DataFrame()

        venda_dados = {
            'id': venda_id,
            'valor_total': float(venda_row.get('valor_total', 0) or 0),
            'forma_pagamento': str(venda_row.get('forma_pagamento', '') or 'N/A'),
            'data_venda': str(venda_row.get('data_venda', ''))[:10],
            'status': str(venda_row.get('status', '')).capitalize(),
            'observacoes': str(venda_row.get('observacoes', '') or ''),
        }
        cliente_dados = {
            'nome': str(cliente.get('nome', 'Cliente')),
            'telefone': str(cliente.get('telefone', '') or ''),
            'email': str(cliente.get('email', '') or ''),
        }

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False, dir='/tmp') as tmp:
            path = tmp.name

        gerar_pdf_venda_v2(venda_dados, cliente_dados, itens_df, path, perfil=get_perfil_dados(uid))
        nome_cli = str(cliente.get('nome', 'cliente')).replace(' ', '_').lower()
        return FileResponse(path, media_type='application/pdf',
                           filename=f"Relatorio_Venda_{venda_id}_{nome_cli}.pdf")

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/pdf/proposta/{proposta_id}/comercial")
async def pdf_proposta_comercial(proposta_id: int, uid: str = Depends(verify_firebase_token)):
    """Gera PDF de Proposta Comercial — usa layout de fechamento com dados da proposta."""
    try:
        from utils.pdf_generator_v2 import gerar_pdf_cliente
        db = get_db(uid)
        prop, cliente = _get_proposta_cliente(db, proposta_id)

        # Buscar produtos
        itens = []
        try:
            prod_df = db.get_produtos_organizadores(proposta_id)
            if prod_df is not None and not prod_df.empty:
                for _, p in prod_df.iterrows():
                    nome = str(p.get('nome', ''))
                    qtd = float(p.get('quantidade', 1) or 1)
                    val = float(p.get('valor', 0) or 0)
                    subtotal = qtd * val
                    if qtd > 1:
                        nome = f"{nome} ({int(qtd)}x)"
                    itens.append((nome, subtotal, False))
        except Exception:
            pass

        # Buscar acréscimos não-fornecedor não-assistente
        try:
            acrescimos = db.get_acrescimos_proposta(proposta_id)
            if acrescimos is not None and not acrescimos.empty:
                for _, ac in acrescimos.iterrows():
                    tipo_ac = str(ac.get('tipo', '')).lower()
                    if tipo_ac in ('fornecedor', 'assistente'):
                        continue
                    desc = str(ac.get('descricao', '') or ac.get('fornecedor', '') or 'Item')
                    val = float(ac.get('valor', 0) or 0)
                    itens.append((desc, val, False))
        except Exception:
            pass

        valor_proposta = float(prop.get('valor', 0) or 0)
        total = valor_proposta + sum(i[1] for i in itens)

        dados = {
            'proposta_id': prop.get('numero', proposta_id),
            'cliente': str(cliente.get('nome', prop.get('cliente_nome', 'Cliente'))),
            'telefone': str(cliente.get('telefone', '') or ''),
            'tipo': str(prop.get('tipo_proposta', 'Organização')),
            'status': str(prop.get('status', '')).capitalize(),
            'descricao': str(prop.get('descricao', '') or ''),
            'itens': [(f"Personal Organizer - {prop.get('tipo_proposta', 'Organização')}", valor_proposta, False)] + itens,
            'total': total,
            'valor_base': valor_proposta,
            'valor_adicionais': total - valor_proposta,
        }

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False, dir='/tmp') as tmp:
            path = tmp.name

        gerar_pdf_cliente(dados, path, perfil=get_perfil_dados(uid))
        nome_cli = str(cliente.get('nome', 'cliente')).replace(' ', '_').lower()
        num = prop.get('numero', proposta_id)
        return FileResponse(path, media_type='application/pdf',
                           filename=f"Relatorio_PropostaComercial_{nome_cli}_{num}.pdf")

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── ENDPOINTS PROPOSTA EM EXECUÇÃO ────────────────────────────────────────────

class ProdutoOrganizadorCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    valor: float
    quantidade: int = 1
    comodo: Optional[str] = None

class AcrescimoCreate(BaseModel):
    tipo: str  # fornecedor, assistente, outros
    valor: float
    descricao: Optional[str] = None
    fornecedor: Optional[str] = None

@api.get("/propostas/{proposta_id}/produtos")
async def get_produtos_proposta(proposta_id: int, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        df = db.get_produtos_organizadores(proposta_id)
        return JSONResponse(content=safe_records(df))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/propostas/{proposta_id}/produtos")
async def add_produto_proposta(proposta_id: int, body: ProdutoOrganizadorCreate, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        db.add_produto_organizador(
            proposta_id=proposta_id, nome=body.nome, descricao=body.descricao,
            valor=body.valor, quantidade=body.quantidade, comodo=body.comodo
        )
        return JSONResponse(content={"success": True})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.get("/propostas/{proposta_id}/acrescimos")
async def get_acrescimos(proposta_id: int, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        df = db.get_acrescimos_proposta(proposta_id)
        return JSONResponse(content=safe_records(df))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/propostas/{proposta_id}/acrescimos")
async def add_acrescimo(proposta_id: int, body: AcrescimoCreate, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        db.add_acrescimo_proposta(
            proposta_id=proposta_id, tipo=body.tipo, valor=body.valor,
            descricao=body.descricao, fornecedor=body.fornecedor
        )
        return JSONResponse(content={"success": True})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.get("/fornecedores")
async def get_fornecedores(uid: str = Depends(verify_firebase_token)):
    try:
        import os as _os, psycopg2, psycopg2.extras
        db_url = _os.environ.get("DATABASE_URL")
        if db_url:
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT id,
                       descricao,
                       descricao AS nome,
                       contato, categoria, estado, cidade, bairro,
                       endereco, pix, recorrente, observacoes, valor,
                       percentual_comissao, usuario_id
                FROM fornecedores
                WHERE usuario_id = %s OR usuario_id IS NULL
                ORDER BY descricao
            """, (uid,))
            rows = cursor.fetchall()
            cursor.close(); conn.close()
            result = []
            for r in rows:
                item = dict(r)
                for k, v in item.items():
                    if hasattr(v, "isoformat"): item[k] = v.isoformat()
                result.append(item)
            return JSONResponse(content=result)
        # fallback ORM — normaliza nome
        db = get_db(uid)
        records = safe_records(db.get_fornecedores())
        for r in records:
            if not r.get("nome"):
                r["nome"] = r.get("descricao", "")
        return JSONResponse(content=records)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.get("/assistentes")
async def get_assistentes(uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        df = db.get_assistentes() if hasattr(db, 'get_assistentes') else None
        return JSONResponse(content=safe_records(df) if df is not None else [])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── ENDPOINTS CADASTROS UNIFICADOS ────────────────────────────────────────────

class FornecedorCreate(BaseModel):
    descricao: str
    contato: Optional[str] = None
    categoria: Optional[str] = None
    estado: Optional[str] = None
    cidade: Optional[str] = None
    pix: Optional[str] = None
    percentual_comissao: Optional[float] = 0.0
    observacoes: Optional[str] = None

class ParceiroCreate(BaseModel):
    nome: str
    telefone: Optional[str] = None
    area_atuacao: Optional[str] = None
    tipo_parceria: Optional[str] = None
    cidade: Optional[str] = None
    pix: Optional[str] = None
    observacoes: Optional[str] = None

class AssistenteCreate(BaseModel):
    nome: str
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    pix: Optional[str] = None
    observacoes: Optional[str] = None

class ProdutoCreate(BaseModel):
    nome: str
    preco_custo: float = 0.0
    preco_venda: float = 0.0
    descricao: Optional[str] = None
    categoria: Optional[str] = None
    estoque: int = 0

@api.get("/parceiros")
async def get_parceiros(uid: str = Depends(verify_firebase_token)):
    try:
        return JSONResponse(content=safe_records(get_db(uid).get_parceiros()))
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@api.post("/fornecedores")
async def create_fornecedor(body: FornecedorCreate, uid: str = Depends(verify_firebase_token)):
    try:
        get_db(uid).add_fornecedor(
            descricao=body.descricao, contato=body.contato, categoria=body.categoria or '',
            estado=body.estado, cidade=body.cidade, pix=body.pix,
            percentual_comissao=body.percentual_comissao or 0.0, observacoes=body.observacoes
        )
        return JSONResponse(content={"success": True})
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@api.post("/parceiros")
async def create_parceiro(body: ParceiroCreate, uid: str = Depends(verify_firebase_token)):
    try:
        get_db(uid).add_parceiro(
            nome=body.nome, telefone=body.telefone or '', area_atuacao=body.area_atuacao or '',
            tipo_parceria=body.tipo_parceria or '', cidade=body.cidade, pix=body.pix, observacoes=body.observacoes
        )
        return JSONResponse(content={"success": True})
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@api.post("/assistentes")
async def create_assistente(body: AssistenteCreate, uid: str = Depends(verify_firebase_token)):
    try:
        get_db(uid).add_assistente(
            nome=body.nome, telefone=body.telefone, endereco=body.endereco,
            pix=body.pix, observacoes=body.observacoes
        )
        return JSONResponse(content={"success": True})
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@api.post("/produtos")
async def create_produto(body: ProdutoCreate, uid: str = Depends(verify_firebase_token)):
    try:
        get_db(uid).add_produto(
            nome=body.nome, preco_custo=body.preco_custo, preco_venda=body.preco_venda,
            descricao=body.descricao, categoria=body.categoria, estoque=body.estoque
        )
        return JSONResponse(content={"success": True})
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@api.put("/produtos/{produto_id}")
async def update_produto(produto_id: int, body: ProdutoCreate, uid: str = Depends(verify_firebase_token)):
    try:
        get_db(uid).update_produto(
            produto_id=produto_id, nome=body.nome, preco_custo=body.preco_custo,
            preco_venda=body.preco_venda, descricao=body.descricao, categoria=body.categoria, estoque=body.estoque
        )
        return JSONResponse(content={"success": True})
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


# ── PÓS-ORGANIZAÇÃO DETALHADO ─────────────────────────────────────────────────

class AcaoUpdate(BaseModel):
    status: str  # FEITO ou PENDENTE
    notes: Optional[str] = None

@api.get("/pos-organizacao/{pos_id}/acoes")
async def get_pos_acoes_detail(pos_id: int, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        acoes = db.get_post_organization_actions(pos_id)
        records = safe_records(acoes)
        # Buscar templates para enrichment
        try:
            templates = db.get_post_org_templates()
            for r in records:
                action_type = r.get('action_type', '')
                if action_type in templates:
                    t = templates[action_type]
                    r['nome'] = t.get('nome', action_type)
                    r['emoji'] = t.get('emoji', '📌')
                    r['dias_apos'] = t.get('dias_apos', '')
                    r['texto'] = t.get('texto', '')
                else:
                    r['nome'] = action_type.replace('_', ' ').title()
                    r['emoji'] = '📌'
                    r['dias_apos'] = ''
                    r['texto'] = ''
        except:
            pass
        return JSONResponse(content=records)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.put("/pos-organizacao/acoes/{acao_id}")
async def update_pos_acao(acao_id: int, body: AcaoUpdate, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        db.update_post_organization_action(action_id=acao_id, status=body.status, notes=body.notes)
        return JSONResponse(content={"success": True})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── PERFIL UPDATE ─────────────────────────────────────────────────────────────

class PerfilUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    instagram: Optional[str] = None
    empresa: Optional[str] = None
    cargo: Optional[str] = None
    website: Optional[str] = None
    cnpj: Optional[str] = None
    mensagem_padrao: Optional[str] = None
    observacoes_relatorio: Optional[str] = None

@api.put("/perfil")
async def update_perfil(body: PerfilUpdate, uid: str = Depends(verify_firebase_token)):
    try:
        db = get_db(uid)
        dados = {k: v for k, v in body.dict().items() if v is not None}
        db.salvar_perfil_usuario(dados)
        return JSONResponse(content={"success": True})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── WEBHOOK STRIPE ────────────────────────────────────────────────────────────

STRIPE_SECRET_KEY    = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = "whsec_u2kzOmFd0pRzCtcAjdINjZOOOu5dtuju"

@api.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        stripe.api_key = STRIPE_SECRET_KEY
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        print(f"[webhook] erro validação: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    import psycopg2 as _pg2, os as _os
    _db_url = _os.environ.get("DATABASE_URL")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # StripeObject usa atributo, não dict .get()
        try:
            email = getattr(session, "customer_email", None) or ""
            if not email:
                cd = getattr(session, "customer_details", None)
                email = getattr(cd, "email", "") or ""
        except Exception:
            email = ""
        print(f"[webhook] pagamento confirmado: {email}")
        if email:
            try:
                _conn = _pg2.connect(_db_url)
                _cur = _conn.cursor()
                _cur.execute(
                    "UPDATE perfis SET plano = 'pro', ativo = TRUE WHERE email = %s",
                    (email,)
                )
                _conn.commit()
                print(f"[webhook] plano ativado para {email} rows={_cur.rowcount}")
                _cur.close()
                _conn.close()
            except Exception as e:
                print(f"[webhook] erro ao ativar plano: {e}")

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        customer_id = getattr(sub, "customer", None)
        print(f"[webhook] assinatura cancelada: {customer_id}")
        if STRIPE_SECRET_KEY and customer_id:
            try:
                stripe.api_key = STRIPE_SECRET_KEY
                customer = stripe.Customer.retrieve(customer_id)
                email = customer.get("email", "")
                if email:
                    _conn = _pg2.connect(_db_url)
                    _cur = _conn.cursor()
                    _cur.execute(
                        "UPDATE perfis SET plano = 'cancelado' WHERE email = %s",
                        (email,)
                    )
                    _conn.commit()
                    print(f"[webhook] plano cancelado para {email}")
                    _cur.close()
                    _conn.close()
            except Exception as e:
                print(f"[webhook] erro ao cancelar plano: {e}")

    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        email = invoice.get("customer_email", "")
        print(f"[webhook] pagamento falhou: {email}")

    return {"status": "ok"}


@api.get("/stripe/portal")
async def stripe_portal(uid: str = Depends(verify_firebase_token)):
    try:
        import stripe as _stripe, psycopg2 as _pg2, os as _os
        _stripe.api_key = _os.environ.get("STRIPE_SECRET_KEY", "")
        # Buscar email do usuário
        _conn = _pg2.connect(_os.environ.get("DATABASE_URL"))
        _cur = _conn.cursor()
        _cur.execute("SELECT email FROM perfis WHERE usuario_id = %s", (uid,))
        row = _cur.fetchone()
        _cur.close()
        _conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")
        email = row[0]
        # Buscar customer_id no Stripe pelo email
        customers = _stripe.Customer.list(email=email, limit=1)
        if not customers.data:
            raise HTTPException(status_code=404, detail="Cliente não encontrado no Stripe")
        customer_id = customers.data[0].id
        # Criar sessão do portal
        session = _stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url="https://plannerorganiza.com.br",
        )
        return JSONResponse(content={"url": session.url})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
