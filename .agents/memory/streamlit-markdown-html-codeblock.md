---
name: Streamlit markdown HTML code-block trap
description: Why raw HTML <span>/<div> text shows up literally in st.markdown(unsafe_allow_html=True) cards
---

When building HTML for `st.markdown(..., unsafe_allow_html=True)`, never rely on
multiline f-strings with indented lines plus conditional fragments.

**Symptom:** raw HTML (e.g. `<span ...>📍 Geral</span>`) appears as literal text
in the UI instead of rendering.

**Why:** A conditional fragment like `{x if cond else ''}` on its own line
collapses to an empty string when false, leaving a BLANK line inside the HTML
block. In CommonMark, a blank line followed by a line indented 4+ spaces is an
indented code block — so the following indented HTML is shown verbatim. The
opening `f"""` newline + indented `<div>` can trigger the same thing.

**How to apply:** Build card/badge HTML as a single concatenated string with NO
leading indentation and NO blank lines. Precompute optional fragments into a
variable (e.g. `desc_html = "<br>..." if desc else ""`) and inline it, rather
than putting the ternary on its own indented line. Affected builders live in
`pages/propostas_unificado.py` (card/badge renderers).
