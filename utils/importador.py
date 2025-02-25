import pandas as pd
import streamlit as st
from datetime import datetime
import io

def validar_data(data_str):
    """Converte string de data para objeto datetime"""
    if pd.isna(data_str):
        return None
    try:
        if isinstance(data_str, str):
            return datetime.strptime(data_str, '%d/%m/%Y').date()
        elif isinstance(data_str, datetime):
            return data_str.date()
        return None
    except ValueError:
        try:
            return datetime.strptime(str(data_str), '%Y-%m-%d').date()
        except ValueError:
            return None

def importar_cadastros(arquivo, tipo_cadastro, db):
    """Importa cadastros de um arquivo Excel ou CSV"""
    try:
        # Detecta o tipo de arquivo pela extensão
        nome_arquivo = arquivo.name.lower()
        if nome_arquivo.endswith('.xlsx') or nome_arquivo.endswith('.xls'):
            df = pd.read_excel(arquivo)
        else:
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
                    'nome': str(row['nome']),
                    'telefone': str(row['telefone']) if not pd.isna(row['telefone']) else None,
                    'email': str(row['email']) if not pd.isna(row['email']) else None,
                    'observacoes': str(row.get('observacoes', '')),
                    'pix': str(row.get('pix', ''))
                }

                if tipo_cadastro == "Cliente":
                    dados.update({
                        'data_aniversario': validar_data(row.get('data_aniversario')),
                        'origem_cliente': str(row.get('origem_cliente', '')),
                        'tipo_cliente': str(row.get('tipo_cliente', 'PF'))
                    })
                    db.add_cliente(**dados)

                elif tipo_cadastro == "Fornecedor":
                    dados.update({
                        'categoria': str(row.get('categoria', '')),
                        'tipo_conta': str(row.get('tipo_conta', 'PF')),
                        'recorrente': bool(row.get('recorrente', False))
                    })
                    db.add_fornecedor(**dados)

                elif tipo_cadastro == "Assistente":
                    dados.update({
                        'endereco': str(row.get('endereco', '')),
                        'disponibilidade': str(row.get('disponibilidade', ''))
                    })
                    db.add_assistente(**dados)

                elif tipo_cadastro == "Parceiro":
                    dados.update({
                        'area_atuacao': str(row.get('area_atuacao', '')),
                        'tipo_parceria': str(row.get('tipo_parceria', ''))
                    })
                    db.add_parceiro(**dados)

                sucessos += 1

            except Exception as e:
                erros.append(f"Erro na linha {_ + 2}: {str(e)}")

        return True, f"Importação concluída: {sucessos} registros importados com sucesso. {len(erros)} erros." + (f"\nErros:\n" + "\n".join(erros) if erros else "")

    except Exception as e:
        return False, f"Erro ao processar arquivo: {str(e)}"

def gerar_template_excel(tipo):
    """Gera um arquivo Excel template baseado no tipo de importação"""
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

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()

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