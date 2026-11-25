const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const D = process.argv[2];
  for (const t of ['inicio','clientes','agenda','propostas','precificacao','financeiro','pos','relatorios']) {
    const p = await b.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1.5 });
    await p.goto(`http://localhost:8630/?t=${t}`); await p.waitForTimeout(7000);
    if (t === 'precificacao') { await p.getByText('Preço de um projeto').first().click().catch(()=>{}); await p.waitForTimeout(2500);
      await p.getByRole('button', { name: 'Cozinha' }).first().click().catch(()=>{}); await p.waitForTimeout(2000); }
    const erro = await p.locator('[data-testid="stException"]').count();
    await p.screenshot({ path: `${D}/web_${t}.png` }); console.log(t, erro ? 'ERRO' : 'ok'); await p.close();
  }
  await b.close();
})();
