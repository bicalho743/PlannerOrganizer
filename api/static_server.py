"""
Servidor Flask simples para servir arquivos estáticos
"""
from flask import Flask, send_from_directory
import os

app = Flask(__name__)

# Definir o caminho raiz do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.route('/public/<path:path>')
def serve_public(path):
    """Serve arquivos do diretório public"""
    return send_from_directory(os.path.join(BASE_DIR, 'public'), path)

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve arquivos do diretório static"""
    return send_from_directory(os.path.join(BASE_DIR, 'static'), path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)