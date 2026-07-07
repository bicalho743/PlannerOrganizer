def fmt_brl(value) -> str:
    try:
        if value is None:
            return "R$ 0,00"
        f = float(value)
        if f != f:  # NaN (nan != nan) — evita "R$ nan" em qualquer exibição de dinheiro
            return "R$ 0,00"
        return f"R$ {f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"

format_currency_br = fmt_brl
format_value_br = fmt_brl
format_currency = fmt_brl
_fmt_brl = fmt_brl
