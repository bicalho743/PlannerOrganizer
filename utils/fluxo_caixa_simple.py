"""
Módulo simplificado de fluxo de caixa que lê diretamente da tabela de transações.
Sem duplicação de dados, apenas leitura organizada das transações existentes.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from utils.database import Database
from sqlalchemy import text

class FluxoCaixaSimple:
    """
    Classe para gerenciar fluxo de caixa lendo diretamente da tabela de transações.
    """
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_transacoes_periodo(self, data_inicio: datetime, data_fim: datetime) -> pd.DataFrame:
        """
        Busca todas as transações em um período específico.
        """
        query = """
        SELECT 
            data,
            tipo,
            descricao,
            categoria,
            valor,
            tipo_receita,
            origem_tipo,
            status
        FROM financeiro 
        WHERE usuario_id = :usuario_id 
        AND data BETWEEN :data_inicio AND :data_fim
        ORDER BY data ASC, tipo DESC
        """
        
        with self.db.session() as session:
            result = session.execute(text(query), {
                'usuario_id': self.db.usuario_id, 
                'data_inicio': data_inicio.date(), 
                'data_fim': data_fim.date()
            })
            return pd.DataFrame(result.fetchall(), columns=result.keys())
    
    def get_transacoes_mes(self, ano: int, mes: int) -> pd.DataFrame:
        """
        Busca todas as transações de um mês específico.
        """
        data_inicio = datetime(ano, mes, 1)
        if mes == 12:
            data_fim = datetime(ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = datetime(ano, mes + 1, 1) - timedelta(days=1)
        
        return self.get_transacoes_periodo(data_inicio, data_fim)
    
    def get_categorias_usadas(self, tipo: Optional[str] = None) -> List[str]:
        """
        Retorna lista de categorias já utilizadas nas transações.
        """
        query = """
        SELECT DISTINCT categoria 
        FROM financeiro 
        WHERE usuario_id = :usuario_id
        """
        params = {'usuario_id': self.db.usuario_id}
        
        if tipo:
            query += " AND tipo = :tipo"
            params['tipo'] = tipo
        
        query += " ORDER BY categoria ASC"
        
        with self.db.session() as session:
            result = session.execute(text(query), params)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df['categoria'].tolist() if not df.empty else []
    
    def get_resumo_mensal(self, ano: int, mes: int) -> Dict:
        """
        Calcula resumo financeiro do mês: receitas, despesas, saldo.
        """
        transacoes = self.get_transacoes_mes(ano, mes)
        
        if transacoes.empty:
            return {
                'total_receitas': 0.0,
                'total_despesas': 0.0,
                'saldo_mes': 0.0,
                'receitas_pagas': 0.0,
                'receitas_pendentes': 0.0,
                'despesas_pagas': 0.0,
                'despesas_pendentes': 0.0
            }
        
        # Separar receitas e despesas
        receitas = transacoes[transacoes['tipo'] == 'receita']
        despesas = transacoes[transacoes['tipo'] == 'despesa']
        
        # Calcular totais
        total_receitas = receitas['valor'].sum()
        total_despesas = despesas['valor'].sum()
        
        # Calcular por status
        receitas_pagas = receitas[receitas['status'] == 'Pago']['valor'].sum()
        receitas_pendentes = receitas[receitas['status'] == 'Pendente']['valor'].sum()
        despesas_pagas = despesas[despesas['status'] == 'Pago']['valor'].sum()
        despesas_pendentes = despesas[despesas['status'] == 'Pendente']['valor'].sum()
        
        return {
            'total_receitas': total_receitas,
            'total_despesas': total_despesas,
            'saldo_mes': total_receitas - total_despesas,
            'receitas_pagas': receitas_pagas,
            'receitas_pendentes': receitas_pendentes,
            'despesas_pagas': despesas_pagas,
            'despesas_pendentes': despesas_pendentes
        }
    
    def get_resumo_por_categoria(self, ano: int, mes: int) -> Dict[str, Dict]:
        """
        Agrupa transações por categoria para análise detalhada.
        """
        transacoes = self.get_transacoes_mes(ano, mes)
        
        if transacoes.empty:
            return {}
        
        resumo = {}
        
        # Agrupar por categoria
        for categoria in transacoes['categoria'].unique():
            categoria_data = transacoes[transacoes['categoria'] == categoria]
            
            receitas = categoria_data[categoria_data['tipo'] == 'receita']
            despesas = categoria_data[categoria_data['tipo'] == 'despesa']
            
            resumo[categoria] = {
                'receitas': receitas['valor'].sum(),
                'despesas': despesas['valor'].sum(),
                'saldo': receitas['valor'].sum() - despesas['valor'].sum(),
                'transacoes': len(categoria_data)
            }
        
        return resumo
    
    def get_fluxo_acumulado(self, data_inicio: datetime, data_fim: datetime) -> pd.DataFrame:
        """
        Calcula fluxo de caixa acumulado dia a dia no período.
        """
        transacoes = self.get_transacoes_periodo(data_inicio, data_fim)
        
        if transacoes.empty:
            return pd.DataFrame()
        
        # Agrupar por data
        fluxo_diario = transacoes.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0)
        
        # Garantir que temos colunas de receita e despesa
        if 'receita' not in fluxo_diario.columns:
            fluxo_diario['receita'] = 0
        if 'despesa' not in fluxo_diario.columns:
            fluxo_diario['despesa'] = 0
        
        # Calcular saldo diário e acumulado
        fluxo_diario['saldo_dia'] = fluxo_diario['receita'] - fluxo_diario['despesa']
        fluxo_diario['saldo_acumulado'] = fluxo_diario['saldo_dia'].cumsum()
        
        return fluxo_diario.reset_index()
    
    def export_to_dataframe(self, ano: int, mes: int) -> pd.DataFrame:
        """
        Exporta dados do mês em formato DataFrame para relatórios.
        """
        transacoes = self.get_transacoes_mes(ano, mes)
        
        if transacoes.empty:
            return pd.DataFrame()
        
        # Formatar para exportação
        export_df = transacoes.copy()
        export_df['data'] = pd.to_datetime(export_df['data']).dt.strftime('%d/%m/%Y')
        export_df['valor_formatado'] = export_df['valor'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        # Reordenar colunas
        colunas_export = ['data', 'tipo', 'descricao', 'categoria', 'valor_formatado', 'status']
        export_df = export_df[colunas_export]
        
        return export_df