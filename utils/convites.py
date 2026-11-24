"""
Convites com teste grátis estendido (ex.: 30 dias em vez dos 7 padrão).

- A tabela `convites` guarda os códigos gerados pelo admin (scripts/criar_convite.py).
- Quando alguém cria a conta e digita o código, a tabela `convites_resgatados` registra
  quantos dias de teste essa conta ganhou. Cada conta usa um convite só.
- O trial (utils/trial.py) lê esses dias; sem convite continua valendo DIAS_TRIAL.
"""
import secrets
from sqlalchemy import text

# Sem letras e números parecidos (O/0, I/1) para o código ser fácil de digitar
ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
DIAS_CONVITE_PADRAO = 30


class ConviteInvalido(ValueError):
    """Mensagem já pronta para mostrar ao usuário."""


_TABELAS_PRONTAS = set()  # engines em que as tabelas já foram conferidas neste processo


def criar_tabelas(engine) -> None:
    _TABELAS_PRONTAS.add(id(engine))
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS convites ("
            "codigo TEXT PRIMARY KEY, dias INTEGER NOT NULL DEFAULT 30, "
            "criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP, usado_por TEXT, usado_em TIMESTAMP)"))
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS convites_resgatados ("
            "usuario_id TEXT PRIMARY KEY, codigo TEXT NOT NULL, dias INTEGER NOT NULL, "
            "resgatado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))


def normalizar_codigo(codigo: str) -> str:
    return "".join(ch for ch in (codigo or "").upper() if ch.isalnum())


def gerar_codigo() -> str:
    """Código no formato ABCDE-FGHJK."""
    parte = lambda: "".join(secrets.choice(ALFABETO) for _ in range(5))
    return f"{parte()}-{parte()}"


def novo_convite(engine, dias: int = DIAS_CONVITE_PADRAO) -> str:
    criar_tabelas(engine)
    codigo = gerar_codigo()
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO convites (codigo, dias) VALUES (:c, :d)"),
                     {"c": normalizar_codigo(codigo), "d": dias})
    return codigo


def resgatar(engine, uid: str, codigo: str) -> int:
    """Liga o convite à conta. Devolve os dias de teste. Levanta ConviteInvalido se não der."""
    criar_tabelas(engine)
    chave = normalizar_codigo(codigo)
    if not chave:
        raise ConviteInvalido("Digite o código do convite.")
    with engine.begin() as conn:
        ja = conn.execute(text("SELECT dias FROM convites_resgatados WHERE usuario_id = :u"),
                          {"u": uid}).first()
        if ja:
            raise ConviteInvalido("Esta conta já usou um convite.")
        linha = conn.execute(text("SELECT dias, usado_por FROM convites WHERE codigo = :c"),
                             {"c": chave}).first()
        if not linha:
            # não é convite: pode ser o código de uma afiliada (utils/afiliados.py)
            from utils import afiliados
            try:
                afiliados.vincular(engine, uid, chave, origem="codigo")
            except afiliados.AfiliadoInvalido as e:
                raise ConviteInvalido(str(e) if "próprio" in str(e) or "já foi" in str(e)
                                      else "Convite não encontrado. Confira o código.")
            # o código da afiliada só liga a conta a ela: o teste continua o padrão
            return afiliados.DIAS_TESTE_INDICADA
        # UPDATE condicional: se outra conta usou o código no mesmo instante, a linha não muda
        marcado = conn.execute(text(
            "UPDATE convites SET usado_por = :u, usado_em = CURRENT_TIMESTAMP "
            "WHERE codigo = :c AND usado_por IS NULL"), {"u": uid, "c": chave}).rowcount
        if marcado != 1:
            raise ConviteInvalido("Este convite já foi usado.")
        dias = int(linha.dias)
        conn.execute(text(
            "INSERT INTO convites_resgatados (usuario_id, codigo, dias) VALUES (:u, :c, :d)"),
            {"u": uid, "c": chave, "d": dias})
    return dias


def dias_trial_da_conta(engine, uid) -> int:
    """Dias de teste desta conta: os do convite, se usou um, senão o padrão (DIAS_TRIAL).
    Web e API usam esta função para valerem os mesmos dias."""
    from utils.trial import DIAS_TRIAL
    return (dias_do_convite(engine, uid) if uid else None) or DIAS_TRIAL


def dias_do_convite(engine, uid: str):
    """Dias de teste do convite usado por esta conta, ou None se não usou convite."""
    try:
        if id(engine) not in _TABELAS_PRONTAS:  # sem isso a consulta falha até o 1º convite ser usado
            criar_tabelas(engine)
        with engine.connect() as conn:
            linha = conn.execute(text("SELECT dias FROM convites_resgatados WHERE usuario_id = :u"),
                                 {"u": uid}).first()
        return int(linha.dias) if linha else None
    except Exception as e:
        print(f"[convites] {e}")
        return None
