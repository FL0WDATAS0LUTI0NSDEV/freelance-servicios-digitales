// Verifica el reporte HTML: errores de consola, scroll horizontal, pedidos externos,
// tablas plegadas (celular) y completas (escritorio), color del foco, signo menos
// y capturas en 375 px y 1280 px, modo oscuro y claro.
// Uso: node verificar_reporte.js reporte_facturacion_2026-10.html
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const archivo = path.resolve(__dirname, process.argv[2] || 'reporte_facturacion_2026-10.html');
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
      // Reporte confidencial: no puede pedir nada fuera del archivo (ni fuentes de Google)
      page.on('request', (r) => { if (!/^(file|data|about):/.test(r.url())) errores.push('pedido externo ' + r.url()); });
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
      // Foco visible: cian en oscuro, azul #0066FF en claro (contraste AA sobre fondo claro)
      await page.keyboard.press('Tab');
      const foco = await page.evaluate(() => getComputedStyle(document.activeElement).outlineColor);
      const focoOk = foco === (tema === 'light' ? 'rgb(0, 102, 255)' : 'rgb(0, 229, 255)');
      await page.evaluate(() => document.activeElement.blur());
      // Tablas largas: en celular 3 filas + botón; en escritorio todas y sin botón
      const folds = await page.evaluate(() => [...document.querySelectorAll('[data-fold]')].map((f) => {
        const filas = [...f.querySelectorAll('tbody tr')];
        const btn = f.querySelector('.fold__btn');
        return { total: filas.length, visibles: filas.filter((r) => r.getClientRects().length > 0).length,
          boton: btn.getClientRects().length > 0 ? btn.textContent : null };
      }));
      let foldsOk = folds.length > 0 && folds.every((f) => ancho < 720
        ? f.visibles === 3 && f.boton === `Ver las ${f.total} filas`
        : f.visibles === f.total && f.boton === null);
      if (ancho < 720 && foldsOk) { // al tocar el botón se ven todas
        await page.click('[data-fold] .fold__btn');
        const abierta = await page.evaluate(() => { const f = document.querySelector('[data-fold]');
          return [...f.querySelectorAll('tbody tr')].every((r) => r.getClientRects().length > 0) &&
            f.querySelector('.fold__btn').getAttribute('aria-expanded') === 'true'; });
        foldsOk = abierta;
        await page.click('[data-fold] .fold__btn');
      }
      // Negativos con signo menos (U+2212), nunca con guion
      const guiones = await page.evaluate(() => [...document.querySelectorAll('.num, td.r, .kpi__value')]
        .map((e) => e.textContent.trim()).filter((t) => /^-|-\s?\$|\s-\d/.test(t)));
      const ok = info.scrollW <= info.clientW && errores.length === 0 && info.tema === tema && !info.desbordes.length &&
        foldsOk && focoOk && !guiones.length;
      if (!ok) fallas++;
      await page.evaluate(() => { document.activeElement.blur(); window.scrollTo(0, 0); });
      await page.mouse.move(0, 0);
      const captura = path.join(dir, `${base}_${ancho}_${tema}.png`);
      await page.screenshot({ path: captura, fullPage: true });
      console.log(`${ok ? 'OK ' : 'MAL'} ${ancho}px ${tema}: scroll ${info.scrollW}/${info.clientW}, neto ${info.neto}, ` +
        `facturas ${info.facturas}, errores ${errores.length}${errores.length ? ' ' + errores.join(' | ') : ''}` +
        `${info.desbordes.length ? ', desbordes ' + info.desbordes.join(', ') : ''}` +
        `, tablas plegables ${folds.map((f) => f.visibles + '/' + f.total + (f.boton ? ' +botón' : '')).join(' y ')}${foldsOk ? '' : ' MAL'}` +
        `, foco ${foco}${focoOk ? '' : ' MAL'}${guiones.length ? ', negativos con guion ' + guiones.join(' ') : ''} -> ${captura}`);
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
