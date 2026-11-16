"""
Gera um código de convite com teste grátis estendido.

Uso (com DATABASE_URL apontando para o banco do Planner):
    python scripts/criar_convite.py            # 30 dias
    python scripts/criar_convite.py --dias 45
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine  # noqa: E402
from utils.convites import novo_convite, DIAS_CONVITE_PADRAO  # noqa: E402


def main():
    p = argparse.ArgumentParser(description="Criar convite do Planner Organiza")
    p.add_argument("--dias", type=int, default=DIAS_CONVITE_PADRAO)
    args = p.parse_args()
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        sys.exit("Defina DATABASE_URL antes de rodar.")
    url = url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(url, connect_args={"sslmode": "require"} if url.startswith("postgresql") else {})
    codigo = novo_convite(engine, dias=args.dias)
    print(f"Convite criado: {codigo} ({args.dias} dias de teste). Cada código serve para uma conta só.")


if __name__ == "__main__":
    main()
