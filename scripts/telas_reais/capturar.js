// Grava as telas reais do sistema (conta demo_landing) para a landing.
// Uso: node capturar.js <url-base> <pasta-de-saida>
// Gera, para cada passo da seção "Como funciona": <nome>.jpg (capa), <nome>.mp4 e <nome>.webm (600x1298, ~10 s,
// rolando a tela) e, para todas as telas, tela_<nome>_computador.png (1440x900 @2x).
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const BASE = process.argv[2] || 'http://localhost:8630';
const SAIDA = path.resolve(process.argv[3] || path.join(__dirname, 'saida'));
fs.mkdirSync(SAIDA, { recursive: true });

// nome do arquivo da landing → tela do sistema e o que fazer antes de gravar
const PASSOS = [
  { nome: 'precificacao', t: 'precificacao', antes: async (p) => {
      await p.getByText('Preço de um projeto').first().click().catch(() => {});
      await p.waitForTimeout(2500);
      await p.getByRole('button', { name: 'Cozinha' }).first().click().catch(() => {});
      await p.waitForTimeout(2000);
      await p.getByRole('button', { name: /Closet/ }).first().click().catch(() => {});
      await p.waitForTimeout(2500);
  } },
  { nome: 'propostas', t: 'propostas' },
  { nome: 'retornos', t: 'pos' },
  { nome: 'agenda', t: 'agenda' },
  { nome: 'financeiro', t: 'financeiro' },
];
const COMPUTADOR = ['inicio', 'agenda', 'propostas', 'precificacao', 'clientes', 'pos', 'financeiro', 'relatorios', 'vendas', 'perfil'];

async function rolar(p, ms) {
  // desce devagar até o fim do conteúdo (o Streamlit rola dentro do bloco principal)
  const passos = 60;
  for (let i = 0; i <= passos; i++) {
    await p.evaluate((f) => {
      const el = document.querySelector('[data-testid="stMain"]') || document.scrollingElement;
      el.scrollTo(0, (el.scrollHeight - el.clientHeight) * f * 0.85);
    }, i / passos);
    await p.waitForTimeout(ms / passos);
  }
}

(async () => {
  const b = await chromium.launch();
  for (const passo of PASSOS) {
    const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 600 / 390,
      recordVideo: { dir: path.join(SAIDA, '_bruto'), size: { width: 600, height: 1298 } } });
    const p = await ctx.newPage();
    const t0 = Date.now();
    await p.goto(`${BASE}/?t=${passo.t}`);
    await p.waitForTimeout(7000);
    if (passo.antes) await passo.antes(p);
    await p.screenshot({ path: path.join(SAIDA, `${passo.nome}.jpg`), type: 'jpeg', quality: 82 });
    const inicio = (Date.now() - t0) / 1000;
    await p.waitForTimeout(1200);
    await rolar(p, 7000);
    await p.waitForTimeout(1500);
    const video = await p.video().path();
    await ctx.close();
    const mp4 = path.join(SAIDA, `${passo.nome}.mp4`), webm = path.join(SAIDA, `${passo.nome}.webm`);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(inicio), '-i', video, '-an', '-c:v', 'libx264',
      '-pix_fmt', 'yuv420p', '-crf', '28', '-movflags', '+faststart', mp4]);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(inicio), '-i', video, '-an', '-c:v', 'libvpx-vp9',
      '-crf', '38', '-b:v', '0', webm]);
    console.log('vídeo', passo.nome);
  }
  for (const t of COMPUTADOR) {
    const p = await b.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
    await p.goto(`${BASE}/?t=${t}`);
    await p.waitForTimeout(7000);
    await p.screenshot({ path: path.join(SAIDA, `tela_${t}_computador.png`) });
    const erro = await p.locator('[data-testid="stException"]').count();
    console.log('tela', t, erro ? 'COM ERRO' : 'ok');
    await p.close();
  }
  fs.rmSync(path.join(SAIDA, '_bruto'), { recursive: true, force: true });
  await b.close();
})().catch((e) => { console.error('ERRO', e.message); process.exit(1); });
