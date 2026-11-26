import sys, json
from playwright.sync_api import sync_playwright
urls = sys.argv[1:]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1243/chrome-linux64/chrome')
    pg = b.new_page(viewport={'width':1280,'height':900})
    for u in urls:
        try:
            pg.goto(u, wait_until='networkidle', timeout=45000)
        except Exception as e:
            print('ERRO', u, e); continue
        pg.wait_for_timeout(1500)
        txt = pg.inner_text('body')
        links = sorted(set(pg.eval_on_selector_all('a[href]', 'els=>els.map(e=>e.href)')))
        name = u.replace('https://','').replace('/','_').replace('#','_')[:60]
        open(name+'.txt','w').write(txt)
        print('=====', u, len(txt)); print('LINKS:', [l for l in links][:80])
    b.close()
