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
            
            # Não criar mais o lançamento base automático da proposta
            # Vamos registrar apenas para fins de controle no resultado
            resultado["lancamentos"]["valores"]["base"] = proposta.valor
            
            # 7. Buscar produtos, fornecedores, assistentes e outros itens
            produtos_proposta = session.query(ProdutoOrganizador).filter_by(proposta_id=proposta.id).all()
            
            # 7.1 Buscar acréscimos do tipo FORNECEDOR e gerar comissões
            from utils.database import AcrescimoProposta, Fornecedor
            fornecedores = session.query(AcrescimoProposta).filter_by(
                proposta_id=proposta.id, 
                tipo="FORNECEDOR"
            ).all()
            
            valor_total_fornecedores = 0
            
            if fornecedores:
                print(f"DEBUG FINALIZAR: Encontrados {len(fornecedores)} fornecedores para a proposta ID={proposta.id}")
                
                for fornecedor in fornecedores:
                    valor_fornecedor = float(fornecedor.valor) if fornecedor.valor else 0
                    valor_total_fornecedores += valor_fornecedor
                    
                    # Verificar se já existe uma transação de comissão para este fornecedor
                    transacao_comissao_existente = session.query(Transacao).filter_by(
                        proposta_id=proposta.id,
                        origem_tipo="comissao_fornecedor"
                    ).filter(Transacao.descricao.like(f"%{fornecedor.fornecedor}%")).first()
                    
                    # Buscar percentual de comissão do fornecedor
                    percentual_comissao = None
                    
                    if hasattr(fornecedor, 'percentual_comissao'):
                        percentual_comissao = fornecedor.percentual_comissao
                    
                    # Se não tiver no acréscimo, buscar no cadastro do fornecedor
                    if not percentual_comissao:
                        fornecedor_cadastro = session.query(Fornecedor).filter(
                            Fornecedor.descricao == fornecedor.fornecedor
                        ).first()
                        
                        if fornecedor_cadastro and hasattr(fornecedor_cadastro, 'percentual_comissao'):
                            percentual_comissao = fornecedor_cadastro.percentual_comissao
                    
                    # Calculamos o valor da comissão para fins informativos, mas não criamos o lançamento
                    if percentual_comissao and percentual_comissao > 0 and not transacao_comissao_existente:
                        valor_comissao = valor_fornecedor * (percentual_comissao / 100)
                        
                        if valor_comissao > 0:
                            print(f"DEBUG FINALIZAR: Calculando comissão de {percentual_comissao}% para fornecedor {fornecedor.fornecedor}: R$ {valor_comissao:.2f} (lançamento não criado)")
                            
                            # Não criamos mais o lançamento de comissão aqui
                            # Apenas registramos o valor para o relatório
                            
                            # Adicionar valor das comissões ao resultado
                            if "comissoes" not in resultado["lancamentos"]["valores"]:
                                resultado["lancamentos"]["valores"]["comissoes"] = 0
                            
                            resultado["lancamentos"]["valores"]["comissoes"] += valor_comissao
                    
                    # Sempre gerar lançamento de comissão sobre fornecedor se não existir
                    # Mesmo para fornecedores sem percentual, vamos criar um lançamento para pagamentos manuais
                    elif not transacao_comissao_existente and valor_fornecedor > 0:
                        print(f"DEBUG FINALIZAR: Criando lançamento de comissão genérica para fornecedor {fornecedor.fornecedor}")
                        
                        # Valor zero, será preenchido manualmente pelo usuário
                        transacao_comissao_fornecedor = Transacao(
                            tipo="Receita",
                            descricao=f"Receita - comissão fornecedor {fornecedor.fornecedor} - Proposta #{proposta.numero}",
                            valor=0.0,  # Valor zero, a ser preenchido manualmente
                            data=datetime.now().date(),
                            categoria="Comissão sobre fornecedores",
                            subcategoria="Comissão de Fornecedor",
                            tipo_receita="comissao",
                            origem_id=fornecedor.id,
                            origem_tipo="comissao_fornecedor_manual",
                            proposta_id=proposta.id,
                            tipo_conta="PF",
                            status="Pendente",
                            classificacao="contas_a_receber",
                            usuario_id=proposta.usuario_id
                        )
                        session.add(transacao_comissao_fornecedor)
                        resultado["lancamentos"]["gerados"] += 1
                
                # Registrar valor total de fornecedores no resultado
                resultado["lancamentos"]["valores"]["fornecedores"] = valor_total_fornecedores
            
            # 7.2 Buscar acréscimos do tipo OUTRO e gerar lançamentos financeiros para eles
            outros_acrescimos = session.query(AcrescimoProposta).filter_by(
                proposta_id=proposta.id, 
                tipo="OUTRO"
            ).all()
            
            valor_total_outros = 0
            
            if outros_acrescimos:
                print(f"DEBUG FINALIZAR: Encontrados {len(outros_acrescimos)} acréscimos do tipo OUTRO para a proposta ID={proposta.id}")
                
                for outro in outros_acrescimos:
                    valor_outro = float(outro.valor) if outro.valor else 0
                    valor_total_outros += valor_outro
                    
                    # Verificar se já existe uma transação para este acréscimo
                    transacao_outro_existente = session.query(Transacao).filter_by(
                        proposta_id=proposta.id,
                        origem_tipo="acrescimo_outro",
                        origem_id=outro.id
                    ).first()
                    
                    if not transacao_outro_existente and valor_outro > 0:
                        print(f"DEBUG FINALIZAR: Criando lançamento para acréscimo OUTRO: {outro.descricao} - R$ {valor_outro}")
                        
                        transacao_outro = Transacao(
                            tipo="Receita",
                            descricao=f"{outro.descricao} - Proposta #{proposta.numero}",
                            valor=valor_outro,
                            data=datetime.now().date(),
                            categoria="Serviços Adicionais",
                            subcategoria="Outros Acréscimos",
                            tipo_receita="Serviço",
                            origem_id=outro.id,
                            origem_tipo="acrescimo_outro",
                            proposta_id=proposta.id,
                            tipo_conta="PF",
                            status="Pendente",
                            classificacao="contas_a_receber",
                            usuario_id=proposta.usuario_id
                        )
                        session.add(transacao_outro)
                        resultado["lancamentos"]["gerados"] += 1
                
                # Registrar valor total de outros acréscimos no resultado
                resultado["lancamentos"]["valores"]["outros"] = valor_total_outros
                
            # 7.3 Buscar acréscimos do tipo ASSISTENTE apenas para contabilização, mas não gerar lançamentos
            assistentes = session.query(AcrescimoProposta).filter_by(
                proposta_id=proposta.id, 
                tipo="ASSISTENTE"
            ).all()
            
            valor_total_assistentes = 0
            
            if assistentes:
                print(f"DEBUG FINALIZAR: Encontrados {len(assistentes)} assistentes para a proposta ID={proposta.id}")
                
                for assistente in assistentes:
                    valor_assistente = float(assistente.valor) if assistente.valor else 0
                    valor_total_assistentes += valor_assistente
                    
                    # Apenas registramos os valores para o relatório, não criamos lançamentos automáticos
                    if valor_assistente > 0:
                        print(f"DEBUG FINALIZAR: Assistente: {assistente.descricao} - R$ {valor_assistente} (lançamento não criado)")
                        
                        # Não criamos mais lançamentos automáticos para assistentes
                        # O usuário precisa criar manualmente
                
                # Registrar valor total de assistentes no resultado
                resultado["lancamentos"]["valores"]["assistentes"] = valor_total_assistentes
            
            # Sempre criar um lançamento genérico de pagamento de equipe quando não houver
            # assistentes específicos cadastrados ou quando o valor total for zero
            transacao_equipe_existente = session.query(Transacao).filter_by(
                proposta_id=proposta.id,
                origem_tipo="despesa_equipe_generica"
            ).first()
            
            if not transacao_equipe_existente and valor_total_assistentes == 0:
                print(f"DEBUG FINALIZAR: Criando lançamento genérico de pagamento de equipe")
                
                # Valor zero, será preenchido manualmente pelo usuário
                transacao_despesa_equipe = Transacao(
                    tipo="despesa_a_pagar",
                    descricao=f"Despesas - pagamento equipe/assistentes - Proposta #{proposta.numero}",
                    valor=0.0,  # Valor zero, a ser preenchido manualmente
                    data=datetime.now().date(),
                    categoria="Pagamento Equipe/Assistentes",
                    subcategoria="Equipe",
                    tipo_receita=None,
                    origem_id=proposta.id,
                    origem_tipo="despesa_equipe_generica",
                    proposta_id=proposta.id,
                    tipo_conta="PF",
                    status="Pendente",
                    classificacao="contas_a_pagar",
                    usuario_id=proposta.usuario_id
                )
                session.add(transacao_despesa_equipe)
                resultado["lancamentos"]["gerados"] += 1
            
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
                    
                    # Verificar se já existe uma transação para os produtos desta venda
                    transacao_produto_existente = session.query(Transacao).filter_by(
                        proposta_id=proposta.id,
                        origem_tipo="venda"
                    ).first()
                    
                    if transacao_produto_existente:
                        print(f"DEBUG FINALIZAR: Já existe lançamento para produtos da proposta ID={proposta.id}, atualizando")
                        # Atualizar o registro existente com o novo valor e ID da venda
                        transacao_produto_existente.valor = valor_total_produtos
                        transacao_produto_existente.origem_id = venda_id
                        transacao_produto_existente.data = datetime.now().date()
                        resultado["lancamentos"]["atualizados"] = True
                    else:
                        # Registrar nova transação financeira para a venda
                        print(f"DEBUG FINALIZAR: Criando novo lançamento para produtos da proposta ID={proposta.id}")
                        transacao_venda = Transacao(
                            tipo="Receita",
                            descricao=f"Produtos da proposta #{proposta.numero}",
                            valor=valor_total_produtos,
                            categoria="Venda Produtos",
                            subcategoria="Produtos",
                            tipo_receita="Venda",
                            data=datetime.now().date(),
                            origem_id=venda_id,
                            origem_tipo="venda",
                            proposta_id=proposta.id,
                            tipo_conta="PF",
                            status="Pendente",
                            classificacao="contas_a_receber",
                            usuario_id=proposta.usuario_id
                        )
                        session.add(transacao_venda)
                        resultado["lancamentos"]["gerados"] += 1
                    
                    # Registrar no resultado
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