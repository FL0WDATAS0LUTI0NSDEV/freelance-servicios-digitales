# Ejemplo 1 — Limpieza y orden de una planilla de ventas

> Datos ficticios, creados para mostrar el trabajo.

## El problema
Una distribuidora cargaba sus ventas a mano entre tres vendedores. Después de tres meses, la planilla tenía:

| Problema | Ejemplo en la planilla original |
|---|---|
| Fechas en 4 formatos distintos | `2026-02-05`, `10/01/2026`, `03/03/26`, `5-3-26` |
| El mismo cliente escrito de varias formas | `Bar El Faro`, `BAR EL FARO`, `  bar el faro ` |
| Productos inconsistentes | `Café 500g`, `CAFÉ 500G`, `Café  500g` |
| Vendedores abreviados | `Laura Gómez`, `Laura G.`, `laura gómez` |
| Provincias sin criterio | `Córdoba`, `cba`, `Cordoba`, `CÓRDOBA` |
| Montos con distintos formatos | `$65.100,00`, `30000,00`, `15500` |
| Datos faltantes | cantidades y montos vacíos |
| Filas duplicadas y vacías | 6 duplicadas, 1 vacía |

Con la planilla así, **no se podía saber cuánto vendió cada cliente** ni hacer un resumen confiable.

## La solución
Un script en Python ([`limpiar.py`](limpiar.py)) que en un segundo:
1. Unifica fechas, nombres, productos, vendedores y provincias.
2. Convierte todos los montos a números.
3. Completa cantidades y montos faltantes usando el precio unitario de cada producto.
4. Elimina filas vacías y duplicadas.
5. Genera un informe con todo lo que cambió.

## Resultado
| Antes | Después |
|---|---|
| [`ventas_original.csv`](ventas_original.csv): 77 filas, 58 formas distintas de escribir clientes, productos, vendedores y provincias | [`ventas_limpias.csv`](ventas_limpias.csv): 70 filas, 6 clientes, 5 productos, 3 vendedores, 3 provincias |

Detalle completo en el [informe de limpieza](informe_limpieza.md).

## Cómo correrlo
```bash
pip install pandas
python limpiar.py ventas_original.csv ventas_limpias.csv
```

El mismo proceso sirve para **listas de clientes, stock, inscripciones, facturación** o cualquier planilla que se cargue a mano.
