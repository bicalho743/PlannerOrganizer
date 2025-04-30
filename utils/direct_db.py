"""
Módulo de acesso direto ao banco de dados, sem usar SQLAlchemy
Este módulo é usado como fallback quando o ORM apresenta problemas no Render
"""

import os
import psycopg2
import psycopg2.extras
from datetime import datetime

class DirectDB:
    """
    Classe para acesso direto ao banco de dados usando psycopg2
    Usada como fallback quando o SQLAlchemy apresenta problemas no Render
    """
    
    def __init__(self, usuario_id=None):
        """
        Inicializa conexão direta com o banco de dados
        
        Args:
            usuario_id (str, optional): ID do usuário para filtrar consultas por isolamento de dados
        """
        self.usuario_id = usuario_id
        self.connection = None
        self.connect()
    
    def connect(self):
        """Estabelece conexão com o banco de dados"""
        try:
            self.connection = psycopg2.connect(os.environ.get('DATABASE_URL'))
            self.connection.autocommit = True
            return True
        except Exception as e:
            print(f"Erro ao conectar diretamente ao banco: {str(e)}")
            return False
    
    def close(self):
        """Fecha a conexão com o banco de dados"""
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query, params=None):
        """
        Executa uma consulta SQL e retorna todos os resultados
        
        Args:
            query (str): Consulta SQL a ser executada
            params (dict, optional): Parâmetros para a consulta
            
        Returns:
            list: Lista de dicionários com os resultados da consulta
        """
        try:
            if not self.connection or self.connection.closed:
                self.connect()
                
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(query, params or {})
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            print(f"Erro ao executar query direta: {str(e)}")
            return []
    
    def execute_action(self, query, params=None):
        """
        Executa uma ação SQL (INSERT, UPDATE, DELETE) e retorna o número de linhas afetadas
        
        Args:
            query (str): Ação SQL a ser executada
            params (dict, optional): Parâmetros para a ação
            
        Returns:
            int: Número de linhas afetadas pela ação
        """
        try:
            if not self.connection or self.connection.closed:
                self.connect()
                
            cursor = self.connection.cursor()
            cursor.execute(query, params or {})
            rowcount = cursor.rowcount
            cursor.close()
            return rowcount
        except Exception as e:
            print(f"Erro ao executar ação direta: {str(e)}")
            return 0
    
    def get_clientes(self):
        """
        Obtém todos os clientes do usuário atual via SQL direto
        
        Returns:
            list: Lista de dicionários com informações dos clientes
        """
        query = """
            SELECT * FROM clientes 
            WHERE usuario_id = %(usuario_id)s
            ORDER BY nome
        """
        return self.execute_query(query, {'usuario_id': self.usuario_id})
    
    def get_cliente(self, cliente_id):
        """
        Obtém um cliente específico via SQL direto
        
        Args:
            cliente_id (int): ID do cliente a ser recuperado
            
        Returns:
            dict: Dicionário com informações do cliente ou None se não encontrado
        """
        query = """
            SELECT * FROM clientes 
            WHERE id = %(cliente_id)s AND usuario_id = %(usuario_id)s
        """
        results = self.execute_query(query, {
            'cliente_id': cliente_id,
            'usuario_id': self.usuario_id
        })
        
        return results[0] if results else None
    
    def get_propostas(self, status=None):
        """
        Obtém propostas do usuário atual via SQL direto
        
        Args:
            status (str, optional): Filtrar por status específico
            
        Returns:
            list: Lista de dicionários com informações das propostas
        """
        if status:
            query = """
                SELECT p.*, c.nome as cliente_nome 
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.usuario_id = %(usuario_id)s AND p.status = %(status)s
                ORDER BY p.data_proposta DESC
            """
            params = {'usuario_id': self.usuario_id, 'status': status}
        else:
            query = """
                SELECT p.*, c.nome as cliente_nome 
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.usuario_id = %(usuario_id)s
                ORDER BY p.data_proposta DESC
            """
            params = {'usuario_id': self.usuario_id}
            
        return self.execute_query(query, params)
    
    def get_proposta(self, proposta_id):
        """
        Obtém uma proposta específica via SQL direto
        
        Args:
            proposta_id (int): ID da proposta a ser recuperada
            
        Returns:
            dict: Dicionário com informações da proposta ou None se não encontrada
        """
        query = """
            SELECT p.*, c.nome as cliente_nome 
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = %(proposta_id)s AND p.usuario_id = %(usuario_id)s
        """
        results = self.execute_query(query, {
            'proposta_id': proposta_id,
            'usuario_id': self.usuario_id
        })
        
        return results[0] if results else None
    
    def update_database_schema(self):
        """
        Atualiza o esquema do banco de dados com comandos SQL diretos
        Usado para corrigir problemas de esquema no Render
        
        Returns:
            dict: Resultado da operação
        """
        try:
            # Verificar e adicionar coluna usuario_id em clientes
            self.execute_action("""
                DO $$
                BEGIN
                    BEGIN
                        ALTER TABLE clientes ADD COLUMN usuario_id VARCHAR;
                    EXCEPTION
                        WHEN duplicate_column THEN
                            NULL; -- Coluna já existe, não fazer nada
                    END;
                END $$;
            """)
            
            # Atualizar valores nulos
            self.execute_action("""
                UPDATE clientes SET usuario_id = '7NDbX2b7hAcFqWzwsgi2BXiFZad2' 
                WHERE usuario_id IS NULL;
            """)
            
            # Adicionar coluna usuario_id em propostas
            self.execute_action("""
                DO $$
                BEGIN
                    BEGIN
                        ALTER TABLE propostas ADD COLUMN usuario_id VARCHAR;
                    EXCEPTION
                        WHEN duplicate_column THEN
                            NULL; -- Coluna já existe, não fazer nada
                    END;
                END $$;
            """)
            
            # Atualizar valores nulos em propostas
            self.execute_action("""
                UPDATE propostas SET usuario_id = '7NDbX2b7hAcFqWzwsgi2BXiFZad2' 
                WHERE usuario_id IS NULL;
            """)
            
            # Criar índices para melhorar performance
            self.execute_action("""
                CREATE INDEX IF NOT EXISTS idx_clientes_usuario_id ON clientes (usuario_id);
                CREATE INDEX IF NOT EXISTS idx_propostas_usuario_id ON propostas (usuario_id);
            """)
            
            # Verificar estrutura final
            result = self.execute_query("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'clientes'
                ORDER BY column_name;
            """)
            
            colunas = [item['column_name'] for item in result]
            tem_usuario_id = 'usuario_id' in colunas
            
            return {
                'status': 'success' if tem_usuario_id else 'error',
                'message': 'Esquema atualizado com sucesso' if tem_usuario_id else 'Falha ao atualizar esquema',
                'colunas': colunas
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erro ao atualizar esquema: {str(e)}'
            }