from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1243/chrome-linux64/chrome')
    pg = b.new_page(viewport={'width':1280,'height':900})
    pg.goto('https://personalhelp.com.br/#planos', wait_until='networkidle')
    for y in range(0, 12000, 600):
        pg.mouse.wheel(0,600); pg.wait_for_timeout(250)
    pg.locator('#planos').scroll_into_view_if_needed(); pg.wait_for_timeout(4000)
    print(pg.inner_text('#planos'))
    pg.locator('#planos').screenshot(path='planos.png')
    for el in pg.locator('#duvidas button, #duvidas summary').all():
        try: el.click(); pg.wait_for_timeout(150)
        except: pass
    print('====FAQ'); print(pg.inner_text('#duvidas'))
    pg.goto('https://personalhelp.com.br/demo/', wait_until='networkidle'); pg.wait_for_timeout(3000)
    pg.screenshot(path='demo.png'); print('====DEMO'); print(pg.inner_text('body')[:1500])
    b.close()
