#!/bin/bash

# Script para construir a aplicação no Render
# Este script resolve o problema de conflito na versão do Stripe

# Primeiro, vamos instalar os requisitos básicos sem o Stripe
pip install streamlit fastapi uvicorn psycopg2-binary pandas firebase-admin pyrebase4

# Em seguida, vamos instalar as outras dependências sem o Stripe
pip install anthropic humanize mercadopago numpy openai openpyxl plotly pyjwt pypdf2 reflex reportlab schedule sqlalchemy trafilatura twilio unidecode werkzeug xlrd zipfile36 streamlit-authenticator requests

# Finalmente, vamos instalar apenas a versão mais recente do Stripe
pip install stripe>=11.5.0

echo "Instalação concluída com sucesso!"