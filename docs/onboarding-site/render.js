const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  for (const f of fs.readdirSync(path.join(__dirname, 'telas')).filter(x => x.endsWith('.html')).sort()) {
    await p.goto('file://' + path.join(__dirname, 'telas', f), { waitUntil: 'load' }); await p.waitForTimeout(300);
    await p.screenshot({ path: path.join(__dirname, 'telas', f.replace('.html', '.png')), clip: { x: 0, y: 0, width: 390, height: 844 } });
  } await b.close(); })();
