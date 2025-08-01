"""
Módulo de fluxo de caixa inspirado na planilha "Fluxo de caixa".

Este módulo define estruturas de dados e funções para montar um fluxo
de caixa mensal semelhante ao encontrado na planilha fornecida. Ele
permite registrar receitas e despesas previstas ou realizadas por
mês, calcular totais, saldos acumulados e necessidades de caixa
("empréstimos"). Além disso, expõe métodos que facilitam a edição
dos valores de saída ("saídas") sem quebrar as fórmulas de cálculo.

O objetivo principal é encapsular a lógica presente na planilha em
classes reutilizáveis para serem integradas a uma aplicação financeira
no Replit ou em outros ambientes Python.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime

# Definição das categorias de entradas e saídas conforme a planilha
REVENUE_CATEGORIES: List[str] = [
    "Previsão de recebimento vendas",
    "Contas a receber-vendas realizadas",
    "Outros recebimentos",
]

EXPENSE_CATEGORIES: List[str] = [
    "Fornecedores",
    "MEI",
    "Marketing Instagram",
    "BNI",
    "Pró Labore",
    "Telefone",
    "Combustíveis",
    "manutenção veículo",
    "Seguro Veículo",
    # A planilha possui duas linhas relacionadas a marketing de Instagram
    # com grafia diferente; ambas foram mantidas por compatibilidade.
    "Marketing instagram",
    "Produção conteúdo",
]


@dataclass
class MonthCashFlow:
    """Representa o fluxo de caixa de um mês específico.

    Cada mês mantém valores previstos e realizados para receitas e
    despesas. O saldo anterior e o valor de empréstimo (quando
    necessário) são considerados no cálculo do saldo final.
    """

    name: str
    # Valores previstos
    previsao_receitas: Dict[str, float] = field(default_factory=dict)
    previsao_despesas: Dict[str, float] = field(default_factory=dict)
    # Valores realizados (podem ser omitidos se não houver)
    realizado_receitas: Optional[Dict[str, float]] = None
    realizado_despesas: Optional[Dict[str, float]] = None
    # Saldos e necessidades de caixa
    saldo_anterior: float = 0.0
    emprestimo: float = 0.0

    def _sum_values(self, values: Dict[str, float]) -> float:
        """Soma todos os valores de um dicionário, ignorando
        chaves ausentes ou valores nulos.
        """
        return sum(v for v in values.values() if v is not None)

    @property
    def total_receitas_previsao(self) -> float:
        """Totaliza as receitas previstas do mês."""
        return self._sum_values(self.previsao_receitas)

    @property
    def total_despesas_previsao(self) -> float:
        """Totaliza as despesas previstas do mês."""
        return self._sum_values(self.previsao_despesas)

    @property
    def saldo_mensal_previsao(self) -> float:
        """Calcula a diferença entre entradas e saídas previstas."""
        return self.total_receitas_previsao - self.total_despesas_previsao

    @property
    def saldo_acumulado_previsao(self) -> float:
        """Calcula o saldo acumulado previsto: 1 (entradas - saídas)
        somado ao saldo anterior.
        """
        return self.saldo_mensal_previsao + self.saldo_anterior

    @property
    def saldo_final_previsao(self) -> float:
        """Calcula o saldo final previsto: saldo acumulado + empréstimo.
        Se não houver empréstimo, assume zero.
        """
        return self.saldo_acumulado_previsao + (self.emprestimo or 0.0)

    # Métodos equivalentes para valores realizados (caso fornecidos)
    @property
    def total_receitas_realizado(self) -> Optional[float]:
        if self.realizado_receitas is None:
            return None
        return self._sum_values(self.realizado_receitas)

    @property
    def total_despesas_realizado(self) -> Optional[float]:
        if self.realizado_despesas is None:
            return None
        return self._sum_values(self.realizado_despesas)

    @property
    def saldo_mensal_realizado(self) -> Optional[float]:
        if self.realizado_receitas is None or self.realizado_despesas is None:
            return None
        return self.total_receitas_realizado - self.total_despesas_realizado

    @property
    def saldo_acumulado_realizado(self) -> Optional[float]:
        if self.saldo_mensal_realizado is None:
            return None
        return self.saldo_mensal_realizado + self.saldo_anterior

    @property
    def saldo_final_realizado(self) -> Optional[float]:
        if self.saldo_acumulado_realizado is None:
            return None
        return self.saldo_acumulado_realizado + (self.emprestimo or 0.0)

    def editar_despesa(self, categoria: str, novo_valor: float, previsao: bool = True) -> None:
        """Permite editar o valor de uma despesa.

        :param categoria: nome da despesa a ser alterada
        :param novo_valor: novo valor numérico para a despesa
        :param previsao: se True, altera a despesa prevista; caso
            contrário, altera a despesa realizada (se existir).
        """
        if previsao:
            self.previsao_despesas[categoria] = novo_valor
        else:
            if self.realizado_despesas is None:
                self.realizado_despesas = {}
            self.realizado_despesas[categoria] = novo_valor

    def editar_receita(self, categoria: str, novo_valor: float, previsao: bool = True) -> None:
        """Permite editar o valor de uma receita.

        :param categoria: nome da receita a ser alterada
        :param novo_valor: novo valor numérico para a receita
        :param previsao: se True, altera a receita prevista; caso
            contrário, altera a receita realizada (se existir).
        """
        if previsao:
            self.previsao_receitas[categoria] = novo_valor
        else:
            if self.realizado_receitas is None:
                self.realizado_receitas = {}
            self.realizado_receitas[categoria] = novo_valor

    def __repr__(self) -> str:
        return (
            f"MonthCashFlow(name={self.name}, "
            f"total_receitas_previsao={self.total_receitas_previsao:.2f}, "
            f"total_despesas_previsao={self.total_despesas_previsao:.2f}, "
            f"saldo_final_previsao={self.saldo_final_previsao:.2f})"
        )


class CashFlowModule:
    """Agrega vários objetos MonthCashFlow para representar o fluxo
    de caixa de uma sequência de meses.

    Este gerenciador cuida de calcular saldos anteriores de cada mês
    com base no saldo final do mês anterior. Ele também fornece uma
    visão consolidada dos saldos finais por mês.
    """

    def __init__(self, saldo_inicial: float = 0.0, db_connection=None) -> None:
        self.months: List[MonthCashFlow] = []
        self.saldo_inicial = saldo_inicial
        self.db_connection = db_connection

    def adicionar_mes(self, month: MonthCashFlow) -> None:
        """Adiciona um novo mês ao módulo. O saldo anterior do mês
        será atualizado automaticamente quando todos os meses forem
        recalculados via ``recalcular_saldos``.
        """
        self.months.append(month)
        # Ajusta o saldo anterior imediatamente se for o primeiro mês
        if len(self.months) == 1:
            month.saldo_anterior = self.saldo_inicial
        else:
            # O saldo anterior do novo mês é o saldo final do mês anterior
            prev_final = self.months[-2].saldo_final_previsao
            month.saldo_anterior = prev_final

    def recalcular_saldos(self) -> None:
        """Recalcula os saldos anteriores e finais de todos os meses.

        Esta função é útil quando valores de receitas ou despesas são
        editados após a inserção dos meses no módulo. Ela garante que
        qualquer alteração reflita corretamente no saldo final dos meses
        subsequentes.
        """
        prev_final = self.saldo_inicial
        for month in self.months:
            month.saldo_anterior = prev_final
            prev_final = month.saldo_final_previsao

    def obter_resumo(self) -> Dict[str, Dict[str, float]]:
        """Retorna um dicionário com o saldo final de cada mês.

        O formato retornado é: {nome_mes: {"saldo_final": valor}}.
        """
        resumo: Dict[str, Dict[str, float]] = {}
        for month in self.months:
            resumo[month.name] = {
                "total_receitas_previsao": month.total_receitas_previsao,
                "total_despesas_previsao": month.total_despesas_previsao,
                "saldo_mensal_previsao": month.saldo_mensal_previsao,
                "saldo_acumulado_previsao": month.saldo_acumulado_previsao,
                "saldo_final_previsao": month.saldo_final_previsao,
            }
        return resumo

    def importar_transacoes_banco(self, mes_nome: str, ano: int = None) -> Dict[str, float]:
        """
        Importa transações reais do banco de dados para um mês específico
        
        Args:
            mes_nome: Nome do mês (ex: "Janeiro", "Fevereiro")
            ano: Ano das transações (padrão: ano atual)
            
        Returns:
            Dict com receitas e despesas importadas
        """
        if not self.db_connection:
            return {"receitas": {}, "despesas": {}}
            
        if ano is None:
            ano = datetime.now().year
            
        # Mapear nomes de meses para números
        meses_map = {
            "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
            "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
            "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
        }
        
        mes_numero = meses_map.get(mes_nome)
        if not mes_numero:
            return {"receitas": {}, "despesas": {}}
            
        try:
            # Buscar transações do banco
            transacoes_df = self.db_connection.get_financeiro()
            
            if transacoes_df.empty:
                return {"receitas": {}, "despesas": {}}
                
            # Converter coluna data
            transacoes_df['data'] = pd.to_datetime(transacoes_df['data'])
            
            # Filtrar por mês e ano
            mask = (
                (transacoes_df['data'].dt.month == mes_numero) & 
                (transacoes_df['data'].dt.year == ano)
            )
            transacoes_mes = transacoes_df[mask]
            
            receitas_importadas = {}
            despesas_importadas = {}
            
            # Processar receitas
            receitas = transacoes_mes[
                (transacoes_mes['tipo'].isin(['receita', 'Receita'])) &
                (transacoes_mes['status'] == 'Recebido')
            ]
            
            for _, transacao in receitas.iterrows():
                categoria = self._mapear_categoria_receita(transacao['categoria'])
                if categoria not in receitas_importadas:
                    receitas_importadas[categoria] = 0.0
                receitas_importadas[categoria] += float(transacao['valor'])
            
            # Processar despesas
            despesas = transacoes_mes[
                (transacoes_mes['tipo'].isin(['despesa', 'Despesa'])) &
                (transacoes_mes['status'] == 'Pago')
            ]
            
            for _, transacao in despesas.iterrows():
                categoria = self._mapear_categoria_despesa(transacao['categoria'])
                if categoria not in despesas_importadas:
                    despesas_importadas[categoria] = 0.0
                despesas_importadas[categoria] += float(transacao['valor'])
                
            return {"receitas": receitas_importadas, "despesas": despesas_importadas}
            
        except Exception as e:
            print(f"Erro ao importar transações: {str(e)}")
            return {"receitas": {}, "despesas": {}}
    
    def _mapear_categoria_receita(self, categoria_banco: str) -> str:
        """Mapeia categorias do banco para categorias do fluxo de caixa"""
        mapeamento = {
            "Serviços de Organização": "Contas a receber-vendas realizadas",
            "Venda de Produtos": "Contas a receber-vendas realizadas", 
            "Vendas": "Contas a receber-vendas realizadas",
            "Comissão sobre Fornecedores": "Outros recebimentos",
            "Serviços Adicionais": "Outros recebimentos"
        }
        return mapeamento.get(categoria_banco, "Outros recebimentos")
    
    def _mapear_categoria_despesa(self, categoria_banco: str) -> str:
        """Mapeia categorias do banco para categorias do fluxo de caixa"""
        mapeamento = {
            "Pagamento Equipe/Assistentes": "Pró Labore",
            "Pagamento Parceiros/Fornecedores": "Fornecedores",
            "Custos Operacionais": "Fornecedores",
            "Custos Administrativos": "MEI",
            "Assistente": "Pró Labore",
            "Fornecedor": "Fornecedores"
        }
        return mapeamento.get(categoria_banco, "Fornecedores")
    
    def sincronizar_mes_com_banco(self, mes_nome: str, ano: int = None) -> bool:
        """
        Sincroniza um mês do fluxo de caixa com dados reais do banco
        
        Args:
            mes_nome: Nome completo do mês (ex: "Janeiro 2024")
            ano: Ano (extraído do nome se não fornecido)
            
        Returns:
            bool: True se sincronizado com sucesso
        """
        try:
            # Extrair mês e ano do nome se necessário
            if ano is None and ' ' in mes_nome:
                partes = mes_nome.split(' ')
                if len(partes) >= 2:
                    mes_nome_limpo = partes[0]
                    ano = int(partes[1])
                else:
                    mes_nome_limpo = mes_nome
                    ano = datetime.now().year
            else:
                mes_nome_limpo = mes_nome
                if ano is None:
                    ano = datetime.now().year
            
            # Encontrar o mês no fluxo de caixa
            mes_obj = None
            for m in self.months:
                if mes_nome in m.name or mes_nome_limpo in m.name:
                    mes_obj = m
                    break
            
            if not mes_obj:
                return False
                
            # Importar dados do banco
            dados_importados = self.importar_transacoes_banco(mes_nome_limpo, ano)
            
            # Atualizar valores realizados
            if dados_importados["receitas"]:
                if mes_obj.realizado_receitas is None:
                    mes_obj.realizado_receitas = {}
                mes_obj.realizado_receitas.update(dados_importados["receitas"])
            
            if dados_importados["despesas"]:
                if mes_obj.realizado_despesas is None:
                    mes_obj.realizado_despesas = {}
                mes_obj.realizado_despesas.update(dados_importados["despesas"])
            
            return True
            
        except Exception as e:
            print(f"Erro ao sincronizar mês {mes_nome}: {str(e)}")
            return False

    def __repr__(self) -> str:
        parts = [f"Saldo inicial: {self.saldo_inicial:.2f}\n"]
        for month in self.months:
            parts.append(
                f"{month.name}: receitas={month.total_receitas_previsao:.2f}, "
                f"despesas={month.total_despesas_previsao:.2f}, "
                f"saldo_final={month.saldo_final_previsao:.2f}"
            )
        return "\n".join(parts)