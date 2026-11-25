"""Cookie de login assinado (utils/sessao_cookie): só o servidor cria; vence; não aceita alteração."""
import time

from utils import sessao_cookie as sc


def test_token_valido_volta_uid_e_email():
    t = sc.criar_token("abc123", "ana@exemplo.com")
    assert sc.ler_token(t) == ("abc123", "ana@exemplo.com")


def test_token_alterado_ou_vencido_e_recusado():
    t = sc.criar_token("abc123", "ana@exemplo.com")
    corpo, assin = t.split(".")
    import base64
    falso = base64.urlsafe_b64encode(b"outra|9999999999|").decode().rstrip("=") + "." + assin
    assert sc.ler_token(falso) is None
    assert sc.ler_token(t[:-3] + "AAA") is None
    assert sc.ler_token(sc.criar_token("x", agora=time.time() - sc.VALIDADE - 10)) is None
    assert sc.ler_token("lixo") is None and sc.ler_token("") is None
