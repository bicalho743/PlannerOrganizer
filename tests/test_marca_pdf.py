"""A marca da organizadora (cores, logotipo, contatos) entra nos PDFs e não vaza entre gerações."""
import base64
import io
import zlib

from PIL import Image


class _Arquivo:
    def __init__(self, dados):
        self._dados = dados

    def getvalue(self):
        return self._dados


def _png(tamanho=(1200, 600)):
    b = io.BytesIO()
    Image.new("RGB", tamanho, "#7A3E9D").save(b, "PNG")
    return b.getvalue()


def _texto_pdf(caminho):
    """Junta os fluxos (descomprimidos) do PDF para procurar textos e cores."""
    bruto = open(caminho, "rb").read()
    partes = [bruto]
    for bloco in bruto.split(b"stream\n")[1:]:
        if b"~>" not in bloco:
            continue
        try:  # reportlab grava os fluxos em ASCII85 + Flate
            partes.append(zlib.decompress(base64.a85decode(bloco.split(b"~>")[0].strip().removeprefix(b"<~"))))
        except Exception:
            pass
    return b"\n".join(partes)


DADOS = {"proposta_id": 7, "cliente": "Cliente", "tipo": "Residencial", "status": "Em Aberto", "periodo": "",
         "descricao": "", "itens": [{"nome": "Closet", "valor": 100.0}], "total": 100.0}


def test_preparar_logo_reduz_e_vira_png():
    from pages.perfil import preparar_logo, LOGO_MAX_PX
    import base64
    url = preparar_logo(_Arquivo(_png()))
    assert url.startswith("data:image/png;base64,")
    img = Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1])))
    assert max(img.size) <= LOGO_MAX_PX


def test_preparar_logo_recusa_arquivo_que_nao_e_imagem():
    import pytest
    from pages.perfil import preparar_logo
    with pytest.raises(ValueError):
        preparar_logo(_Arquivo(b"isto nao e imagem"))


def test_pdf_usa_cores_logo_e_contatos_da_organizadora(tmp_path, monkeypatch):
    import utils.pdf_generator_v2 as gerador
    from pages.perfil import preparar_logo
    monkeypatch.setattr(gerador, "_perfil_da_conta", lambda: {})  # só o perfil passado, sem o salvo no banco
    from utils.pdf_generator_v2 import gerar_pdf_cliente, _paleta
    perfil = {"nome": "Ana", "empresa": "Organiza Ana", "telefone": "(31) 90000-0000", "cnpj": "12.345.678/0001-90",
              "cor_principal": "#4A1D5E", "cor_secundaria": "#F4C2D7", "logo": preparar_logo(_Arquivo(_png()))}
    com, sem = tmp_path / "com.pdf", tmp_path / "sem.pdf"
    gerar_pdf_cliente(DADOS, str(com), perfil=perfil)
    gerar_pdf_cliente(DADOS, str(sem), perfil={"nome": "Ana"})
    t_com, t_sem = _texto_pdf(com), _texto_pdf(sem)
    assert b"/Subtype /Image" in t_com and b"/Subtype /Image" not in t_sem
    assert b"Organiza Ana" in t_com and b"12.345.678/0001-90" in t_com and rb"\(31\) 90000-0000" in t_com
    # cor principal #4A1D5E = (0.290196, 0.113725, 0.368627) no cabeçalho; ausente sem marca
    assert b".290196 .113725 .368627 rg" in t_com and b".290196 .113725 .368627 rg" not in t_sem
    assert _paleta.get() is None
