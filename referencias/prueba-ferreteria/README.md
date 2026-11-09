# Caso de referencia — "Ferretería de prueba"

> ⚠️ **Todos los datos son ficticios.** La ferretería, los clientes, los CUIT, los vendedores y los montos fueron inventados para probar los agentes de FlowData Solutions. No corresponden a ninguna empresa real.

Este caso muestra el **flujo completo de un proyecto**, de punta a punta, hecho con los agentes de `.claude/agents/`:

```
Planilla desordenada → analista-datos → generador-reportes → control-calidad → entrega
```

## 1. Datos de origen (simulan la exportación de un sistema de facturación)
- [`ventas_octubre_2026.xlsx`](ventas_octubre_2026.xlsx): ventas de octubre con los problemas típicos de una exportación real: títulos encima de la tabla, fila de "TOTAL GENERAL", fechas en 4 formatos, clientes/rubros/vendedores escritos de varias formas, precios como texto, CUIT con y sin guiones, totales y cantidades vacías, 8 duplicados, devoluciones con cantidad negativa y una hoja de objetivos inconsistente.

## 2. Limpieza — agente `analista-datos`
- [`limpiar.py`](limpiar.py): script reproducible que lee el original sin modificarlo.
- [`ventas_octubre_2026_limpio.xlsx`](ventas_octubre_2026_limpio.xlsx): modelo listo para Power BI (`fVentas`, `dClientes`, `dProductos`, `dVendedores`, `dCalendario`, `fObjetivos`), con trazabilidad a la fila original.
- [`informe_limpieza.md`](informe_limpieza.md): cada cambio, la conciliación de totales y las 6 preguntas para el cliente.

**Resultado:** 210 facturas, total neto **$ 79.706.300**, conciliado contra el original (suma del sistema − duplicados + faltantes calculados).

## 3. Reporte — agente `generador-reportes`
- [`reporte/generar_reporte.py`](reporte/generar_reporte.py): genera el reporte web y el Excel desde los datos limpios.
- [`reporte/reporte_ventas_2026-10.html`](reporte/reporte_ventas_2026-10.html): reporte para el dueño (navegador o celular), modo oscuro y claro.
- [`reporte/reporte_ventas_2026-10.xlsx`](reporte/reporte_ventas_2026-10.xlsx): 10 hojas con fórmulas y hoja de control.
- [`reporte/capturas/`](reporte/capturas/): capturas en 375 y 1280 px, oscuro y claro.
- [`reporte/verificar_reporte.js`](reporte/verificar_reporte.js): verificación automática con Playwright.

👉 [Ver el reporte en línea](https://fl0wdatas0luti0nsdev.github.io/freelance-servicios-digitales/referencias/prueba-ferreteria/reporte/reporte_ventas_2026-10.html)

## 4. Control de calidad — agente `control-calidad`
Veredicto: **se puede entregar, sin bloqueantes.** Regeneró el reporte desde cero (idéntico byte a byte), recalculó los totales con pandas y LibreOffice, probó la interfaz en 4 combinaciones y verificó la privacidad. Encontró mejoras que ya se incorporaron a las instrucciones del agente `generador-reportes` (sección "Lecciones aprendidas"):
- Contraste del foco en modo claro (corregido también en la web).
- Textos escritos a mano en el script que fallarían con otro mes.
- Sello "Datos verificados" → "Totales controlados".
- Pendiente de CUIT faltante en las notas.
- Excel sin valores calculados para vistas previas.

> Este reporte es la versión **anterior** a esas mejoras, con una excepción ya aplicada: **en celular, las tablas largas (productos y devoluciones) arrancan plegadas** con las primeras 3 filas y un botón "Ver las N filas". La página en celular bajó de ~9.700 px a ~7.400 px de alto. En escritorio e impresión se ven completas.

## Cómo reproducirlo
```bash
cd referencias/prueba-ferreteria
python limpiar.py
cd reporte
python generar_reporte.py
node verificar_reporte.js reporte_ventas_2026-10.html   # requiere Playwright
```
