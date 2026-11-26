from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1243/chrome-linux64/chrome')
    pg = b.new_page(viewport={'width':1280,'height':900})
    pg.goto('https://personalhelp.com.br/demo/', wait_until='networkidle'); pg.wait_for_timeout(2000)
    for nome in ['Meus valores','Orçamentos','Agenda']:
        try:
            pg.get_by_text(nome, exact=True).first.click(); pg.wait_for_timeout(2000)
            print('=====',nome); print(pg.inner_text('main') if pg.locator('main').count() else pg.inner_text('body')[:3000])
        except Exception as e: print('ERRO',nome,e)
    try:
        pg.get_by_text('Clientes', exact=True).first.click(); pg.wait_for_timeout(1500)
        pg.get_by_text('Criar orçamento').first.click(); pg.wait_for_timeout(2000)
        print('===== NOVO ORCAMENTO'); print(pg.inner_text('body')[:4000])
        pg.screenshot(path='orc.png', full_page=True)
    except Exception as e: print('ERRO orc', e)
    b.close()
