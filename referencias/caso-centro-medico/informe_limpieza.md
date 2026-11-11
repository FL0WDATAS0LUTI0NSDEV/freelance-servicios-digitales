# Informe de limpieza — Facturación octubre 2026

Archivo original: `facturacion_octubre_2026.xlsx` (no se modificó)

## Resumen

- Filas leídas debajo del encabezado: **221**
- Fila de pie 'TOTAL GENERAL' (fórmula `=SUM(J5:J224)`) quitada: **1**
- Filas vacías eliminadas: **2** (filas Excel: 125, 224)

## Normalización de formatos

- Fechas escritas como texto convertidas a fecha: **49** (formatos: 15/10/2026, 20261015, 24-10-26)
- **Financiador**: 76 celdas corregidas; 20 variantes -> 5 valores
- **Especialidad**: 128 celdas corregidas; 19 variantes -> 4 valores
- **Profesional**: 121 celdas corregidas; 12 variantes -> 3 valores
- **CUIT**: 39 celdas corregidas; 10 variantes -> 5 valores
- Aranceles guardados como texto ('$ 18.000', '18000,00', '18000') convertidos a número: **44**

## Controles de calidad

- Fechas sin poder interpretar: **0**; fuera de octubre 2026: **0**
- Valores fuera de catálogo (obra social, especialidad o profesional): **0**
- CUIT distintos por obra social (máximo): **1**; aranceles distintos por prestación: **1**; especialidades por prestación: **1**
- Filas completas donde Cantidad x Precio no coincide con Total: **0** de 197

## Datos completados

- Totales vacíos calculados como Cantidad x Precio: **20** (filas Excel: 17, 21, 22, 31, 39, 70, 75, 81, 87, 98, 99, 102, 105, 134, 173, 176, 178, 189, 210, 213)
- Cantidades vacías calculadas como Total / Precio: **1** (filas Excel: 5)

## Duplicados

- Filas duplicadas eliminadas: **8** (se conserva la primera aparición)
  - B-0003-00020193: fila 68 repite la fila 47 (Total $480.000)
  - B-0003-00020021: fila 97 repite la fila 20 (Total $156.000)
  - B-0003-00020122: fila 139 repite la fila 95 (Total $336.000)
  - B-0003-00020017: fila 158 repite la fila 89 (Total $260.000)
  - B-0003-00020123: fila 183 repite la fila 14 (Total $312.000)
  - B-0003-00020128: fila 199 repite la fila 155 (Total $740.000)
  - B-0003-00020206: fila 216 repite la fila 154 (Total $666.000)
  - B-0003-00020057: fila 218 repite la fila 147 (Total $286.000)
- Números de factura repetidos con datos distintos: **0**

## Débitos (cantidades negativas)

- Renglones con cantidad negativa: **8**, total **-$588.000**. Se conservan con signo negativo y se marcan en `Tipo_Movimiento`.

## Hoja Objetivos

- Laura Ibáñez: sin cambios
- Martín Suárez: nombre 'Martin Suarez' -> 'Martín Suárez'; monto texto '3.300.000' -> 3.300.000
- Sofía Ríos: nombre 'Sofia Rios' -> 'Sofía Ríos'
- Profesionales de objetivos que no figuran en la facturación: **0**

## Verificación de totales

- Suma de la columna Total en el original (lo que da `=SUM(J5:J224)`): **$77.427.000**
- Menos Total original de los duplicados eliminados: **-$3.236.000**
- Más totales que estaban vacíos y se calcularon: **+$7.743.000**
- Total esperado: **$81.934.000** | Total limpio (neto): **$81.934.000** ✔ coinciden
- Facturación bruta: **$82.522.000** | Débitos: **-$588.000**
- Renglones finales: **210** (facturas únicas: 210)

## Facturación neta vs. objetivo por profesional

| Profesional | Facturación neta | Objetivo | Cumplimiento |
|---|---:|---:|---:|
| Laura Ibáñez | $34.670.000 | $5.200.000 | 667% |
| Martín Suárez | $25.026.000 | $3.300.000 | 758% |
| Sofía Ríos | $22.238.000 | $4.100.000 | 542% |

## Valores únicos después de limpiar

- **Financiador** (5): Cobertura Norte, Mutual del Sur, Obra Social Andina, Plan Salud Pampa, Prepaga Litoral Salud
- **Prestacion** (9): Consulta clínica, Consulta pediátrica, Control de niño sano, Ecocardiograma, Ecografía abdominal, Ecografía obstétrica, Electrocardiograma, Ergometría, Radiografía de tórax
- **Especialidad** (4): Cardiología, Clínica Médica, Diagnóstico por Imágenes, Pediatría
- **Profesional** (3): Laura Ibáñez, Martín Suárez, Sofía Ríos

## Pendiente de decidir con el cliente

1. **Débitos:** 8 renglones con cantidad negativa numerados como facturas (no como notas de crédito). ¿Son débitos reales de las obras sociales (prestaciones rechazadas) o errores de carga? Hoy se incluyen restando.
2. **Duplicados:** se eliminaron 8 renglones idénticos (misma factura). Confirmar que es un error de la exportación y no una factura cargada dos veces en el sistema.
3. **Faltantes calculados:** 20 totales y 1 cantidad se completaron con Cantidad x Precio (marcados en `Origen_Dato`). Confirmar si hubo descuentos.
4. **CUIT:** 1 de 5 CUIT no pasa el dígito verificador (Cobertura Norte 30-99000172-2). No se modificaron.
5. **Objetivos:** la facturación neta supera el objetivo entre 542% y 758%. Confirmar si los objetivos están en la misma unidad que la facturación (¿pesos? ¿miles? ¿semanales? ¿solo particulares?) antes de mostrar % de cumplimiento en el dashboard.
6. **Total del sistema:** la fórmula `=SUM(J5:J224)` del original suma duplicados y deja afuera los totales vacíos; no usarla como cifra de control.
