#!/usr/bin/env python3
"""
Script simples para excluir vendas diretamente do banco de dados
Uso: python3 excluir_venda_direto.py <id_da_venda>
"""

import sys
import os
import psycopg2

def excluir_venda(venda_id):
    """Exclui uma venda e todos os registros relacionados diretamente via SQL"""
    # Verificar o ID da venda
    try:
        venda_id = int(venda_id)
    except ValueError:
        print(f"Erro: ID de venda inválido: {venda_id}")
        return False
    
    # Conectar ao banco de dados
    print(f"Conectando ao banco de dados...")
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cursor = conn.cursor()
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return False
    
    try:
        # Iniciar transação
        print(f"Iniciando transação...")
        
        # 1. Excluir registros financeiros relacionados
        print(f"1. Excluindo registros financeiros...")
        cursor.execute("""
            DELETE FROM financeiro 
            WHERE origem_id = %s AND origem_tipo = 'venda'
        """, (venda_id,))
        print(f"   - {cursor.rowcount} registros financeiros excluídos")
        
        # 2. Excluir itens da venda
        print(f"2. Excluindo itens da venda...")
        cursor.execute("""
            DELETE FROM itens_venda 
            WHERE venda_id = %s
        """, (venda_id,))
        print(f"   - {cursor.rowcount} itens excluídos")
        
        # 3. Remover referência à proposta
        print(f"3. Removendo referência à proposta...")
        cursor.execute("""
            UPDATE vendas 
            SET proposta_id = NULL 
            WHERE id = %s
        """, (venda_id,))
        print(f"   - Referências removidas: {cursor.rowcount}")
        
        # 4. Finalmente excluir a venda
        print(f"4. Excluindo a venda...")
        cursor.execute("""
            DELETE FROM vendas 
            WHERE id = %s
        """, (venda_id,))
        print(f"   - Vendas excluídas: {cursor.rowcount}")
        
        # Confirmar transação
        print(f"Confirmando transação...")
        conn.commit()
        print(f"\n✅ Venda #{venda_id} excluída com sucesso!")
        return True
    
    except Exception as e:
        # Rollback em caso de erro
        print(f"❌ ERRO: {e}")
        print(f"Revertendo transação...")
        conn.rollback()
        return False
    
    finally:
        # Fechar conexão
        cursor.close()
        conn.close()
        print("Conexão fechada")

def main():
    """Função principal"""
    if len(sys.argv) != 2:
        print(f"Uso: python3 {sys.argv[0]} <id_da_venda>")
        sys.exit(1)
    
    venda_id = sys.argv[1]
    print(f"Excluindo venda #{venda_id}...")
    
    if excluir_venda(venda_id):
        print("Operação concluída com sucesso!")
        sys.exit(0)
    else:
        print("A operação falhou. Verifique os erros acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()