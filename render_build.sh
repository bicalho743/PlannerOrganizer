#!/bin/bash

# Script para construir a aplicação no Render
# Este script resolve o problema de conflito na versão do Stripe

# Instalar diretamente do arquivo de requisitos unificado
pip install -r requirements_unified.txt

# Garantir que a versão do Stripe seja a mais recente
pip install --force-reinstall stripe>=11.5.0

echo "Instalação concluída com sucesso!"