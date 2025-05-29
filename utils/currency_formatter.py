"""
Utilitário para formatação de moeda brasileira
"""

def format_currency_br(value):
    """
    Formata um valor como moeda brasileira no padrão correto
    Exemplo: 1234.56 -> R$ 1.234,56
    
    Args:
        value: Valor numérico (float ou int)
        
    Returns:
        str: Valor formatado como moeda brasileira
    """
    try:
        # Converter para float se não for
        if isinstance(value, str):
            # Remove caracteres não numéricos exceto ponto e vírgula
            value = value.replace('R$', '').replace(' ', '')
            # Converte vírgula para ponto se necessário
            if ',' in value and '.' not in value:
                value = value.replace(',', '.')
            elif ',' in value and '.' in value:
                # Se tem ambos, assume formato brasileiro (1.234,56)
                value = value.replace('.', '').replace(',', '.')
            value = float(value)
        
        # Formatar no padrão brasileiro
        formatted = f"R$ {value:,.2f}"
        # Trocar separadores para padrão brasileiro
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        
        return formatted
        
    except (ValueError, TypeError):
        return "R$ 0,00"

def format_value_br(value, include_currency=True):
    """
    Formata um valor numérico no padrão brasileiro
    
    Args:
        value: Valor numérico
        include_currency: Se deve incluir o símbolo R$
        
    Returns:
        str: Valor formatado
    """
    try:
        if isinstance(value, str):
            value = value.replace('R$', '').replace(' ', '')
            if ',' in value and '.' not in value:
                value = value.replace(',', '.')
            elif ',' in value and '.' in value:
                value = value.replace('.', '').replace(',', '.')
            value = float(value)
        
        formatted = f"{value:,.2f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        
        if include_currency:
            return f"R$ {formatted}"
        else:
            return formatted
            
    except (ValueError, TypeError):
        return "0,00" if not include_currency else "R$ 0,00"