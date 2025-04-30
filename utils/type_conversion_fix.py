"""
Este módulo contém funções para corrigir problemas de conversão de tipos
entre numpy e Python padrão.
"""
import os
import sys

def fix_numpy_int64_bug():
    """
    Corrige o bug 'can't adapt type numpy.int64' adicionando um adaptador ao PostgreSQL
    
    Deve ser chamado no início da aplicação, antes de qualquer conexão com o banco de dados.
    """
    try:
        # Primeiro verificar se numpy está instalado
        import numpy
        
        # Verificar se psycopg2 está instalado
        import psycopg2
        import psycopg2.extensions
        
        # Registrar adaptador para converter numpy.int64 em int nativo
        def adapt_numpy_int64(numpy_int64):
            return psycopg2.extensions.AsIs(int(numpy_int64))
        
        # Registrar os adaptadores para todos os tipos do numpy que podem aparecer
        psycopg2.extensions.register_adapter(numpy.int64, adapt_numpy_int64)
        
        # Registrar também para outros tipos se necessário
        if hasattr(numpy, 'int32'):
            psycopg2.extensions.register_adapter(numpy.int32, adapt_numpy_int64)
        
        if hasattr(numpy, 'int16'):
            psycopg2.extensions.register_adapter(numpy.int16, adapt_numpy_int64)
        
        if hasattr(numpy, 'int8'):
            psycopg2.extensions.register_adapter(numpy.int8, adapt_numpy_int64)
        
        print("Adaptadores para numpy.int* registrados com sucesso para PostgreSQL")
        return True
    except ImportError as e:
        print(f"Erro ao registrar adaptadores: {str(e)}")
        return False
    except Exception as e:
        print(f"Erro desconhecido ao registrar adaptadores: {str(e)}")
        return False

def ensure_int(value):
    """
    Garante que o valor seja um inteiro Python padrão, mesmo que seja numpy.int64
    """
    if value is None:
        return None
    return int(value)