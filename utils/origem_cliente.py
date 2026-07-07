"""
Fonte única de verdade para o campo `clientes.origem_cliente`.

Antes o campo era texto livre, gerando duplicatas por caixa
('Instagram' vs 'instagram'), legendas '0' e nomes próprios de clientes
como se fossem origens, fragmentando o gráfico "Distribuição por Origem".

Aqui definimos as opções oficiais e uma normalização que mapeia qualquer
entrada legada para uma categoria oficial (desconhecido -> 'Outros';
vazio/nulo -> None, exibido como 'Não informado').
"""

# Opções oficiais oferecidas no cadastro (dropdown). Ajustadas às fontes já
# usadas no negócio (BNI aparece nos dados reais).
ORIGENS_OFICIAIS = ["Instagram", "Indicação", "BNI", "Google", "Site", "Outros"]

# Rótulo de exibição quando não há origem definida.
ORIGEM_NAO_INFORMADA = "Não informado"


def normalizar_origem(valor):
    """
    Converte qualquer entrada (legada ou nova) para uma categoria oficial.

    Retorna None para vazio/nulo (o chamador exibe como 'Não informado').
    Retorna 'Outros' para valores que não casam com nenhuma opção conhecida
    (ex.: nomes próprios de clientes).
    """
    if valor is None:
        return None
    s = str(valor).strip().lower()
    if s in ("", "nan", "none", "null", "undefined", "<na>"):
        return None
    if "instagram" in s or s == "insta":
        return "Instagram"
    if "bni" in s:
        return "BNI"
    if "google" in s:
        return "Google"
    if "site" in s or "website" in s:
        return "Site"
    if "indica" in s or "amig" in s or "conhec" in s or "boca a boca" in s or "boca-a-boca" in s:
        return "Indicação"
    if s in (o.lower() for o in ORIGENS_OFICIAIS):
        # já é uma oficial (com caixa diferente)
        return next(o for o in ORIGENS_OFICIAIS if o.lower() == s)
    return "Outros"


def origem_para_exibicao(valor):
    """Normaliza e devolve rótulo pronto para UI ('Não informado' quando vazio)."""
    canonico = normalizar_origem(valor)
    return canonico if canonico else ORIGEM_NAO_INFORMADA
