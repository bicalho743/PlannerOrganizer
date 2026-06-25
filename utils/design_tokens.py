NAVY = "#0D1B2A"
NAVY_HOVER = "#162840"
GOLD = "#C9A84C"
GOLD_DARK = "#B8943D"
GOLD_LIGHT = "#E8D5A3"

SUCCESS = "#38A169"
SUCCESS_BG = "#C6F6D5"
SUCCESS_FG = "#276749"
DANGER = "#E53E3E"
DANGER_BG = "#FED7D7"
DANGER_FG = "#9B2C2C"
WARNING = "#D69E2E"
WARNING_BG = "#FEFCBF"
WARNING_FG = "#744210"

TEXT_PRIMARY = "#1a202c"
TEXT_SECONDARY = "#64748b"
TEXT_MUTED = "#6c757d"
BORDER = "#e2e8f0"
BORDER_LIGHT = "#dee2e6"
BG_CARD = "#fff"
BG_SUBTLE = "#faf9f7"

FONT_SIZE_H1 = "2rem"
FONT_SIZE_H2 = "1.5rem"
FONT_SIZE_H3 = "1.15rem"
FONT_SIZE_BASE = "0.95rem"
FONT_SIZE_CAPTION = "0.85rem"

SPACE_XXS = "0.25rem"
SPACE_XS = "0.5rem"
SPACE_SM = "0.75rem"
SPACE_MD = "1rem"
SPACE_LG = "1.5rem"
SPACE_XL = "2rem"

CARD_RADIUS = "10px"
CARD_PADDING = "1rem"
CARD_SHADOW = "0 10px 30px rgba(0, 0, 0, 0.08)"

GLOBAL_CSS_VARS = f"""
:root {{
    --navy: {NAVY};
    --navy-hover: {NAVY_HOVER};
    --gold: {GOLD};
    --gold-dark: {GOLD_DARK};
    --gold-light: {GOLD_LIGHT};
    --success: {SUCCESS};
    --success-bg: {SUCCESS_BG};
    --success-fg: {SUCCESS_FG};
    --danger: {DANGER};
    --danger-bg: {DANGER_BG};
    --danger-fg: {DANGER_FG};
    --warning: {WARNING};
    --warning-bg: {WARNING_BG};
    --warning-fg: {WARNING_FG};
    --text-primary: {TEXT_PRIMARY};
    --text-secondary: {TEXT_SECONDARY};
    --text-muted: {TEXT_MUTED};
    --border: {BORDER};
    --border-light: {BORDER_LIGHT};
    --bg-card: {BG_CARD};
    --bg-subtle: {BG_SUBTLE};
    --font-h1: {FONT_SIZE_H1};
    --font-h2: {FONT_SIZE_H2};
    --font-h3: {FONT_SIZE_H3};
    --font-base: {FONT_SIZE_BASE};
    --font-caption: {FONT_SIZE_CAPTION};
    --space-xxs: {SPACE_XXS};
    --space-xs: {SPACE_XS};
    --space-sm: {SPACE_SM};
    --space-md: {SPACE_MD};
    --space-lg: {SPACE_LG};
    --space-xl: {SPACE_XL};
    --card-radius: {CARD_RADIUS};
    --card-padding: {CARD_PADDING};
    --card-shadow: {CARD_SHADOW};
}}
"""

GOLD_GRADIENT = f"linear-gradient(135deg, {GOLD}, {GOLD_DARK})"
GOLD_BUTTON_CSS = f"""
    button {{
        background: {GOLD_GRADIENT} !important;
        color: #fff !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 12px 32px !important;
        border-radius: 10px !important;
        border: none !important;
        letter-spacing: 0.02em !important;
        box-shadow: 0 3px 12px rgba(201,168,76,0.35) !important;
    }}
"""

NAVY_CARD_CSS = f"""
    background:{NAVY};border-radius:10px;padding:16px;text-align:center;min-height:80px;
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    cursor:pointer;transition:all 0.2s;border:1px solid transparent;
"""

NAVY_CARD_HOVER = f"this.style.background='{NAVY_HOVER}';this.style.transform='translateY(-2px)';this.style.boxShadow='0 4px 12px rgba(0,0,0,0.3)'"
NAVY_CARD_OUT = f"this.style.background='{NAVY}';this.style.transform='none';this.style.boxShadow='none'"
