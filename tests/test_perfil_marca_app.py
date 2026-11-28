"""Logo e cor da marca enviados pelo app (PUT /perfil)."""
import base64, io
import pytest
from fastapi import HTTPException
from PIL import Image
from api.router import _logo_do_app


def _png(w=1200, h=400):
    b = io.BytesIO(); Image.new("RGB", (w, h), "#B8943D").save(b, "PNG"); return base64.b64encode(b.getvalue()).decode()


def test_logo_reduzido_para_600():
    url = _logo_do_app(_png())
    assert url.startswith("data:image/png;base64,")
    img = Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1])))
    assert max(img.size) == 600


def test_aceita_data_url():
    assert _logo_do_app("data:image/png;base64," + _png(100, 100)).startswith("data:image/png")


def test_imagem_invalida():
    with pytest.raises(HTTPException):
        _logo_do_app(base64.b64encode(b"nao e imagem").decode())
