"""Sem login não se entra: nenhum parâmetro de URL abre sessão (havia ?restore_session=true&session_type=demo)."""
import os

import pytest
from streamlit.testing.v1 import AppTest

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="precisa de DATABASE_URL")


@pytest.mark.parametrize("params", [{}, {"restore_session": "true", "session_type": "demo"}])
def test_app_sem_login_mostra_tela_de_entrada(params):
    at = AppTest.from_file("../app.py", default_timeout=60)
    for k, v in params.items():
        at.query_params[k] = v
    at.run()
    assert not at.session_state["authenticated"]
    assert "usuario_id" not in at.session_state
    assert any("Entrar na minha conta" in b.label for b in at.button)
