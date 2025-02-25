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
            try:
                return datetime.strptime(data_str, '%d/%m/%Y').date()
            except ValueError:
                try:
                    return datetime.strptime(data_str, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        return datetime.strptime(data_str, '%d/%m').date()
                    except ValueError:
                        return None
        elif isinstance(data_str, datetime):
            return data_str.date()
        return None
    except Exception as e:
        st.warning(f"Erro ao processar data: {data_str}. Erro: {str(e)}")
        return None

def importar_cadastros(arquivo, tipo_cadastro, db):
    """Importa cadastros de um arquivo Excel ou CSV"""
    try:
        # Detecta o tipo de arquivo pela extensão
        nome_arquivo = arquivo.name.lower()
        st.info(f"Processando arquivo: {nome_arquivo}")

        try:
            if nome_arquivo.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(arquivo)
            else:
                df = pd.read_csv(arquivo, encoding='utf-8')

            st.info(f"Colunas encontradas: {', '.join(df.columns.tolist())}")

        except Exception as e:
            return False, f"Erro ao ler arquivo: {str(e)}"

        # Validar colunas obrigatórias
        colunas_base = ['nome', 'telefone', 'email']
        colunas_faltantes = [col for col in colunas_base if col not in df.columns]
        if colunas_faltantes:
            return False, f"Colunas obrigatórias não encontradas: {', '.join(colunas_faltantes)}"

        # Limpar dados
        df = df.replace({pd.NA: None, 'nan': None, 'NaN': None, '': None})

        sucessos = 0
        erros = []

        for idx, row in df.iterrows():
            try:
                # Validar nome (obrigatório)
                if pd.isna(row['nome']) or str(row['nome']).strip() == '':
                    erros.append(f"Linha {idx + 2}: Nome é obrigatório")
                    continue

                dados = {
                    'nome': str(row['nome']).strip(),
                    'telefone': str(row['telefone']).strip() if not pd.isna(row['telefone']) else None,
                    'email': str(row['email']).strip() if not pd.isna(row['email']) else None,
                    'observacoes': str(row.get('observacoes', '')).strip() if not pd.isna(row.get('observacoes')) else None,
                    'pix': str(row.get('pix', '')).strip() if not pd.isna(row.get('pix')) else None
                }

                if tipo_cadastro == "Cliente":
                    # Processar data de aniversário
                    data_aniv = None
                    if 'data_aniversario' in row and not pd.isna(row['data_aniversario']):
                        data_aniv = validar_data(row['data_aniversario'])
                        if not data_aniv:
                            st.warning(f"Data de aniversário inválida na linha {idx + 2}: {row['data_aniversario']}")

                    dados.update({
                        'data_aniversario': data_aniv,
                        'origem_cliente': str(row.get('origem_cliente', '')).strip() if not pd.isna(row.get('origem_cliente')) else None,
                        'tipo_conta': str(row.get('tipo_conta', 'PF')).strip().upper()
                    })

                    # Validar tipo_conta
                    if dados['tipo_conta'] not in ['PF', 'PJ']:
                        dados['tipo_conta'] = 'PF'

                    db.add_cliente(**dados)

                elif tipo_cadastro == "Fornecedor":
                    dados.update({
                        'categoria': str(row.get('categoria', '')).strip() if not pd.isna(row.get('categoria')) else None,
                        'tipo_conta': str(row.get('tipo_conta', 'PF')).strip().upper(),
                        'recorrente': bool(row.get('recorrente', False))
                    })
                    db.add_fornecedor(**dados)

                elif tipo_cadastro == "Assistente":
                    dados.update({
                        'endereco': str(row.get('endereco', '')).strip() if not pd.isna(row.get('endereco')) else None,
                        'disponibilidade': str(row.get('disponibilidade', '')).strip() if not pd.isna(row.get('disponibilidade')) else None
                    })
                    db.add_assistente(**dados)

                elif tipo_cadastro == "Parceiro":
                    dados.update({
                        'area_atuacao': str(row.get('area_atuacao', '')).strip() if not pd.isna(row.get('area_atuacao')) else None,
                        'tipo_parceria': str(row.get('tipo_parceria', '')).strip() if not pd.isna(row.get('tipo_parceria')) else None
                    })
                    db.add_parceiro(**dados)

                sucessos += 1

            except Exception as e:
                erros.append(f"Erro na linha {idx + 2}: {str(e)}")

        mensagem = f"Importação concluída:\n- Registros importados com sucesso: {sucessos}"
        if erros:
            mensagem += f"\n- Erros encontrados: {len(erros)}\n"
            for erro in erros:
                mensagem += f"\n  • {erro}"

        return sucessos > 0, mensagem

    except Exception as e:
        return False, f"Erro ao processar arquivo: {str(e)}"

def gerar_template_excel(tipo):
    """Gera um arquivo Excel template baseado no tipo de importação"""
    if tipo == "Cliente":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email', 'data_aniversario', 
            'origem_cliente', 'tipo_conta', 'observacoes', 'pix'
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
            'origem_cliente', 'tipo_conta', 'observacoes', 'pix'
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