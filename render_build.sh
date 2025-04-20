#!/bin/bash

# Script para construir a aplicação no Render
# Este script resolve o problema de conflito na versão do Stripe

# Primeiro, remova qualquer versão existente do Stripe
pip uninstall -y stripe

# Instalar pacotes sem dependências (exceto Stripe)
export PIP_CONFIG_FILE=render_pip.conf
pip install streamlit fastapi uvicorn psycopg2-binary pandas firebase-admin 
pip install anthropic humanize mercadopago numpy openai openpyxl plotly pyjwt pypdf2
pip install reflex reportlab schedule sqlalchemy trafilatura twilio unidecode werkzeug xlrd
pip install zipfile36 streamlit-authenticator requests pyrebase4

# Agora, sem a configuração no-dependencies, executamos o script de limpeza do Python
unset PIP_CONFIG_FILE
chmod +x render_cleanup.py
python render_cleanup.py

# Uma última verificação para garantir que temos a versão correta
pip list | grep stripe

echo "Instalação concluída com sucesso!"