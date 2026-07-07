"""
Fonte única de verdade para o campo `clientes.origem_cliente`.

Antes o campo era texto livre, gerando duplicatas por caixa
('Instagram' vs 'instagram'), legendas '0' e nomes próprios de clientes
como se fossem origens, fragmentando o gráfico "Distribuição por Origem".

Aqui definimos as opções oficiais e uma normalização que mapeia qualquer
entrada legada para uma categoria oficial (desconhecido -> 'Outros';
vazio/nulo -> None, exibido como 'Não informado').
"""

# Opções oficiais oferecidas no cadastro (dropdown).
ORIGEM_NAO_INFORMADA = "Não informado"
ORIGENS_OFICIAIS = ["Cliente", "Internet", "Instagram", "Google", ORIGEM_NAO_INFORMADA]


def normalizar_origem(valor):
    """
    Converte qualquer entrada (legada ou nova) para uma categoria oficial.

    Retorna None para vazio/nulo (o chamador exibe como 'Não informado').
    Nomes próprios / indicações viram 'Cliente' (indicação de cliente);
    site/redes/online viram 'Internet'.
    """
    if valor is None:
        return None
    s = str(valor).strip().lower()
    if s in ("", "nan", "none", "null", "undefined", "<na>"):
        return None
    if s in ("não informado", "nao informado"):
        return ORIGEM_NAO_INFORMADA
    if "instagram" in s or s == "insta":
        return "Instagram"
    if "google" in s:
        return "Google"
    if any(k in s for k in ("internet", "site", "website", "rede", "facebook", "online")):
        return "Internet"
    # indicação de cliente, nomes próprios, BNI e demais fontes de indicação
    return "Cliente"


def origem_para_exibicao(valor):
    """Normaliza e devolve rótulo pronto para UI ('Não informado' quando vazio)."""
    canonico = normalizar_origem(valor)
    return canonico if canonico else ORIGEM_NAO_INFORMADA
