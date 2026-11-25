const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const D = process.argv[2];
  for (const [t, clique] of [['vendas', null], ['financeiro', 'Impostos e MEI'], ['perfil', null]]) {
    const p = await b.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1.5 });
    await p.goto(`http://localhost:8630/?t=${t}`); await p.waitForTimeout(7000);
    if (clique) { await p.getByText(clique).first().click().catch(()=>{}); await p.waitForTimeout(3000); }
    await p.screenshot({ path: `${D}/web_telas/web_${clique ? 'impostos' : t}.png` }); console.log('web', t); await p.close();
  }
  for (const [nome, rota, clique] of [['vendas', '/vendas', null], ['impostos', '/financeiro', 'Impostos']]) {
    const ctx = await b.newContext({ viewport:{width:390,height:844}, isMobile:true, hasTouch:true, deviceScaleFactor:2 });
    await ctx.addInitScript(() => { try { localStorage.setItem('onb_visto_v1','1'); } catch(e){} });
    const p = await ctx.newPage(); await p.goto('http://localhost:8641' + rota); await p.waitForTimeout(6000);
    if (clique) { await p.getByText(clique, { exact: true }).first().click().catch(()=>{}); await p.waitForTimeout(2500); }
    await p.screenshot({ path: `${D}/app_telas/app_${nome}.png` }); console.log('app', nome); await ctx.close();
  }
  await b.close();
})();
