#!/bin/bash

# Script para construir a aplicação no Render
# Este script resolve o problema de conflito na versão do Stripe

# Primeiro, remova qualquer versão existente do Stripe
pip uninstall -y stripe

# Instalar todas as dependências do arquivo requirements-render.txt (versões compatíveis)
pip install -r requirements-render.txt

# Uma última verificação para garantir que temos a versão correta
pip list | grep stripe

echo "Instalação concluída com sucesso!"