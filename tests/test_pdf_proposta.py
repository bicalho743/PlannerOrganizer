"""PDF novo da proposta: contraste das cores, ambientes da descrição e geração em todas as cores."""
import os

from reportlab.lib import colors

from utils import pdf_proposta as pp


def test_cores_claras_ficam_legiveis():
    for h in ("#2F7D57", "#5B4B8A", "#0D1B2A", "#B5546A", "#B8943D", "#3D6BB3", "#F2C94C", "#F6C1CC", "#FFFFFF"):
        texto, sobre = pp.cores_legiveis(colors.HexColor(h))
        assert pp._contraste(texto, colors.white) >= 4.5
        assert pp._contraste(colors.HexColor(h), sobre) >= 3.0 or sobre == pp.TX


def test_ambientes_vem_da_descricao():
    amb = pp.ambientes_da_descricao("Organização de Cozinha, Closet / guarda-roupa (2). Prazo estimado: 2 dia(s).")
    assert amb == [("Cozinha", "1 ambiente"), ("Closet / guarda-roupa", "2 ambientes")]
    assert pp.ambientes_da_descricao("Organização completa do apartamento com etiquetas") == []


def test_telefone_e_link():
    assert pp.telefone_fmt("31999887766") == "(31) 99988-7766"
    assert pp.link_whatsapp("(31) 99988-7766", "oi").startswith("https://wa.me/5531999887766")
    assert pp.condicoes("1. Pagamento sinal, na reserva da data, via PIX\n2. x") == pp.CONDICOES_PADRAO
    assert pp.condicoes("Pix na aprovação\n- Sem reembolso") == ["Pix na aprovação", "Sem reembolso"]


def test_gera_pdf_em_qualquer_cor(tmp_path):
    dados = {"numero": 1, "cliente": "Juliana", "tipo": "Pós-mudança", "descricao": "Pós-mudança: Cozinha. Prazo.",
             "itens": [("Serviço", "", 2500)], "total": 2500, "sinal": 500, "condicoes": pp.CONDICOES_PADRAO}
    for h in ("#2F7D57", "#F2C94C", "", "cor-invalida"):
        arq = tmp_path / f"p{abs(hash(h))}.pdf"
        pp.gerar_pdf_proposta(dados, str(arq), perfil={"empresa": "Ana", "cor_principal": h, "telefone": "31999887766"})
        assert os.path.getsize(arq) > 1500
