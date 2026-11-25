"""
Monta o vídeo "O app em 1 minuto e meio" da landing com as telas REAIS novas, no tempo da narração atual.

Uso: python3 montar_tour.py <horizontal|vertical> <saida.mp4>
- horizontal (1920x1080): telas do site no computador (web_*.png), com a moldura do navegador.
- vertical (1080x1920): telas do app (app_*.png) em moldura de celular.
Áudio: narracao_antiga.mp3 (a mesma narração; os temas das telas continuam os mesmos).
"""
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = "/tmp/claude-0/-home-user/ac9bca1e-440f-585e-897d-28876c56361c/scratchpad"
FONTES = "/home/user/planner-app/marketing/video/2026-11-vsl/fontes/"
NAVY, GOLD, GOLD_TX, CREME, MUTED = (13, 27, 42), (201, 168, 76), (138, 106, 28), (247, 245, 240), (91, 107, 128)
FPS = 30
DUR = 91.08
CORTES = [0, 7.0, 16.2, 25.3, 30.9, 36.4, 43.9, 49.8, 55.4, 62.8, 68.4, 74.4, 79.0, 82.7, DUR]
TRANS = 0.45

SLIDES = [
    ("Seu dia numa tela só", "Lucro do mês, contas a receber e a lista do que fazer hoje.", "inicio", "inicio", (0.3, 0.3)),
    ("Agenda que junta tudo", "Serviços, visitas, retornos, aniversários e contas no mesmo lugar.", "agenda", "agenda", (0.5, 0.4)),
    ("Lembrete de aniversário", "A cliente faz aniversário e você é avisada, com os parabéns prontos no WhatsApp.", "agenda", "agenda", (0.85, 0.45)),
    ("Clientes organizadas", "Cadastro rápido com telefone, origem e aniversário.", "clientes", "clientes", (0.4, 0.4)),
    ("Do orçamento ao serviço", "Proposta em PDF com a sua marca, do envio à finalização.", "propostas", "propostas", (0.5, 0.45)),
    ("Saiba quanto cobrar", "Sua hora e o preço de cada projeto, com os seus números.", "precificacao", "precificacao", (0.7, 0.4)),
    ("Venda de produtos", "Estoque, parcelas e o lucro de cada venda.", "vendas", "vendas", (0.4, 0.35)),
    ("Nunca mais esqueça de retornar uma cliente", "O app lembra no dia certo, com a mensagem pronta no WhatsApp.", "pos", "pos", (0.5, 0.5)),
    ("Financeiro sem planilha", "Quanto entrou, quanto gastou e quanto sobrou no mês.", "financeiro", "financeiro", (0.35, 0.4)),
    ("MEI e Simples Nacional", "DAS de cada mês, limite do ano e prazo da declaração.", "impostos", "impostos", (0.4, 0.45)),
    ("Relatórios prontos", "O resultado do período em PDF e em Excel, para você e o contador.", "relatorios", "relatorios", (0.4, 0.35)),
    ("Com a sua marca", "Logotipo e cores em todas as propostas e relatórios.", "pdf", "pdf", (0.5, 0.3)),
]
PDF_CORES = ["dourado", "marinho", "verde", "rosa", "ameixa", "azul"]


def fonte(nome, tam):
    return ImageFont.truetype(FONTES + nome, tam)


def quebra(dr, txt, f, larg):
    linhas, atual = [], ""
    for p in txt.split():
        t = (atual + " " + p).strip()
        if dr.textlength(t, font=f) <= larg:
            atual = t
        else:
            linhas.append(atual)
            atual = p
    return linhas + [atual]


def sombra(img, raio, desloc=18, op=70):
    s = Image.new("RGBA", (img.width + raio * 4, img.height + raio * 4), (0, 0, 0, 0))
    m = Image.new("RGBA", img.size, (13, 27, 42, op))
    s.paste(m, (raio * 2, raio * 2 + desloc))
    return s.filter(ImageFilter.GaussianBlur(raio))


