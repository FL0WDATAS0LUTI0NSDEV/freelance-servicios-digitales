# Caso de referencia — "Centro médico de prueba"

> ⚠️ **Todos los datos son ficticios.** El centro médico, las obras sociales y prepagas, los CUIT, los profesionales y los montos fueron inventados para probar los agentes de FlowData Solutions. No corresponden a ninguna institución real. **No hay datos de pacientes:** cada renglón es una liquidación a una obra social o prepaga.

Este caso muestra el **flujo completo de un proyecto**, de punta a punta, hecho con los agentes de `.claude/agents/`:

```
Exportación desordenada → analista-datos → generador-reportes → control-calidad → entrega
```

## 1. Datos de origen (simulan la exportación de un sistema de facturación médica)
- [`generar_datos.py`](generar_datos.py): arma la exportación con semilla fija, así el caso se puede reproducir desde cero.
- [`facturacion_octubre_2026.xlsx`](facturacion_octubre_2026.xlsx): facturación de octubre a obras sociales y prepagas, con los problemas típicos de una exportación real: títulos encima de la tabla, fila de "TOTAL GENERAL", fechas en 4 formatos, obras sociales, especialidades y profesionales escritos de varias formas, aranceles como texto, CUIT con y sin guiones, totales y cantidades vacías, 8 duplicados, **débitos** de las obras sociales cargados con cantidad negativa y una hoja de objetivos inconsistente.

## 2. Limpieza — agente `analista-datos`
- [`limpiar.py`](limpiar.py): script reproducible que lee el original sin modificarlo.
- [`facturacion_octubre_2026_limpio.xlsx`](facturacion_octubre_2026_limpio.xlsx): modelo listo para Power BI (`fFacturacion`, `dFinanciadores`, `dPrestaciones`, `dProfesionales`, `dCalendario`, `fObjetivos`), con trazabilidad a la fila original.
- [`informe_limpieza.md`](informe_limpieza.md): cada cambio, la conciliación de totales y las 6 preguntas para el cliente.

**Resultado:** 210 facturas, facturación neta **$ 81.934.000**, conciliada contra el original (suma del sistema − duplicados + faltantes calculados).

## 3. Reporte — agente `generador-reportes`
- [`reporte/generar_reporte.py`](reporte/generar_reporte.py): genera el reporte web y el Excel desde los datos limpios.
- [`reporte/reporte_facturacion_2026-10.html`](reporte/reporte_facturacion_2026-10.html): reporte para la dirección del centro (navegador o celular), modo oscuro y claro. Facturación por día y semana, por especialidad, por profesional, por obra social y por prestación, y detalle de débitos.
- [`reporte/reporte_facturacion_2026-10.xlsx`](reporte/reporte_facturacion_2026-10.xlsx): 10 hojas con fórmulas (ya recalculadas, con valores) y hoja de control.
- [`reporte/capturas/`](reporte/capturas/): capturas en 375 y 1280 px, oscuro y claro.
- [`reporte/verificar_reporte.js`](reporte/verificar_reporte.js): verificación automática con Playwright.

👉 [Ver el reporte en línea](https://fl0wdatas0luti0nsdev.github.io/freelance-servicios-digitales/referencias/caso-centro-medico/reporte/reporte_facturacion_2026-10.html)

## 4. Control de calidad — agente `control-calidad`
Las reglas que salieron de los controles de calidad quedaron en las instrucciones del agente `generador-reportes` (sección "Lecciones aprendidas") y **están aplicadas en este reporte**:

1. **Ningún texto dependiente de datos escrito a mano.** La cantidad de duplicados y el total de la fórmula "TOTAL GENERAL" se leen de `informe_limpieza.md`, solo si el informe corresponde a los datos (mismo total neto, cantidad de renglones y mes); si no, esas frases se omiten. La relación facturación / objetivo sale de un solo cálculo con un solo redondeo, igual en el HTML, el Excel y las notas. El período se toma de las fechas con datos: si el archivo trae medio mes, el reporte lo dice.
2. **Bloque CONFIG** al principio de `generar_reporte.py`: cliente, archivo de entrada por defecto, nombre del informe de limpieza, `OBJETIVOS_CONFIRMADOS` y recálculo del Excel. Además, `--salida CARPETA` para generar en otra carpeta.
3. **Sello "Totales controlados"** con un solo indicador (punto).
4. **Notas sobre los datos:** débitos a confirmar, faltantes calculados, duplicados quitados y CUIT de obras sociales que no pasan el dígito verificador (hoy 1 de 5), calculado desde `dFinanciadores[CUIT_Valido]`.
5. **Excel con valores calculados:** se recalcula con LibreOffice y el script controla cero errores, que el Resumen coincida con los totales y que la hoja Control dé OK.
6. **Foco en modo claro** en azul `#0066FF` (contraste AA sobre fondo claro).
7. **Signo menos (−, U+2212)** en todos los negativos: indicadores, tabla de débitos y formatos del Excel.
8. **Sin Google Fonts** (reporte confidencial: no pide nada a internet).
9. **Lenguaje neutro** en los destacados: el texto no supone el género de cada profesional.

En celular, las tablas largas (prestaciones y débitos) arrancan plegadas con las primeras 3 filas y un botón "Ver las N filas". En escritorio e impresión se ven completas.

## Requisitos para correrlo en tu computadora
- **Python 3** con `pandas` y `openpyxl`: `pip install pandas openpyxl`.
- **LibreOffice** (gratis, https://www.libreoffice.org/download/): el script lo usa para guardar el Excel con los valores ya calculados. Lo encuentra solo en las ubicaciones habituales de Windows, macOS y Linux; si lo instalaste en otro lugar, definí la variable `SOFFICE` con la ruta a `soffice`. Sin LibreOffice el reporte se genera igual y el Excel se calcula al abrirlo.
- **Node.js + Playwright** solo para `verificar_reporte.js` (opcional): `npm install playwright` y `npx playwright install chromium`.

## Cómo reproducirlo
```bash
cd referencias/caso-centro-medico
python generar_datos.py          # exportación desordenada (semilla fija)
python limpiar.py
cd reporte
python generar_reporte.py                                    # requiere LibreOffice para recalcular el Excel
# python generar_reporte.py otro_mes_limpio.xlsx --salida otra_carpeta
node verificar_reporte.js reporte_facturacion_2026-10.html   # requiere Playwright
```
