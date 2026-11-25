# Telas reais (landing, lojas, vídeo)

Tudo com a conta de demonstração `demo_landing` no banco de TESTE (`seed_demo.py`).

1. Site: `bash gerar.sh` (Streamlit `tela.py` na porta 8630) e `node capturar_web.js <pasta>` → `web_<tela>.png`.
2. App de verdade no navegador: copiar o planner-app para uma pasta à parte, pôr `app_web/metro.config.js` e
   `app_web/falsos/` nela, `npx expo install react-native-web react-dom @expo/metro-runtime`, trocar a URL da API por
   `http://localhost:8640` e `npx expo export --platform web --output-dir web-out`. Servir `web-out` (porta 8641, com
   volta para index.html) e a API local `uvicorn api_demo:api --port 8640` (qualquer token vira demo_landing).
   `node capturar_app.js <pasta>` → `app_<tela>.png` (390x844 @2x) e os vídeos do "Como funciona" (600x1298).
   `node capturar_extras.js <pasta>` → vendas e impostos (site e app).
3. Vídeo da landing (1min30, mesma narração): `python3 montar_tour.py horizontal|vertical <saida.mp4>`.
   Os caminhos no topo dos scripts apontam para a pasta de trabalho usada em 25/11/2026: ajuste antes de rodar.
