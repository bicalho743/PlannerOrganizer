"""
Migração: normaliza `clientes.origem_cliente` para as categorias oficiais
(utils/origem_cliente.ORIGENS_OFICIAIS). Valores fora do padrão (ex.: nomes
próprios de clientes) viram 'Outros'; variações de caixa são unificadas
('instagram' -> 'Instagram'). Registros vazios/nulos NÃO são alterados.

Uso:
    python scripts/migrar_origem_cliente.py            # dry-run (só mostra)
    python scripts/migrar_origem_cliente.py --apply    # aplica no banco

Requer DATABASE_URL no ambiente.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from utils.origem_cliente import normalizar_origem

URL = os.environ.get("DATABASE_URL")
if not URL:
    print("ERRO: defina a variável de ambiente DATABASE_URL")
    sys.exit(1)

APPLY = "--apply" in sys.argv


def main():
    conn = psycopg2.connect(URL, sslmode="require", connect_timeout=30)
    cur = conn.cursor()
    cur.execute("SELECT id, origem_cliente FROM clientes")
    rows = cur.fetchall()

    mudancas = []
    for cid, origem in rows:
        if origem is None or str(origem).strip() == "":
            continue  # vazio/nulo: deixado como está (exibido como 'Não informado')
        novo = normalizar_origem(origem)  # sempre uma oficial, pois é não-vazio
        if novo != origem:
            mudancas.append((cid, origem, novo))

    print(f"Total de clientes: {len(rows)}")
    print(f"Registros a normalizar: {len(mudancas)}")
    for cid, atual, novo in mudancas:
        print(f"  #{cid}: {atual!r} -> {novo!r}")

    if not mudancas:
        print("Nada a fazer.")
    elif APPLY:
        for cid, _atual, novo in mudancas:
            cur.execute(
                "UPDATE clientes SET origem_cliente = %s WHERE id = %s",
                (novo, cid),
            )
        conn.commit()
        print(f"\n✅ Aplicado: {len(mudancas)} registros atualizados.")
    else:
        print("\n(dry-run) Rode novamente com --apply para gravar.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