def arredondar(img, r):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, img.width - 1, img.height - 1), r, fill=255)
    out = img.convert("RGBA")
    out.putalpha(m)
    return out


# ───────── telas (imagem já emoldurada, guardada em cache) ─────────
_cache = {}


def tela_pc(nome, larg):
    chave = ("pc", nome, larg)
    if chave in _cache:
        return _cache[chave]
    if nome == "pdf":
        img = None
    else:
        img = Image.open(f"{RAIZ}/web_telas/web_{nome}.png").convert("RGB")
    barra = 46
    alt = int(larg * 900 / 1440)
    quadro = Image.new("RGB", (larg, alt + barra), (238, 240, 243))
    dr = ImageDraw.Draw(quadro)
    for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        dr.ellipse((20 + i * 24, 16, 34 + i * 24, 30), fill=c)
    dr.rounded_rectangle((110, 10, 520, 36), 8, fill=(255, 255, 255))
    dr.text((126, 15), "app.plannerorganiza.com.br", font=fonte("dmsans_medium.ttf", 16), fill=(102, 112, 133))
    quadro.paste(img.resize((larg, alt), Image.LANCZOS), (0, barra))
    q = arredondar(quadro, 16)
    _cache[chave] = q
    return q


def tela_cel(nome, larg):
    chave = ("cel", nome, larg)
    if chave in _cache:
        return _cache[chave]
    img = Image.open(f"{RAIZ}/app_telas/app_{nome}.png").convert("RGB")
    borda, status = int(larg * 0.035), int(larg * 0.085)
    tela_w = larg - 2 * borda
    tela_h = int(tela_w * 844 / 390)
    alt = tela_h + status + int(larg * 0.05) + 2 * borda
    corpo = Image.new("RGBA", (larg, alt), (0, 0, 0, 0))
    dr = ImageDraw.Draw(corpo)
    dr.rounded_rectangle((0, 0, larg - 1, alt - 1), int(larg * 0.15), fill=(11, 15, 20))
    tela = Image.new("RGB", (tela_w, alt - 2 * borda), (250, 248, 243))
    td = ImageDraw.Draw(tela)
    f = fonte("dmsans_bold.ttf", int(status * 0.42))
    td.text((int(tela_w * 0.09), int(status * 0.28)), "9:41", font=f, fill=(16, 24, 40))
    ilha_w = int(tela_w * 0.28)
    td.rounded_rectangle(((tela_w - ilha_w) // 2, int(status * 0.18), (tela_w + ilha_w) // 2, int(status * 0.82)), 40, fill=(11, 15, 20))
    bx = tela_w - int(tela_w * 0.09) - 40
    td.rounded_rectangle((bx, int(status * 0.33), bx + 36, int(status * 0.67)), 5, outline=(16, 24, 40), width=2)
    td.rectangle((bx + 4, int(status * 0.33) + 4, bx + 28, int(status * 0.67) - 4), fill=(16, 24, 40))
    tela.paste(img.resize((tela_w, tela_h), Image.LANCZOS), (0, status))
    ind_y = status + tela_h + int(larg * 0.025)
    td.rounded_rectangle((int(tela_w * 0.33), ind_y, int(tela_w * 0.67), ind_y + 7), 4, fill=(16, 24, 40))
    tela = arredondar(tela, int(larg * 0.12))
    corpo.alpha_composite(tela, (borda, borda))
    _cache[chave] = corpo
    return corpo


def pdf_img(cor, larg):
    chave = ("pdf", cor, larg)
    if chave not in _cache:
        img = Image.open(f"{RAIZ}/demo_pdf/proposta_{cor}.png").convert("RGB")
        _cache[chave] = img.resize((larg, int(img.height * larg / img.width)), Image.LANCZOS)
    return _cache[chave]


# ───────── quadros ─────────
def fundo_slide(W, H, i, titulo, legenda, vertical):
    base = Image.new("RGB", (W, H), CREME)
    dr = ImageDraw.Draw(base)
    dr.rectangle((60 if not vertical else 70, 52 if not vertical else 90, 78 if not vertical else 92, 70 if not vertical else 112), fill=GOLD)
    dr.text((92 if not vertical else 108, 46 if not vertical else 84), "Planner Organiza", font=fonte("cormorant_semibold.ttf", 30 if not vertical else 40), fill=NAVY)
    if vertical:
        x, y, larg = 70, 200, W - 140
        tam_t, tam_l = 76, 36
    else:
        x, y, larg = 70, 330, 520
        tam_t, tam_l = 64, 27
    dr.text((x, y), f"{i + 1:02d}", font=fonte("dmsans_bold.ttf", 26 if not vertical else 32), fill=GOLD_TX)
    y += 46 if not vertical else 56
    ft = fonte("cormorant_semibold.ttf", tam_t)
    for ln in quebra(dr, titulo, ft, larg):
        dr.text((x, y), ln, font=ft, fill=NAVY)
        y += int(tam_t * 1.05)
    y += 24
    dr.rectangle((x, y, x + 64, y + 4), fill=GOLD)
    y += 30
    fl = fonte("dmsans_medium.ttf", tam_l)
    for ln in quebra(dr, legenda, fl, larg):
        dr.text((x, y), ln, font=fl, fill=MUTED)
        y += int(tam_l * 1.45)
    # pontinhos de progresso
    py = H - 60 if not vertical else H - 90
    for k in range(12):
        cx = (70 if not vertical else 70) + k * 22
        dr.ellipse((cx, py, cx + 9, py + 9), fill=GOLD if k == i else (214, 208, 194))
    return base


def quadro_slide(W, H, i, t, dur, vertical, base):
    titulo, legenda, web, app, (fx, fy) = SLIDES[i]
    img = base.copy().convert("RGBA")
    p = min(max(t / dur, 0), 1)
    z = 1 + 0.05 * p
    if app == "pdf":
        cor = PDF_CORES[min(int(p * len(PDF_CORES)), len(PDF_CORES) - 1)]
        larg = 560 if not vertical else 860
        pg = pdf_img(cor, larg).crop((0, 0, larg, int(larg * 1.18)))
        pg = arredondar(pg, 10)
        ox = (W - larg) // 2 + (180 if not vertical else 0)
        oy = 150 if not vertical else 640
        img.alpha_composite(sombra(pg, 20), (ox - 40, oy - 40))
        img.alpha_composite(pg, (ox, oy))
        return img.convert("RGB")
    if vertical:
        cel = tela_cel(app, 480)
        cw, ch = int(cel.width * z), int(cel.height * z)
        c2 = cel.resize((cw, ch), Image.BILINEAR)
        ox, oy = (W - cw) // 2, 660 - int((ch - cel.height) * fy)
        img.alpha_composite(sombra(c2, 26), (ox - 52, oy - 52))
        img.alpha_composite(c2, (ox, oy))
    else:
        pc = tela_pc(web, 1180)
        cw, ch = int(pc.width * z), int(pc.height * z)
        p2 = pc.resize((cw, ch), Image.BILINEAR)
        ox, oy = 660 - int((cw - pc.width) * fx), 170 - int((ch - pc.height) * fy)
        img.alpha_composite(sombra(p2, 26), (ox - 52, oy - 52))
        img.alpha_composite(p2, (ox, oy))
    return img.convert("RGB")


def quadro_capa(W, H, t, vertical):
    img = Image.new("RGB", (W, H), NAVY)
    dr = ImageDraw.Draw(img)
    a = min(max((t - 0.3) / 0.8, 0), 1)
    tam = 84 if not vertical else 96
    f = fonte("cormorant_semibold.ttf", tam)
    linhas = [("Personal organizer,", (255, 255, 255)), ("ainda controla tudo", (255, 255, 255)), ("no caderno?", GOLD)]
    y0 = H // 2 - int(tam * 1.9)
    dr.rounded_rectangle((W // 2 - 17, y0 - 90, W // 2 + 17, y0 - 56), 6, fill=GOLD)
    for k, (ln, cor) in enumerate(linhas):
        c = tuple(int(NAVY[j] + (cor[j] - NAVY[j]) * a) for j in range(3))
        w = dr.textlength(ln, font=f)
        dr.text(((W - w) / 2, y0 + k * int(tam * 1.1)), ln, font=f, fill=c)
    b = min(max((t - 1.6) / 0.8, 0), 1)
    fs = fonte("dmsans_medium.ttf", 34 if not vertical else 40)
    txt = "Conheça o Planner Organiza"
    c = tuple(int(NAVY[j] + ((200, 210, 222)[j] - NAVY[j]) * b) for j in range(3))
    dr.text(((W - dr.textlength(txt, font=fs)) / 2, y0 + int(tam * 3.6)), txt, font=fs, fill=c)
    return img


def quadro_fim(W, H, t, vertical):
    img = Image.new("RGB", (W, H), NAVY)
    dr = ImageDraw.Draw(img)
    a = min(max(t / 0.6, 0), 1)
    tam = 70 if not vertical else 80
    f = fonte("cormorant_semibold.ttf", tam)
    linhas = ["Agenda, propostas, financeiro", "e MEI num lugar só."] if not vertical else \
        ["Agenda, propostas,", "financeiro e MEI", "num lugar só."]
    y = H // 2 - int(tam * 1.3 * len(linhas) / 2) - 60
    for ln in linhas:
        c = tuple(int(NAVY[j] + (255 - NAVY[j]) * a) for j in range(3))
        dr.text(((W - dr.textlength(ln, font=f)) / 2, y), ln, font=f, fill=c)
        y += int(tam * 1.15)
    y += 50
    fb = fonte("dmsans_bold.ttf", 36 if not vertical else 42)
    txt = "Teste grátis por 7 dias"
    bw = dr.textlength(txt, font=fb) + 90
    dr.rounded_rectangle(((W - bw) / 2, y, (W + bw) / 2, y + 86), 43, fill=GOLD)
    dr.text(((W - dr.textlength(txt, font=fb)) / 2, y + 22), txt, font=fb, fill=NAVY)
    fu = fonte("dmsans_medium.ttf", 34 if not vertical else 40)
    u = "plannerorganiza.com.br"
    dr.text(((W - dr.textlength(u, font=fu)) / 2, y + 130), u, font=fu, fill=(200, 210, 222))
    return img


def main():
    modo, saida = sys.argv[1], sys.argv[2]
    vertical = modo == "vertical"
    W, H = (1080, 1920) if vertical else (1920, 1080)
    bases = [fundo_slide(W, H, i, s[0], s[1], vertical) for i, s in enumerate(SLIDES)]
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-i", f"{RAIZ}/tour/narracao_antiga.mp3", "-c:v", "libx264",
                             "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                             "-shortest", "-movflags", "+faststart", saida], stdin=subprocess.PIPE)

    def quadro(t):
        for k in range(len(CORTES) - 1):
            if CORTES[k] <= t < CORTES[k + 1]:
                break
        ini, fim = CORTES[k], CORTES[k + 1]
        if k == 0:
            return quadro_capa(W, H, t, vertical)
        if k == len(CORTES) - 2:
            return quadro_fim(W, H, t - ini, vertical)
        i = k - 1
        return quadro_slide(W, H, i, t - ini, fim - ini, vertical, bases[i])

    n = int(DUR * FPS)
    ant = None
    for f in range(n):
        t = f / FPS
        img = quadro(t)
        # transição suave nos cortes
        for c in CORTES[1:-1]:
            if c <= t < c + TRANS:
                a = (t - c) / TRANS
                img = Image.blend(quadro(c - 1 / FPS), img, a)
                break
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    proc.wait()
    print("pronto", saida)


if __name__ == "__main__":
    main()
