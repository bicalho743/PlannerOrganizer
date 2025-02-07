
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import pandas as pd
from utils.database import Database

api = FastAPI(
    title="Personal Organizer API",
    description="API para sistema de gestão Personal Organizer",
    version="1.0.0"
)

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
