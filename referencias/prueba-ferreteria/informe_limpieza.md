# Informe de limpieza — Ventas octubre 2026

Archivo original: `ventas_octubre_2026.xlsx` (no se modificó)

## Resumen

- Filas leídas debajo del encabezado: **221**
- Fila de pie 'TOTAL GENERAL' (fórmula `=SUM(J5:J224)`) quitada: **1**
- Filas vacías eliminadas: **2** (filas Excel: 125, 224)

## Normalización de formatos

- Fechas escritas como texto convertidas a fecha: **55** (formatos: 15/10/2026, 20261015, 24-10-26)
- **Cliente**: 72 celdas corregidas; 18 variantes -> 5 valores
- **Rubro**: 108 celdas corregidas; 16 variantes -> 4 valores
- **Vendedor**: 86 celdas corregidas; 9 variantes -> 3 valores
- **CUIT**: 39 celdas corregidas; 10 variantes -> 5 valores
- Precios unitarios guardados como texto ('$ 9.800', '9800,00', '3200') convertidos a número: **53**

## Controles de calidad

- Fechas sin poder interpretar: **0**; fuera de octubre 2026: **0**
- Valores fuera de catálogo (cliente, rubro o vendedor): **0**
- CUIT distintos por cliente (máximo): **1**; precios distintos por producto: **1**; rubros por producto: **1**
- Filas completas donde Cantidad x Precio no coincide con Total: **0** de 197

## Datos completados

- Totales vacíos calculados como Cantidad x Precio: **20** (filas Excel: 9, 31, 32, 41, 43, 47, 61, 65, 81, 86, 98, 100, 110, 113, 120, 161, 185, 196, 204, 215)
- Cantidades vacías calculadas como Total / Precio: **1** (filas Excel: 55)

## Duplicados

- Filas duplicadas eliminadas: **8** (se conserva la primera aparición)
  - A-0001-00010059: fila 86 repite la fila 65 (Total $480.000)
  - A-0001-00010040: fila 109 repite la fila 45 (Total $1.860.000)
  - A-0001-00010143: fila 156 repite la fila 141 (Total $1.426.000)
  - A-0001-00010145: fila 158 repite la fila 150 (Total $136.800)
  - A-0001-00010157: fila 170 repite la fila 77 (Total $1.584.000)
  - A-0001-00010083: fila 186 repite la fila 92 (Total $70.200)
  - A-0001-00010183: fila 197 repite la fila 48 (Total $306.000)
  - A-0001-00010194: fila 208 repite la fila 80 (Total $199.800)
- Números de factura repetidos con datos distintos: **0**

## Devoluciones (cantidades negativas)

- Renglones con cantidad negativa: **10**, total **-$782.600**. Se conservan con signo negativo y se marcan en `Tipo_Movimiento`.

## Hoja Objetivos

- Jorge Ibáñez: sin cambios
- Paula Suárez: nombre 'Paula Suarez' -> 'Paula Suárez'; monto texto '3.800.000' -> 3.800.000
- Diego Ríos: nombre 'Diego Rios' -> 'Diego Ríos'
- Vendedores de objetivos que no figuran en ventas: **0**

## Verificación de totales

- Suma de la columna Total en el original (lo que da `=SUM(J5:J224)`): **$76.851.800**
- Menos Total original de los duplicados eliminados: **-$5.582.800**
- Más totales que estaban vacíos y se calcularon: **+$8.437.300**
- Total esperado: **$79.706.300** | Total limpio (neto): **$79.706.300** ✔ coinciden
- Ventas brutas: **$80.488.900** | Devoluciones: **-$782.600**
- Renglones finales: **210** (facturas únicas: 210)

## Ventas netas vs. objetivo por vendedor

| Vendedor | Ventas netas | Objetivo | Cumplimiento |
|---|---:|---:|---:|
| Jorge Ibáñez | $33.867.000 | $4.500.000 | 753% |
| Paula Suárez | $18.677.300 | $3.800.000 | 492% |
| Diego Ríos | $27.162.000 | $4.200.000 | 647% |

## Valores únicos después de limpiar

- **Cliente** (5): Bulonera Rosario, Construcciones Delta, Corralón Los Pinos, Ferretería San Martín, Pinturerías Norte
- **Producto** (7): Cable 2.5mm x100m, Cinta métrica 5m, Llave térmica 20A, Martillo carpintero, Pintura látex 20L, Rodillo lana 22cm, Tornillo 6x40 x100
- **Rubro** (4): Bulonería, Electricidad, Herramientas, Pinturas
- **Vendedor** (3): Diego Ríos, Jorge Ibáñez, Paula Suárez

## Pendiente de decidir con el cliente

1. **Devoluciones:** 10 renglones con cantidad negativa numerados como facturas (no como notas de crédito). ¿Son devoluciones reales que restan de la venta del vendedor, o errores de carga? Hoy se incluyen restando.
2. **Duplicados:** se eliminaron 8 renglones idénticos (misma factura). Confirmar que es un error de la exportación y no una factura cargada dos veces en el sistema.
3. **Faltantes calculados:** 20 totales y 1 cantidad se completaron con Cantidad x Precio (marcados en `Origen_Dato`). Confirmar si hubo descuentos.
4. **CUIT:** 4 de 5 CUIT no pasan el dígito verificador (Bulonera Rosario 20-31222333-5, Construcciones Delta 30-71999888-2, Ferretería San Martín 20-28765432-9, Pinturerías Norte 30-70011223-4). No se modificaron.
5. **Objetivos:** las ventas netas superan el objetivo entre 492% y 753%. Confirmar si los objetivos están en la misma unidad que las ventas (¿pesos? ¿miles? ¿semanales? ¿sin IVA?) antes de mostrar % de cumplimiento en el dashboard.
6. **Total del sistema:** la fórmula `=SUM(J5:J224)` del original suma duplicados y deja afuera los totales vacíos; no usarla como cifra de control.
