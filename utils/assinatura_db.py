"""
Gerenciamento de assinaturas no banco de dados
"""
import os
from datetime import datetime, timedelta
import json
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text

from utils.database import Database

db = Database()

# Função para registrar uma nova assinatura
def registrar_assinatura(usuario_id, plano, customer_id=None, subscription_id=None, 
                         status='ativo', data_inicio=None, data_fim=None):
    """
    Registra uma nova assinatura para o usuário
    
    Args:
        usuario_id: ID do usuário
        plano: Nome do plano (Mensal, Anual, Vitalício)
        customer_id: ID do cliente no Stripe
        subscription_id: ID da assinatura no Stripe
        status: Status da assinatura (ativo, cancelado, pendente)
        data_inicio: Data de início da assinatura
        data_fim: Data de término da assinatura
        
    Returns:
        dict: Resultado da operação
    """
    try:
        # Verificar se já existe uma assinatura para este usuário
        assinatura_existente = obter_assinatura_usuario(usuario_id)
        
        if assinatura_existente.get('sucesso'):
            # Atualizar assinatura existente
            return atualizar_status_assinatura(
                usuario_id=usuario_id,
                status=status,
                plano=plano,
                customer_id=customer_id,
                subscription_id=subscription_id,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
        
        # Se não existe, criar nova assinatura
        # Preparar datas
        if not data_inicio:
            data_inicio = datetime.now()
            
        if not data_fim and plano.lower() != 'vitalicio':
            # Definir data de término com base no plano
            if plano.lower() == 'mensal':
                data_fim = data_inicio + timedelta(days=30)
            elif plano.lower() == 'anual':
                data_fim = data_inicio + timedelta(days=365)
                
        # Preparar SQL para inserção
        sql = """
        INSERT INTO assinaturas (
            usuario_id, plano, customer_id, subscription_id, 
            status, data_inicio, data_fim, data_criacao
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        # Executar SQL
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql, (
                usuario_id, 
                plano, 
                customer_id, 
                subscription_id, 
                status, 
                data_inicio, 
                data_fim,
                datetime.now()
            ))
            conn.commit()
            
            return {
                'sucesso': True,
                'mensagem': 'Assinatura registrada com sucesso'
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'sucesso': False,
            'mensagem': f'Erro ao registrar assinatura: {str(e)}'
        }

# Função para obter uma assinatura
def obter_assinatura_usuario(usuario_id):
    """
    Obtém a assinatura de um usuário
    
    Args:
        usuario_id: ID do usuário
        
    Returns:
        dict: Informações da assinatura
    """
    try:
        # Preparar SQL para consulta
        sql = """
        SELECT * FROM assinaturas 
        WHERE usuario_id = %s 
        ORDER BY data_criacao DESC 
        LIMIT 1
        """
        
        # Executar SQL
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql, (usuario_id,))
            result = cursor.fetchone()
            
            if not result:
                return {
                    'sucesso': False,
                    'mensagem': 'Nenhuma assinatura encontrada para este usuário'
                }
                
            # Obter nomes das colunas
            colunas = [desc[0] for desc in cursor.description]
            
            # Criar dicionário com os dados
            assinatura = dict(zip(colunas, result))
            
            # Verificar se a assinatura está ativa
            if assinatura.get('status') == 'ativo':
                # Para assinaturas vitalícias, sempre está ativa
                if assinatura.get('plano', '').lower() == 'vitalicio':
                    dias_restantes = float('inf')
                else:
                    # Verificar se ainda está no período ativo
                    data_fim = assinatura.get('data_fim')
                    
                    if data_fim:
                        if isinstance(data_fim, str):
                            data_fim = datetime.strptime(data_fim, '%Y-%m-%d %H:%M:%S')
                            
                        hoje = datetime.now()
                        
                        if data_fim > hoje:
                            # Ainda está no período ativo
                            dias_restantes = (data_fim - hoje).days
                        else:
                            # Expirou
                            dias_restantes = 0
                            # Atualizar status para expirado
                            atualizar_status_assinatura(usuario_id, 'expirado')
                            assinatura['status'] = 'expirado'
                    else:
                        # Sem data de término, consideramos ativo
                        dias_restantes = float('inf')
                
                assinatura['dias_restantes'] = dias_restantes
            else:
                assinatura['dias_restantes'] = 0
            
            return {
                'sucesso': True,
                'assinatura': assinatura
            }
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'sucesso': False,
            'mensagem': f'Erro ao obter assinatura: {str(e)}'
        }

# Função para atualizar o status de uma assinatura
def atualizar_status_assinatura(usuario_id, status, plano=None, customer_id=None, 
                              subscription_id=None, data_inicio=None, data_fim=None):
    """
    Atualiza o status de uma assinatura
    
    Args:
        usuario_id: ID do usuário
        status: Novo status da assinatura
        plano: Nome do plano (opcional)
        customer_id: ID do cliente no Stripe (opcional)
        subscription_id: ID da assinatura no Stripe (opcional)
        data_inicio: Nova data de início (opcional)
        data_fim: Nova data de término (opcional)
        
    Returns:
        dict: Resultado da operação
    """
    try:
        # Construir SQL para atualização dinâmica
        campos_atualizacao = []
        valores = []
        
        # Adicionar campos a serem atualizados
        if status:
            campos_atualizacao.append("status = %s")
            valores.append(status)
            
        if plano:
            campos_atualizacao.append("plano = %s")
            valores.append(plano)
            
        if customer_id:
            campos_atualizacao.append("customer_id = %s")
            valores.append(customer_id)
            
        if subscription_id:
            campos_atualizacao.append("subscription_id = %s")
            valores.append(subscription_id)
            
        if data_inicio:
            campos_atualizacao.append("data_inicio = %s")
            valores.append(data_inicio)
            
        if data_fim:
            campos_atualizacao.append("data_fim = %s")
            valores.append(data_fim)
        
        # Verificar se há campos para atualizar
        if not campos_atualizacao:
            return {
                'sucesso': False,
                'mensagem': 'Nenhum campo fornecido para atualização'
            }
            
        # Adicionar data de atualização
        campos_atualizacao.append("data_atualizacao = %s")
        valores.append(datetime.now())
        
        # Adicionar ID do usuário ao final dos valores
        valores.append(usuario_id)
        
        # Construir SQL completo
        sql = f"""
        UPDATE assinaturas 
        SET {', '.join(campos_atualizacao)} 
        WHERE usuario_id = %s
        """
        
        # Executar SQL
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql, valores)
            conn.commit()
            
            # Verificar se alguma linha foi afetada
            if cursor.rowcount > 0:
                return {
                    'sucesso': True,
                    'mensagem': f'Status da assinatura atualizado para {status}'
                }
            else:
                # Se nenhuma linha foi afetada, pode ser que não exista assinatura
                # Neste caso, tenta criar uma nova
                if status and plano:
                    return registrar_assinatura(
                        usuario_id=usuario_id,
                        plano=plano,
                        customer_id=customer_id,
                        subscription_id=subscription_id,
                        status=status,
                        data_inicio=data_inicio,
                        data_fim=data_fim
                    )
                else:
                    return {
                        'sucesso': False,
                        'mensagem': 'Nenhuma assinatura encontrada para atualização'
                    }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'sucesso': False,
            'mensagem': f'Erro ao atualizar status da assinatura: {str(e)}'
        }

# Função para cancelar uma assinatura
def cancelar_assinatura(usuario_id, motivo=None):
    """
    Cancela a assinatura de um usuário
    
    Args:
        usuario_id: ID do usuário
        motivo: Motivo do cancelamento (opcional)
        
    Returns:
        dict: Resultado da operação
    """
    try:
        # Obter assinatura atual
        resultado_assinatura = obter_assinatura_usuario(usuario_id)
        
        if not resultado_assinatura.get('sucesso'):
            return {
                'sucesso': False,
                'mensagem': 'Nenhuma assinatura encontrada para cancelamento'
            }
            
        assinatura = resultado_assinatura.get('assinatura')
        
        # Verificar se já está cancelada
        if assinatura.get('status') == 'cancelado':
            return {
                'sucesso': True,
                'mensagem': 'Assinatura já cancelada'
            }
            
        # Atualizar status para cancelado
        resultado = atualizar_status_assinatura(
            usuario_id=usuario_id,
            status='cancelado'
        )
        
        if resultado.get('sucesso'):
            # Registrar motivo do cancelamento, se fornecido
            if motivo:
                # SQL para registrar motivo
                sql = """
                UPDATE assinaturas 
                SET motivo_cancelamento = %s 
                WHERE usuario_id = %s
                """
                
                # Executar SQL
                conn = db.engine.raw_connection()
                cursor = conn.cursor()
                
                try:
                    cursor.execute(sql, (motivo, usuario_id))
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    # Não repassamos o erro, pois o cancelamento já foi feito
                    print(f"Erro ao registrar motivo do cancelamento: {str(e)}")
                finally:
                    cursor.close()
                    conn.close()
            
            return {
                'sucesso': True,
                'mensagem': 'Assinatura cancelada com sucesso'
            }
        else:
            return resultado
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'sucesso': False,
            'mensagem': f'Erro ao cancelar assinatura: {str(e)}'
        }

# Função para verificar se o usuário tem uma assinatura ativa
def verificar_assinatura_ativa(usuario_id):
    """
    Verifica se o usuário tem uma assinatura ativa
    
    Args:
        usuario_id: ID do usuário
        
    Returns:
        dict: Resultado da verificação com informações sobre a assinatura
    """
    try:
        # Obter assinatura
        resultado = obter_assinatura_usuario(usuario_id)
        
        if not resultado.get('sucesso'):
            return {
                'sucesso': True,
                'assinatura_ativa': False,
                'mensagem': 'Nenhuma assinatura encontrada'
            }
            
        assinatura = resultado.get('assinatura')
        
        # Obter status atual
        status = assinatura.get('status')
        
        # Verificar status
        is_ativo = status == 'ativo'
        is_trial = status == 'trial'
        
        # Também considerar como ativo se estiver em período de teste
        assinatura_ativa = is_ativo or is_trial
        
        # Verificar data de término para assinaturas ativas e de teste
        if assinatura_ativa and 'data_fim' in assinatura:
            data_fim = assinatura.get('data_fim')
            
            if data_fim:
                # Converter para datetime se for string
                if isinstance(data_fim, str):
                    try:
                        data_fim = datetime.strptime(data_fim, '%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                
                # Verificar se ainda está no período ativo
                hoje = datetime.now()
                if data_fim < hoje:
                    # Se expirou, atualizar status
                    atualizar_status_assinatura(usuario_id, 'expirado')
                    assinatura['status'] = 'expirado'
                    assinatura_ativa = False
        
        return {
            'sucesso': True,
            'assinatura_ativa': assinatura_ativa,
            'tipo': assinatura.get('status'),
            'plano': assinatura.get('plano'),
            'dias_restantes': assinatura.get('dias_restantes', 0),
            'assinatura': assinatura if assinatura_ativa else None
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Erro ao verificar assinatura ativa: {str(e)}")
        
        return {
            'sucesso': False,
            'assinatura_ativa': False,
            'mensagem': f'Erro ao verificar assinatura: {str(e)}'
        }

# Função para criar a tabela de assinaturas, se não existir
def criar_tabela_assinaturas():
    """
    Cria a tabela de assinaturas no banco de dados, se não existir
    """
    try:
        # Verificar se a tabela já existe
        sql_verificar = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'assinaturas'
        )
        """
        
        # Função principal de criação de tabela usando SQLAlchemy
        try:
            # Usar SQLAlchemy em vez da conexão direta
            from sqlalchemy import text
            import utils.database as database
            
            # Verificar se a tabela existe usando SQLAlchemy global
            with database.engine.connect() as conexao:
                resultado = conexao.execute(text(sql_verificar))
                tabela_existe = resultado.scalar()
            
            # Se a tabela já existe, não fazemos nada
            if tabela_existe:
                return {
                    'sucesso': True,
                    'mensagem': 'Tabela de assinaturas já existe'
                }
                
            # Criar tabela
            sql_criar = """
            CREATE TABLE assinaturas (
                id SERIAL PRIMARY KEY,
                usuario_id VARCHAR(255) NOT NULL,
                plano VARCHAR(50) NOT NULL,
                customer_id VARCHAR(255),
                subscription_id VARCHAR(255),
                status VARCHAR(50) NOT NULL DEFAULT 'ativo',
                data_inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                data_fim TIMESTAMP,
                data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                motivo_cancelamento TEXT
            )
            """
            
            # Criar índices
            sql_indices = """
            CREATE INDEX idx_assinaturas_usuario_id ON assinaturas(usuario_id);
            CREATE INDEX idx_assinaturas_status ON assinaturas(status);
            """
            
            # Executar os comandos SQL usando SQLAlchemy global
            with database.engine.begin() as conexao:
                conexao.execute(text(sql_criar))
                conexao.execute(text(sql_indices))
            
            return {
                'sucesso': True,
                'mensagem': 'Tabela de assinaturas criada com sucesso'
            }
        except Exception as inner_e:
            # Capturar exceção interna durante a criação da tabela
            import traceback
            traceback.print_exc()
            
            return {
                'sucesso': False,
                'mensagem': f'Erro ao criar tabela de assinaturas: {str(inner_e)}'
            }
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'sucesso': False,
            'mensagem': f'Erro ao criar tabela de assinaturas: {str(e)}'
        }

# Função para iniciar um período de teste
def iniciar_periodo_teste(usuario_id, dias=7):
    """
    Inicia um período de teste para o usuário
    
    Args:
        usuario_id: ID do usuário
        dias: Número de dias do período de teste
        
    Returns:
        dict: Resultado da operação
    """
    try:
        # Verificar se já existe uma assinatura
        resultado_assinatura = obter_assinatura_usuario(usuario_id)
        
        if resultado_assinatura.get('sucesso'):
            # Já existe uma assinatura, não fazer nada
            return {
                'sucesso': True,
                'mensagem': 'Usuário já possui uma assinatura'
            }
            
        # Criar nova assinatura com período de teste
        data_inicio = datetime.now()
        data_fim = data_inicio + timedelta(days=dias)
        
        return registrar_assinatura(
            usuario_id=usuario_id,
            plano='Teste',
            status='trial',
            data_inicio=data_inicio,
            data_fim=data_fim
        )
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'sucesso': False,
            'mensagem': f'Erro ao iniciar período de teste: {str(e)}'
        }

# Criar a tabela de assinaturas ao inicializar o módulo
resultado_criacao = criar_tabela_assinaturas()
print(f"Inicialização da tabela de assinaturas: {resultado_criacao.get('mensagem')}")