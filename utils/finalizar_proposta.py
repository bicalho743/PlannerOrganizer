"""
Módulo para finalizar propostas com segurança
Este módulo contém funções para finalizar propostas de forma segura, evitando problemas de concorrência no banco de dados.
"""
import os
import traceback
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session as SQLSession

# Importar modelos necessários do módulo database
from utils.database import Database, Proposta, Cliente, ProdutoOrganizador, Transacao, Venda, ItemVenda

def finalizar_proposta_segura(proposta_id):
    """
    Finaliza uma proposta de forma segura, usando uma sessão isolada para evitar problemas de concorrência.
    Esta função executa todas as operações relacionadas à finalização em uma única transação.
    
    Args:
        proposta_id: ID da proposta a ser finalizada
        
    Returns:
        dict: Resultado da operação com detalhes sobre os lançamentos gerados
    """
    # Obter a URL do banco de dados diretamente das variáveis de ambiente
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        return {
            "status": False,
            "mensagem": "DATABASE_URL não encontrada no ambiente"
        }
    
    # Criar uma nova conexão e sessão isolada para esta operação
    engine = create_engine(database_url)
    session = SQLSession(bind=engine)
    
    try:
        print(f"DEBUG FINALIZAR: Iniciando finalização segura da proposta ID={proposta_id}")
        
        # 1. Buscar a proposta a ser finalizada
        proposta = session.query(Proposta).filter_by(id=proposta_id).first()
        if not proposta:
            return {
                "status": False,
                "mensagem": f"Proposta ID={proposta_id} não encontrada"
            }
        
        # 2. Verificar se a proposta já está finalizada
        if proposta.status == "Concluída" and proposta.status_execucao == "Finalizada":
            return {
                "status": True,
                "mensagem": f"Proposta #{proposta.numero} já está finalizada"
            }
        
        # 3. Buscar o cliente da proposta
        cliente = session.query(Cliente).filter_by(id=proposta.cliente_id).first()
        if not cliente:
            return {
                "status": False,
                "mensagem": f"Cliente ID={proposta.cliente_id} não encontrado"
            }
        
        # 4. Atualizar o status da proposta
        proposta.status = "Concluída"
        proposta.status_execucao = "Finalizada"
        if not proposta.data_fim:
            proposta.data_fim = datetime.now().date()
        
        # 5. Preparar objeto para conter resultados das operações
        resultado = {
            "status": True,
            "mensagem": f"Proposta #{proposta.numero} finalizada com sucesso",
            "proposta_numero": proposta.numero,
            "proposta_descricao": proposta.descricao,
            "data_fim": proposta.data_fim,
            "lancamentos": {
                "gerados": 0,
                "valores": {
                    "base": 0,
                    "produtos": 0,
                    "fornecedores": 0,
                    "assistentes": 0,
                    "outros": 0
                }
            }
        }
        
        # 6. Gerar lançamentos financeiros para proposta concluída
        try:
            # Verificar se já existem lançamentos para esta proposta
            lancamentos_existentes = session.query(Transacao).filter_by(proposta_id=proposta.id).count()
            if lancamentos_existentes > 0:
                print(f"DEBUG FINALIZAR: Existem {lancamentos_existentes} lançamentos para a proposta")
                resultado["lancamentos"]["existentes"] = lancamentos_existentes
            
            # Cria lançamento para o valor base da proposta (valor do cliente)
            # O valor base é o preço do serviço antes de adicionar produtos/fornecedores/assistentes
            transacao_base = Transacao(
                tipo="receita",
                descricao=f"Receita da proposta #{proposta.numero} - {proposta.descricao}",
                valor=proposta.valor,
                categoria="Vendas",
                subcategoria=proposta.tipo_proposta or "Serviço",
                tipo_receita="Serviço",
                data=datetime.now().date(),
                origem_id=proposta.id,
                origem_tipo="proposta",
                tipo_conta="PF",
                status="Pendente",
                proposta_id=proposta.id,
                classificacao="receita_a_receber",
                usuario_id=proposta.usuario_id
            )
            session.add(transacao_base)
            
            # Registrar valor no resultado
            resultado["lancamentos"]["gerados"] += 1
            resultado["lancamentos"]["valores"]["base"] = proposta.valor
            
            # 7. Buscar produtos, fornecedores, assistentes e outros itens
            produtos_proposta = session.query(ProdutoOrganizador).filter_by(proposta_id=proposta.id).all()
            
            # 8. Registrar venda dos produtos, se houver
            venda_id = None
            if produtos_proposta:
                try:
                    # Verificar se já existe uma venda para esta proposta
                    venda_existente = session.query(Venda).filter_by(proposta_id=proposta.id).first()
                    if venda_existente:
                        # Remover venda existente e seus itens para criar novamente
                        print(f"DEBUG FINALIZAR: Removendo venda existente ID={venda_existente.id}")
                        
                        # Remover transações da venda
                        session.query(Transacao).filter_by(
                            origem_id=venda_existente.id,
                            origem_tipo='venda'
                        ).delete()
                        
                        # Remover itens da venda
                        session.query(ItemVenda).filter_by(venda_id=venda_existente.id).delete()
                        
                        # Remover a venda
                        session.query(Venda).filter_by(id=venda_existente.id).delete()
                        session.flush()
                    
                    # Calcular valor total dos produtos
                    valor_total_produtos = 0
                    for produto in produtos_proposta:
                        valor_produto = float(produto.valor) * produto.quantidade
                        valor_total_produtos += valor_produto
                    
                    # Criar venda
                    venda = Venda(
                        cliente_id=cliente.id,
                        proposta_id=proposta.id,
                        data_venda=datetime.now().date(),
                        valor_total=valor_total_produtos,
                        status="Concluída",
                        forma_pagamento="Proposta",
                        observacoes=f"Venda gerada automaticamente da proposta #{proposta.numero}",
                        usuario_id=proposta.usuario_id
                    )
                    session.add(venda)
                    session.flush()
                    venda_id = venda.id
                    
                    # Adicionar itens da venda
                    for produto in produtos_proposta:
                        subtotal = float(produto.valor) * produto.quantidade
                        item = ItemVenda(
                            venda_id=venda_id,
                            produto_id=produto.produto_id if hasattr(produto, 'produto_id') else None,
                            quantidade=produto.quantidade,
                            preco_unitario=produto.valor,
                            subtotal=subtotal
                        )
                        
                        # Adicionar descrição se o campo existir
                        if hasattr(ItemVenda, 'descricao'):
                            item.descricao = produto.nome
                            
                        session.add(item)
                    
                    # Registrar transação financeira para a venda
                    transacao_venda = Transacao(
                        tipo="receita",
                        descricao=f"Venda de produtos da proposta #{proposta.numero}",
                        valor=valor_total_produtos,
                        categoria="Vendas",
                        subcategoria="Produtos",
                        tipo_receita="Venda",
                        data=datetime.now().date(),
                        origem_id=venda_id,
                        origem_tipo="venda",
                        proposta_id=proposta.id,
                        tipo_conta="PF",
                        status="Pendente",
                        classificacao="receita_a_receber",
                        usuario_id=proposta.usuario_id
                    )
                    session.add(transacao_venda)
                    
                    # Registrar no resultado
                    resultado["lancamentos"]["gerados"] += 1
                    resultado["lancamentos"]["valores"]["produtos"] = valor_total_produtos
                    resultado["venda_id"] = venda_id
                    resultado["produtos_vendidos"] = len(produtos_proposta)
                    
                except Exception as e:
                    print(f"ERRO ao registrar venda de produtos: {str(e)}")
                    traceback.print_exc()
                    resultado["erro_venda"] = str(e)
                    
            # 9. Commit da transação
            session.commit()
            print(f"DEBUG FINALIZAR: Proposta #{proposta.numero} finalizada com sucesso")
            return resultado
        
        except Exception as e:
            # Rollback em caso de erro
            session.rollback()
            print(f"ERRO ao finalizar proposta: {str(e)}")
            traceback.print_exc()
            return {
                "status": False,
                "mensagem": f"Erro ao finalizar proposta: {str(e)}"
            }
    
    finally:
        # Sempre fechar a sessão
        session.close()