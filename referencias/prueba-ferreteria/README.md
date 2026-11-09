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
- [`reporte/reporte_ventas_2026-10.xlsx`](reporte/reporte_ventas_2026-10.xlsx): 10 hojas con fórmulas (ya recalculadas, con valores) y hoja de control.
- [`reporte/capturas/`](reporte/capturas/): capturas en 375 y 1280 px, oscuro y claro.
- [`reporte/verificar_reporte.js`](reporte/verificar_reporte.js): verificación automática con Playwright.

👉 [Ver el reporte en línea](https://fl0wdatas0luti0nsdev.github.io/freelance-servicios-digitales/referencias/prueba-ferreteria/reporte/reporte_ventas_2026-10.html)

## 4. Control de calidad — agente `control-calidad`
Veredicto: **se puede entregar, sin bloqueantes.** Regeneró el reporte desde cero, recalculó los totales con pandas y LibreOffice, probó la interfaz en 4 combinaciones y verificó la privacidad. Las mejoras que encontró quedaron en las instrucciones del agente `generador-reportes` (sección "Lecciones aprendidas") y **ya están aplicadas en este reporte**:

1. **Ningún texto dependiente de datos escrito a mano.** La cantidad de duplicados y el total de la fórmula "TOTAL GENERAL" se leen de `informe_limpieza.md`, solo si el informe corresponde a los datos (mismo total neto, cantidad de renglones y mes); si no, esas frases se omiten. La relación venta / objetivo sale de un solo cálculo con un solo redondeo, igual en el HTML, el Excel y las notas ("entre 4,9 y 7,5 veces"). El período se toma de las fechas con datos: si el archivo trae medio mes, el reporte lo dice y no informa el mes completo.
2. **Bloque CONFIG** al principio de `generar_reporte.py`: cliente, archivo de entrada por defecto, nombre del informe de limpieza, `OBJETIVOS_CONFIRMADOS` y recálculo del Excel. Además, `--salida CARPETA` para generar en otra carpeta.
3. **Sello "Totales controlados"** con un solo indicador (punto), en lugar de "✓ Datos verificados".
4. **Notas sobre los datos:** se suma el pendiente de los CUIT que no pasan el dígito verificador (hoy 4 de 5), calculado desde `dClientes[CUIT_Valido]`.
5. **Excel con valores calculados:** después de generarlo con openpyxl se recalcula con LibreOffice (`recalc.py` de la skill xlsx o, si no está, `soffice --convert-to xlsx`) y el script controla cero errores, que el Resumen tenga valores y coincida con los totales, y que la hoja Control dé OK.
6. **Foco en modo claro** en azul `#0066FF` (contraste AA sobre fondo claro).
7. **Signo menos (−, U+2212)** en todos los negativos: indicadores, tabla de devoluciones (cantidad y monto) y formatos del Excel.
8. **Sin Google Fonts** (reporte confidencial: no pide nada a internet). Usa Inter / Plus Jakarta Sans si están instaladas y, si no, las fuentes del sistema.

Se mantiene la mejora anterior: **en celular, las tablas largas (productos y devoluciones) arrancan plegadas** con las primeras 3 filas y un botón "Ver las N filas". En escritorio e impresión se ven completas.

`verificar_reporte.js` ahora también controla: ningún pedido externo, tablas plegadas en 375 px (3 filas + botón, y que el botón las abra) y completas en 1280 px, color del foco en cada tema y que no haya negativos con guion.

## Requisitos para correrlo en tu computadora
- **Python 3** con `pandas` y `openpyxl`: `pip install pandas openpyxl`.
- **LibreOffice** (gratis, https://www.libreoffice.org/download/): el script lo usa para guardar el Excel con los valores ya calculados. Lo encuentra solo en las ubicaciones habituales de Windows, macOS y Linux; si lo instalaste en otro lugar, definí la variable `SOFFICE` con la ruta a `soffice`. Sin LibreOffice el reporte se genera igual y el Excel se calcula al abrirlo.
- **Node.js + Playwright** solo para `verificar_reporte.js` (opcional): `npm install playwright` y `npx playwright install chromium`.

## Cómo reproducirlo
```bash
cd referencias/prueba-ferreteria
python limpiar.py
cd reporte
python generar_reporte.py                               # requiere LibreOffice para recalcular el Excel
# python generar_reporte.py otro_mes_limpio.xlsx --salida otra_carpeta
node verificar_reporte.js reporte_ventas_2026-10.html   # requiere Playwright
```
