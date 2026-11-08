# Ejemplo 2 — Reporte de ventas automático

> Datos ficticios, creados para mostrar el trabajo.

## El problema
Todos los meses alguien pasaba **medio día** armando el resumen de ventas a mano en Excel: copiar datos, hacer tablas dinámicas, calcular totales y escribir un mail con los números.

## La solución
Un script en Python ([`generar_reporte.py`](generar_reporte.py)) que toma la planilla de ventas (la limpia del [ejemplo 1](../01-limpieza-de-datos/)) y con **un solo comando** genera:

- 📄 **[reporte_ventas.html](reporte_ventas.html)**: un reporte prolijo con indicadores clave, conclusiones escritas automáticamente y el detalle por mes, cliente, producto, vendedor y provincia. Se abre en cualquier navegador o celular.
- 📊 **[reporte_ventas.xlsx](reporte_ventas.xlsx)**: un Excel con una hoja por análisis y los datos completos.

👉 **[Ver el reporte en línea](https://fl0wdatas0luti0nsdev.github.io/freelance-servicios-digitales/portafolio/02-reporte-automatico/reporte_ventas.html)**

## Qué incluye el reporte
- Ventas totales, cantidad de pedidos y ticket promedio
- Comparación con el mes anterior
- Mejor cliente y producto más vendido
- Rankings con barras para comparar de un vistazo

## Cómo correrlo
```bash
pip install pandas openpyxl
python generar_reporte.py ../01-limpieza-de-datos/ventas_limpias.csv
```

Se puede **programar para que corra solo** cada semana o cada mes y que el reporte llegue por mail, sin que nadie tenga que tocar nada.

**Tiempo ahorrado:** de medio día por mes a menos de un minuto.
