// Verifica el reporte HTML: errores de consola, scroll horizontal y capturas
// en 375 px y 1280 px, modo oscuro y claro.
// Uso: node verificar_reporte.js reporte_ventas_2026-10.html
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const archivo = path.resolve(__dirname, process.argv[2] || 'reporte_ventas_2026-10.html');
  const base = path.basename(archivo, '.html');
  const dir = path.join(__dirname, 'capturas');
  require('fs').mkdirSync(dir, { recursive: true });
  const browser = await chromium.launch();
  let fallas = 0;
  for (const ancho of [375, 1280]) {
    for (const tema of ['dark', 'light']) {
      const ctx = await browser.newContext({ viewport: { width: ancho, height: 900 }, deviceScaleFactor: 1 });
      await ctx.addInitScript((t) => { try { localStorage.setItem('fds-theme', t); } catch (e) {} }, tema);
      const page = await ctx.newPage();
      const errores = [];
      page.on('console', (m) => { if (m.type() === 'error') errores.push(m.text()); });
      page.on('pageerror', (e) => errores.push(e.message));
      page.on('requestfailed', (r) => errores.push('requestfailed ' + r.url()));
      await page.goto('file://' + archivo, { waitUntil: 'networkidle' });
      await page.evaluate(() => document.fonts.ready);
      const info = await page.evaluate(() => ({
        tema: document.documentElement.dataset.theme,
        scrollW: document.documentElement.scrollWidth,
        clientW: document.documentElement.clientWidth,
        neto: document.querySelector('.kpi--main .kpi__value').textContent,
        facturas: document.querySelectorAll('.kpi__value')[1].textContent,
        desbordes: [...document.querySelectorAll('body *')].filter((el) => {
          const r = el.getBoundingClientRect();
          return r.width && (r.right > document.documentElement.clientWidth + 0.5 || r.left < -0.5) && !el.closest('.sr-only, .skip') &&
            !(el.closest('thead') && getComputedStyle(el.closest('thead')).clip !== 'auto'); // encabezado oculto en vista apilada
        }).map((el) => el.tagName + '.' + el.className).slice(0, 5),
      }));
      const ok = info.scrollW <= info.clientW && errores.length === 0 && info.tema === tema && !info.desbordes.length;
      if (!ok) fallas++;
      const captura = path.join(dir, `${base}_${ancho}_${tema}.png`);
      await page.screenshot({ path: captura, fullPage: true });
      console.log(`${ok ? 'OK ' : 'MAL'} ${ancho}px ${tema}: scroll ${info.scrollW}/${info.clientW}, neto ${info.neto}, ` +
        `facturas ${info.facturas}, errores ${errores.length}${errores.length ? ' ' + errores.join(' | ') : ''}` +
        `${info.desbordes.length ? ', desbordes ' + info.desbordes.join(', ') : ''} -> ${captura}`);
      // El botón de tema cambia el modo y lo recuerda
      if (ancho === 1280 && tema === 'dark') {
        await page.click('#theme-toggle');
        const t = await page.evaluate(() => [document.documentElement.dataset.theme, localStorage.getItem('fds-theme')]);
        console.log(`    toggle de tema: ${t.join(' / ')}`);
        if (t[0] !== 'light' || t[1] !== 'light') fallas++;
      }
      await ctx.close();
    }
  }
  await browser.close();
  process.exit(fallas ? 1 : 0);
})();
