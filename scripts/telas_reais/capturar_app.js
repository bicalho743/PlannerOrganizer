// Telas reais do app (Expo no navegador, conta demo_landing): fotos 390x844 @2x e vídeos 600x1298 rolando
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');
const BASE = 'http://localhost:8641', SAIDA = process.argv[2];
const TELAS = [['inicio','/'],['propostas','/propostas'],['agenda','/agenda'],['financeiro','/financeiro'],
  ['precificacao','/precificacao'],['pos','/pos'],['clientes','/clientes'],['relatorios','/relatorios'],['menu','/menu']];
const VIDEOS = [['precificacao','/precificacao'],['propostas','/propostas'],['retornos','/pos'],['agenda','/agenda'],['financeiro','/financeiro']];
async function preparar(p, rota) {
  if (rota !== '/precificacao') return;
  await p.getByText('Preço de um projeto').first().click().catch(()=>{}); await p.waitForTimeout(1200);
  for (const i of [0, 1, 6]) { await p.locator('[aria-label="mais"]').nth(i).click().catch(()=>{}); await p.waitForTimeout(600); }
  await p.waitForTimeout(800);
  const el = await rolavel(p); await p.evaluate((el) => { if (el) el.scrollTo(0, 0); }, el); await p.waitForTimeout(600);
}
async function rolavel(p) {
  return p.evaluateHandle(() => { let m = null, mh = 0;
    for (const el of document.querySelectorAll('div')) { const cs = getComputedStyle(el);
      if (/(auto|scroll)/.test(cs.overflowY) && el.scrollHeight > el.clientHeight + 40 && el.clientHeight > 300) {
        const h = el.scrollHeight - el.clientHeight; if (h > mh) { mh = h; m = el; } } }
    return m; });
}
(async () => {
  const b = await chromium.launch();
  const novo = async (extra = {}) => { const ctx = await b.newContext({ viewport:{width:390,height:844}, isMobile:true, hasTouch:true, ...extra });
    await ctx.addInitScript(() => { try { localStorage.setItem('onb_visto_v1','1'); } catch(e){} }); return ctx; };
  for (const [nome, rota] of TELAS) {
    const ctx = await novo({ deviceScaleFactor: 2 }); const p = await ctx.newPage();
    await p.goto(BASE + rota); await p.waitForTimeout(6000); await preparar(p, rota);
    await p.screenshot({ path: path.join(SAIDA, `app_${nome}.png`) });
    console.log('foto', nome); await ctx.close();
  }
  for (const [nome, rota] of VIDEOS) {
    const ctx = await novo({ deviceScaleFactor: 600/390, recordVideo: { dir: path.join(SAIDA, '_bruto'), size: { width: 600, height: 1298 } } });
    const p = await ctx.newPage(); const t0 = Date.now();
    await p.goto(BASE + rota); await p.waitForTimeout(5500); await preparar(p, rota);
    await p.screenshot({ path: path.join(SAIDA, `${nome}.jpg`), type: 'jpeg', quality: 84 });
    const inicio = (Date.now() - t0) / 1000;
    await p.waitForTimeout(1200);
    const el = await rolavel(p);
    for (let i = 0; i <= 60; i++) { await p.evaluate(([el, f]) => { if (el) el.scrollTo(0, (el.scrollHeight - el.clientHeight) * f * 0.8); }, [el, i/60]); await p.waitForTimeout(115); }
    await p.waitForTimeout(1500);
    const video = await p.video().path(); await ctx.close();
    for (const [ext, args] of [['mp4', ['-c:v','libx264','-pix_fmt','yuv420p','-crf','28','-movflags','+faststart']], ['webm', ['-c:v','libvpx-vp9','-crf','38','-b:v','0']]])
      execFileSync('ffmpeg', ['-y','-loglevel','error','-ss',String(inicio),'-i',video,'-an',...args, path.join(SAIDA, `${nome}.${ext}`)]);
    console.log('vídeo', nome);
  }
  fs.rmSync(path.join(SAIDA, '_bruto'), { recursive: true, force: true });
  await b.close();
})().catch(e => { console.error('ERRO', e.message); process.exit(1); });
