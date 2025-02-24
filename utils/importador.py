import pandas as pd
import streamlit as st
from datetime import datetime
import io

def validar_data(data_str):
    """Converte string de data para objeto datetime"""
    if pd.isna(data_str):
        return None
    try:
        return datetime.strptime(str(data_str), '%d/%m/%Y').date()
    except ValueError:
        try:
            return datetime.strptime(str(data_str), '%Y-%m-%d').date()
        except ValueError:
            return None

def importar_cadastros(arquivo, tipo_cadastro, db):
    """Importa cadastros de um arquivo CSV"""
    try:
        df = pd.read_csv(arquivo, encoding='utf-8')
        
        # Validar colunas obrigatórias
        colunas_base = ['nome', 'telefone', 'email']
        for col in colunas_base:
            if col not in df.columns:
                return False, f"Coluna obrigatória '{col}' não encontrada no arquivo"

        sucessos = 0
        erros = []
        
        for _, row in df.iterrows():
            try:
                dados = {
                    'nome': row['nome'],
                    'telefone': row['telefone'] if not pd.isna(row['telefone']) else None,
                    'email': row['email'] if not pd.isna(row['email']) else None,
                    'observacoes': row.get('observacoes', None),
                    'pix': row.get('pix', None)
                }

                if tipo_cadastro == "Cliente":
                    dados.update({
                        'data_aniversario': validar_data(row.get('data_aniversario')),
                        'origem_cliente': row.get('origem_cliente'),
                        'tipo_cliente': row.get('tipo_cliente', 'PF')
                    })
                    db.add_cliente(**dados)

                elif tipo_cadastro == "Fornecedor":
                    dados.update({
                        'categoria': row.get('categoria'),
                        'tipo_conta': row.get('tipo_conta', 'PF'),
                        'recorrente': bool(row.get('recorrente', False))
                    })
                    db.add_fornecedor(**dados)

                elif tipo_cadastro == "Assistente":
                    dados.update({
                        'endereco': row.get('endereco'),
                        'disponibilidade': row.get('disponibilidade')
                    })
                    db.add_assistente(**dados)

                elif tipo_cadastro == "Parceiro":
                    dados.update({
                        'area_atuacao': row.get('area_atuacao'),
                        'tipo_parceria': row.get('tipo_parceria')
                    })
                    db.add_parceiro(**dados)

                sucessos += 1

            except Exception as e:
                erros.append(f"Erro na linha {_ + 2}: {str(e)}")

        return True, f"Importação concluída: {sucessos} registros importados com sucesso. {len(erros)} erros." + (f"\nErros:\n" + "\n".join(erros) if erros else "")

    except Exception as e:
        return False, f"Erro ao processar arquivo: {str(e)}"

def importar_propostas(arquivo, db):
    """Importa propostas de um arquivo CSV"""
    try:
        df = pd.read_csv(arquivo, encoding='utf-8')
        
        # Validar colunas obrigatórias
        colunas_obrigatorias = ['cliente_id', 'descricao', 'valor', 'status']
        for col in colunas_obrigatorias:
            if col not in df.columns:
                return False, f"Coluna obrigatória '{col}' não encontrada no arquivo"

        sucessos = 0
        erros = []
        
        for _, row in df.iterrows():
            try:
                # Validar e converter datas
                data_inicio = validar_data(row.get('data_inicio'))
                data_fim = validar_data(row.get('data_fim'))
                prazo_entrega = validar_data(row.get('prazo_entrega'))

                db.add_proposta(
                    cliente_id=int(row['cliente_id']),
                    descricao=row['descricao'],
                    valor=float(row['valor']),
                    status=row['status'],
                    tipo_proposta=row.get('tipo_proposta'),
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    prazo_entrega=prazo_entrega
                )
                sucessos += 1

            except Exception as e:
                erros.append(f"Erro na linha {_ + 2}: {str(e)}")

        return True, f"Importação concluída: {sucessos} propostas importadas com sucesso. {len(erros)} erros." + (f"\nErros:\n" + "\n".join(erros) if erros else "")

    except Exception as e:
        return False, f"Erro ao processar arquivo: {str(e)}"

def gerar_template_csv(tipo):
    """Gera um arquivo CSV template baseado no tipo de importação"""
    if tipo == "Cliente":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email', 'data_aniversario', 
            'origem_cliente', 'tipo_cliente', 'observacoes', 'pix'
        ])
    elif tipo == "Fornecedor":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email', 'categoria',
            'tipo_conta', 'recorrente', 'observacoes', 'pix'
        ])
    elif tipo == "Assistente":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email', 'endereco',
            'disponibilidade', 'observacoes', 'pix'
        ])
    elif tipo == "Parceiro":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email', 'area_atuacao',
            'tipo_parceria', 'observacoes', 'pix'
        ])
    elif tipo == "Proposta":
        df = pd.DataFrame(columns=[
            'cliente_id', 'descricao', 'valor', 'status',
            'tipo_proposta', 'data_inicio', 'data_fim', 'prazo_entrega'
        ])
    else:
        return None

    return df.to_csv(index=False).encode('utf-8')
