"""
Formatadores de exibição (camada de apresentação).
Corrige UX-1: CPF com .0, valores None literais, mojibake e
inconsistência de capitalização — SEM alterar os dados do banco.
"""
import re
import unicodedata

import pandas as pd

# Sufixos que NÃO devem ser title-cased em nomes de cidade/bairro
_MINUSCULAS = {"de", "da", "do", "das", "dos", "e"}


def _eh_vazio(valor) -> bool:
    if valor is None:
        return True
    try:
        if pd.isna(valor):
            return True
    except (TypeError, ValueError):
        pass
    texto = str(valor).strip()
    return texto == "" or texto.lower() in {"none", "nan", "null", "undefined", "<na>"}


def valor_ou_traco(valor, fallback="—"):
    """Retorna o valor como string exibível, ou `fallback` quando ausente
    (None/NaN/vazio/'nan'/'none'/'null'/'undefined'). Use em toda exibição de
    campo que pode vir nulo, evitando literais de programação para o usuário."""
    if _eh_vazio(valor):
        return fallback
    return str(valor).strip()


def corrigir_encoding(texto: str) -> str:
    """Tenta reverter mojibake (ex.: 'Endere�', 'Mário' quebrado)."""
    if not isinstance(texto, str):
        return texto
    try:
        consertado = texto.encode("latin-1").decode("utf-8")
        # Só aceita se reduziu o nº de caracteres de substituição
        if consertado.count("\ufffd") <= texto.count("\ufffd"):
            texto = consertado
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    return texto.replace("\ufffd", "")


def formatar_cpf(valor) -> str:
    """000.000.000-00 a partir de qualquer entrada suja (inclui float .0)."""
    if _eh_vazio(valor):
        return "—"
    # Remove o ".0" de floats e qualquer caractere não numérico
    digitos = re.sub(r"\D", "", str(valor).split(".")[0])
    if len(digitos) == 11:
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
    return str(valor).strip()  # devolve original se não tiver 11 dígitos


def formatar_telefone(valor) -> str:
    if _eh_vazio(valor):
        return "—"
    bruto = str(valor).strip()
    # Placeholder de importação ("(xx)xxxxxxxx") vira vazio
    if "x" in bruto.lower():
        return "—"
    digitos = re.sub(r"\D", "", bruto)
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    if len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return bruto


def normalizar_titulo(valor) -> str:
    """Title-case respeitando preposições (cidade, bairro, endereço)."""
    if _eh_vazio(valor):
        return "—"
    texto = corrigir_encoding(str(valor).strip())
    palavras = texto.lower().split()
    saida = []
    for i, p in enumerate(palavras):
        saida.append(p if (p in _MINUSCULAS and i != 0) else p.capitalize())
    return " ".join(saida)


def normalizar_uf(valor) -> str:
    """Estado sempre como UF em maiúsculas (MG, SP...)."""
    if _eh_vazio(valor):
        return "—"
    texto = str(valor).strip()
    return texto.upper() if len(texto) == 2 else normalizar_titulo(texto)


def texto_simples(valor) -> str:
    """Para campos livres (nome, observações): corrige encoding e nulos."""
    if _eh_vazio(valor):
        return "—"
    return corrigir_encoding(str(valor).strip())


def formatar_df_clientes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe o DataFrame JÁ RENOMEADO (colunas em PT) e devolve uma cópia
    formatada apenas para exibição. Não altera o original.
    """
    if df is None or df.empty:
        return df
    out = df.copy()
    mapa = {
        "CPF": formatar_cpf,
        "Telefone": formatar_telefone,
        "Cidade": normalizar_titulo,
        "Bairro": normalizar_titulo,
        "Endereço": texto_simples,
        "Estado": normalizar_uf,
        "Nome": texto_simples,
        "Origem": texto_simples,
        "Observações": texto_simples,
    }
    for coluna, func in mapa.items():
        if coluna in out.columns:
            out[coluna] = out[coluna].map(func)
    return out


# ====== UX-2: validação e auxiliares de formulário ======

UFS_BRASIL = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]


def validar_cpf(valor) -> bool:
    digitos = re.sub(r"\D", "", str(valor).split(".")[0])
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    soma = sum(int(digitos[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    dv1 = 0 if resto == 10 else resto
    if dv1 != int(digitos[9]):
        return False
    soma = sum(int(digitos[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    dv2 = 0 if resto == 10 else resto
    return dv2 == int(digitos[10])
MESES_ABREV = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

def data_para_ddmmm(data):
    if data is None:
        return None
    return f"{data.day:02d}/{MESES_ABREV[data.month - 1]}"
