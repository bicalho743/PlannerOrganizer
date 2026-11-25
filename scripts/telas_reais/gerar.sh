#!/usr/bin/env bash
# Gera as telas reais do sistema para a landing (não publica nada).
# Uso: bash scripts/telas_reais/gerar.sh [pasta-de-saida]
# Precisa do Postgres de teste na porta 5499 (ver CLAUDE.md) e de ffmpeg.
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
SAIDA="${1:-$RAIZ/scripts/telas_reais/saida}"
export DATABASE_URL="${DATABASE_URL:-postgresql://postgres@127.0.0.1:5499/sinal_teste}"
case "$DATABASE_URL" in *render.com*|*dpg-*) echo "Use o banco de teste."; exit 1;; esac
PORTA=8630
cd "$RAIZ"
python scripts/telas_reais/seed_demo.py
pkill -f "streamlit run.*$PORTA" 2>/dev/null || true
setsid nohup streamlit run scripts/telas_reais/tela.py --server.port $PORTA --server.headless true > /tmp/telas_reais_streamlit.log 2>&1 &
trap 'pkill -f "streamlit run.*$PORTA" 2>/dev/null || true' EXIT
for i in $(seq 1 30); do curl -s -o /dev/null "http://localhost:$PORTA" && break; sleep 1; done
node scripts/telas_reais/capturar.js "http://localhost:$PORTA" "$SAIDA"
echo "Pronto: $SAIDA"
