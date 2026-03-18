#!/bin/bash
set -e

echo "=== Post-merge setup ==="

# Instalar dependências Python se necessário
if [ -f "requirements.txt" ]; then
  echo "Instalando dependências Python..."
  pip install -r requirements.txt --quiet --no-input
fi

echo "=== Setup concluído ==="
