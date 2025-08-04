"""
Utilitário para criar tooltips personalizados no Streamlit
"""
import streamlit as st

def create_tooltip(texto_explicativo, icone="ℹ️", tamanho_icone="18px", cor="#666"):
    """
    Cria um tooltip HTML com CSS personalizado
    
    Args:
        texto_explicativo (str): Texto que aparece no hover
        icone (str): Ícone a ser exibido (padrão: ℹ️)
        tamanho_icone (str): Tamanho do ícone CSS (padrão: 18px)
        cor (str): Cor do ícone (padrão: #666)
    
    Returns:
        str: HTML do tooltip
    """
    return f"""
    <div style="margin-top: 8px;">
        <span title="{texto_explicativo}" style="cursor: help; color: {cor}; font-size: {tamanho_icone};">{icone}</span>
    </div>
    """

def create_inline_tooltip(texto, texto_explicativo, cor_texto="#333"):
    """
    Cria um tooltip inline diretamente no texto
    
    Args:
        texto (str): Texto a ser exibido
        texto_explicativo (str): Explicação no hover
        cor_texto (str): Cor do texto
    
    Returns:
        str: HTML do tooltip inline
    """
    return f"""
    <span title="{texto_explicativo}" style="cursor: help; color: {cor_texto}; text-decoration: underline dotted;">{texto}</span>
    """

def header_with_tooltip(titulo, explicacao, nivel="subheader"):
    """
    Cria um cabeçalho com tooltip explicativo
    
    Args:
        titulo (str): Título do cabeçalho
        explicacao (str): Texto explicativo do tooltip
        nivel (str): Tipo de cabeçalho ('header', 'subheader', 'title')
    """
    col_titulo, col_help = st.columns([4, 1])
    
    with col_titulo:
        if nivel == "header":
            st.header(titulo)
        elif nivel == "subheader":
            st.subheader(titulo)
        elif nivel == "title":
            st.title(titulo)
        else:
            st.write(f"**{titulo}**")
    
    with col_help:
        st.markdown(create_tooltip(explicacao), unsafe_allow_html=True)

def metric_with_tooltip(label, value, explicacao, delta=None):
    """
    Cria uma métrica com tooltip explicativo
    
    Args:
        label (str): Rótulo da métrica
        value (str/int/float): Valor da métrica
        explicacao (str): Explicação do tooltip
        delta (str/int/float, optional): Variação da métrica
    """
    col_metric, col_help = st.columns([4, 1])
    
    with col_metric:
        st.metric(label=label, value=value, delta=delta)
    
    with col_help:
        st.markdown(create_tooltip(explicacao), unsafe_allow_html=True)

def input_with_tooltip(tipo_input, label, explicacao, **kwargs):
    """
    Cria um input com tooltip explicativo
    
    Args:
        tipo_input (str): Tipo do input ('text_input', 'number_input', 'selectbox', etc.)
        label (str): Label do input
        explicacao (str): Explicação do tooltip
        **kwargs: Argumentos adicionais para o input
    
    Returns:
        Valor do input
    """
    # Criar o label com tooltip inline
    label_com_tooltip = f"""
    <label style="font-size: 14px; font-weight: 600; margin-bottom: 4px; display: block;">
        {label} 
        <span title="{explicacao}" style="cursor: help; color: #666; font-size: 14px; margin-left: 5px;">ℹ️</span>
    </label>
    """
    
    st.markdown(label_com_tooltip, unsafe_allow_html=True)
    
    # Criar o input sem label (já criamos acima)
    input_function = getattr(st, tipo_input)
    return input_function(label="", **kwargs)

# Exemplos de uso para diferentes componentes:

def exemplo_tooltips():
    """Demonstra diferentes tipos de tooltips"""
    
    st.title("Exemplos de Tooltips")
    
    # 1. Cabeçalho com tooltip
    header_with_tooltip("Vendas Totais", "Soma de todas as vendas realizadas no período selecionado")
    
    # 2. Métrica com tooltip
    metric_with_tooltip("Receita", "R$ 15.430,00", "Total de receitas brutas do mês atual", delta="12%")
    
    # 3. Input com tooltip
    valor = input_with_tooltip(
        "number_input", 
        "Valor do Produto", 
        "Digite o preço de venda do produto em reais", 
        min_value=0.0, 
        format="%.2f"
    )
    
    # 4. Texto inline com tooltip
    st.markdown(f"""
    Este é um texto normal, mas aqui temos um 
    {create_inline_tooltip('termo técnico', 'Explicação detalhada do termo técnico')} 
    que precisa de explicação.
    """, unsafe_allow_html=True)
    
    # 5. Tooltip simples ao lado de qualquer elemento
    col1, col2 = st.columns([4, 1])
    with col1:
        st.selectbox("Status da Venda", ["Pendente", "Concluída", "Cancelada"])
    with col2:
        st.markdown(create_tooltip("Status atual da venda no sistema"), unsafe_allow_html=True)