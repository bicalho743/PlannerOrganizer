import pandas as pd
from datetime import datetime
import os

class Database:
    def __init__(self):
        self.clientes_file = 'clientes.csv'
        self.propostas_file = 'propostas.csv'
        self.financeiro_file = 'financeiro.csv'
        self.produtos_file = 'produtos.csv'
        
        # Criar arquivos se não existirem
        self._create_if_not_exists()
    
    def _create_if_not_exists(self):
        if not os.path.exists(self.clientes_file):
            pd.DataFrame(columns=[
                'id', 'nome', 'email', 'telefone', 'endereco', 
                'data_cadastro'
            ]).to_csv(self.clientes_file, index=False)
            
        if not os.path.exists(self.propostas_file):
            pd.DataFrame(columns=[
                'id', 'cliente_id', 'descricao', 'valor', 
                'status', 'data_proposta'
            ]).to_csv(self.propostas_file, index=False)
            
        if not os.path.exists(self.financeiro_file):
            pd.DataFrame(columns=[
                'id', 'tipo', 'descricao', 'valor', 'data',
                'categoria', 'referencia_id'
            ]).to_csv(self.financeiro_file, index=False)
            
        if not os.path.exists(self.produtos_file):
            pd.DataFrame(columns=[
                'id', 'nome', 'descricao', 'valor', 'quantidade',
                'data_cadastro'
            ]).to_csv(self.produtos_file, index=False)

    def get_clientes(self):
        return pd.read_csv(self.clientes_file)
    
    def add_cliente(self, nome, email, telefone, endereco):
        df = self.get_clientes()
        novo_id = len(df) + 1
        novo_cliente = pd.DataFrame([{
            'id': novo_id,
            'nome': nome,
            'email': email,
            'telefone': telefone,
            'endereco': endereco,
            'data_cadastro': datetime.now().strftime('%Y-%m-%d')
        }])
        df = pd.concat([df, novo_cliente], ignore_index=True)
        df.to_csv(self.clientes_file, index=False)
        return novo_id

    def get_propostas(self):
        return pd.read_csv(self.propostas_file)
    
    def add_proposta(self, cliente_id, descricao, valor, status):
        df = self.get_propostas()
        novo_id = len(df) + 1
        nova_proposta = pd.DataFrame([{
            'id': novo_id,
            'cliente_id': cliente_id,
            'descricao': descricao,
            'valor': valor,
            'status': status,
            'data_proposta': datetime.now().strftime('%Y-%m-%d')
        }])
        df = pd.concat([df, nova_proposta], ignore_index=True)
        df.to_csv(self.propostas_file, index=False)
        return novo_id

    def get_financeiro(self):
        return pd.read_csv(self.financeiro_file)
    
    def add_transacao(self, tipo, descricao, valor, categoria, referencia_id=None):
        df = self.get_financeiro()
        novo_id = len(df) + 1
        nova_transacao = pd.DataFrame([{
            'id': novo_id,
            'tipo': tipo,
            'descricao': descricao,
            'valor': valor,
            'data': datetime.now().strftime('%Y-%m-%d'),
            'categoria': categoria,
            'referencia_id': referencia_id
        }])
        df = pd.concat([df, nova_transacao], ignore_index=True)
        df.to_csv(self.financeiro_file, index=False)
        return novo_id

    def get_produtos(self):
        return pd.read_csv(self.produtos_file)
    
    def add_produto(self, nome, descricao, valor, quantidade):
        df = self.get_produtos()
        novo_id = len(df) + 1
        novo_produto = pd.DataFrame([{
            'id': novo_id,
            'nome': nome,
            'descricao': descricao,
            'valor': valor,
            'quantidade': quantidade,
            'data_cadastro': datetime.now().strftime('%Y-%m-%d')
        }])
        df = pd.concat([df, novo_produto], ignore_index=True)
        df.to_csv(self.produtos_file, index=False)
        return novo_id
