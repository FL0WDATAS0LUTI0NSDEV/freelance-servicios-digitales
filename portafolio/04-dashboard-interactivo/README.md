# Ejemplo 4 — Dashboard de ventas interactivo

> Datos ficticios, creados para mostrar el trabajo.

👉 **[Abrir el dashboard](https://fl0wdatas0luti0nsdev.github.io/freelance-servicios-digitales/portafolio/04-dashboard-interactivo/)**

## El problema
La distribuidora tenía un año de ventas en una planilla, pero para responder preguntas simples —*¿qué mes vendimos más? ¿qué cliente pesa más en Córdoba? ¿cómo viene el segundo semestre contra el primero?*— había que armar tablas dinámicas cada vez.

## La solución
Un tablero web que se abre en cualquier navegador o celular, sin instalar nada:

- **Filtros** por período (desde / hasta), provincia, vendedor, producto y cliente.
- **Indicadores clave**: ventas, pedidos, ticket promedio y unidades, con la **variación contra el período anterior** de la misma duración.
- **Gráficos interactivos**: ventas por mes (clic en una barra para filtrar ese mes), por provincia, top clientes, productos y vendedores (clic en un nombre para filtrar).
- **Tabla de detalle** con búsqueda, orden por columna y botón **Exportar CSV** con lo filtrado.
- **Modo oscuro y claro**, accesible con teclado y pensado para celular.

## Cómo está hecho
| Archivo | Qué es |
|---|---|
| [`generar_datos.py`](generar_datos.py) | Genera los datos ficticios (12 meses, 293 ventas). En un proyecto real se reemplaza por la planilla o el sistema del cliente. |
| [`ventas_2025.csv`](ventas_2025.csv) | Los datos en formato planilla. |
| `datos.js` | Los mismos datos, listos para el tablero. |
| [`index.html`](index.html) | El dashboard: HTML, CSS y JavaScript **sin librerías**, liviano y rápido. |

Para actualizarlo con datos nuevos alcanza con volver a correr el script:
```bash
python generar_datos.py
```

## Variantes que ofrezco
- El mismo tablero en **Google Looker Studio** o **Google Sheets**, conectado a la planilla del cliente.
- Actualización **automática** diaria o semanal desde Excel, Google Sheets o un CSV exportado del sistema.
