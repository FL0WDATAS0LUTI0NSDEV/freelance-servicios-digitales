# Ejemplo 5 — Dashboard de ventas en Power BI

> Datos ficticios. Este ejemplo lo arma **[tu nombre]** en Power BI Desktop siguiendo esta guía (1–2 horas). Todo lo demás —datos, modelo, medidas DAX, tema de colores y diseño de páginas— ya está listo.

**Qué demuestra a un cliente:** modelo estrella, Power Query, medidas DAX (comparación de períodos, acumulado anual, cumplimiento de objetivos, rankings), formato condicional y un diseño profesional con la identidad de FlowData Solutions.

---

## Archivos

| Archivo | Qué es |
|---|---|
| `datos/Ventas.csv` | Hechos: 293 ventas de 2025 |
| `datos/Clientes.csv` | 8 clientes, con tipo y provincia |
| `datos/Productos.csv` | 6 productos, con categoría y precio de lista |
| `datos/Vendedores.csv` | 3 vendedores, con zona |
| `datos/Calendario.csv` | 365 días, con meses y días en español |
| `datos/Objetivos.csv` | Objetivo mensual de ventas por vendedor |
| `tema-fds-dark.json` / `tema-fds-light.json` | Temas de Power BI con los colores FDS |
| `preparar_datos.py` | Script que genera los CSV (por si querés regenerarlos) |

---

## Paso 1 — Importar los datos (10 min)
1. Abrí **Power BI Desktop** → **Obtener datos → Texto/CSV** → importá los 6 archivos de `datos/`.
2. En cada uno, tocá **Transformar datos** y revisá los tipos en Power Query:
   - `Fecha` → **Fecha** (en Ventas, Calendario y Objetivos).
   - `Cantidad`, `Monto`, `Objetivo`, `PrecioLista` → **Número entero**.
   - IDs y textos → **Texto**.
   - Si Power BI lee mal las fechas, usá **Cambiar tipo → Usando configuración regional → Inglés (Estados Unidos)**: los CSV usan formato `aaaa-mm-dd`.
3. **Cerrar y aplicar.**

## Paso 2 — Modelo estrella (10 min)
En la vista **Modelo**, creá estas relaciones (todas *varios a uno*, filtro en una dirección):

| Desde (varios) | Hacia (uno) |
|---|---|
| `Ventas[Fecha]` | `Calendario[Fecha]` |
| `Ventas[ClienteID]` | `Clientes[ClienteID]` |
| `Ventas[ProductoID]` | `Productos[ProductoID]` |
| `Ventas[VendedorID]` | `Vendedores[VendedorID]` |
| `Objetivos[Fecha]` | `Calendario[Fecha]` |
| `Objetivos[VendedorID]` | `Vendedores[VendedorID]` |

Después:
- `Calendario` → clic derecho → **Marcar como tabla de fechas** → columna `Fecha`.
- `Calendario[Mes]` → **Ordenar por columna** → `MesNum`. Lo mismo `MesAnio` → `MesNum` y `DiaSemana` → `DiaSemanaNum`.
- Ocultá las columnas de ID en la vista de informe (clic derecho → *Ocultar*).

> Los objetivos están por vendedor y mes: se filtran por fecha y vendedor, pero **no** por cliente ni producto (es lo correcto para este caso).

## Paso 3 — Medidas DAX (15 min)
Creá una tabla vacía para ordenar las medidas: **Inicio → Especificar datos** → nombre `_Medidas` → Cargar. Después, con esa tabla seleccionada, **Nueva medida** para cada una:

```dax
Ventas = SUM ( Ventas[Monto] )
```
```dax
Pedidos = COUNTROWS ( Ventas )
```
```dax
Unidades = SUM ( Ventas[Cantidad] )
```
```dax
Ticket Promedio = DIVIDE ( [Ventas], [Pedidos] )
```
```dax
Clientes Activos = DISTINCTCOUNT ( Ventas[ClienteID] )
```
```dax
Ventas Mes Anterior = CALCULATE ( [Ventas], DATEADD ( Calendario[Fecha], -1, MONTH ) )
```
```dax
Var % vs Mes Anterior = DIVIDE ( [Ventas] - [Ventas Mes Anterior], [Ventas Mes Anterior] )
```
```dax
Ventas Acumuladas Año = TOTALYTD ( [Ventas], Calendario[Fecha] )
```
```dax
Objetivo = SUM ( Objetivos[Objetivo] )
```
```dax
Cumplimiento % = DIVIDE ( [Ventas], [Objetivo] )
```
```dax
Brecha vs Objetivo = [Ventas] - [Objetivo]
```
```dax
Participación % = DIVIDE ( [Ventas], CALCULATE ( [Ventas], ALLSELECTED () ) )
```
```dax
Ranking Cliente = RANKX ( ALLSELECTED ( Clientes[Cliente] ), [Ventas] )
```
```dax
Color Cumplimiento =
SWITCH (
    TRUE (),
    ISBLANK ( [Cumplimiento %] ), BLANK (),
    [Cumplimiento %] >= 1, "#10B981",
    [Cumplimiento %] >= 0.9, "#F59E0B",
    "#EF4444"
)
```
```dax
Título Período =
"Ventas " & IF (
    HASONEVALUE ( Calendario[MesAnio] ),
    VALUES ( Calendario[MesAnio] ),
    "2025"
)
```

**Formato:** `Ventas`, `Ticket Promedio`, `Objetivo`, `Brecha vs Objetivo` y `Ventas Acumuladas Año` → *Moneda*, sin decimales. Las que terminan en `%` → *Porcentaje*, 1 decimal.

### Controles para verificar que todo está bien
Sin filtros, en tarjetas, tenés que ver:

| Medida | Valor esperado |
|---|---|
| Ventas | $ 14.626.998 |
| Pedidos | 293 |
| Unidades | 3.943 |
| Ticket Promedio | $ 49.921 |
| Objetivo | $ 14.820.000 |
| Cumplimiento % | 98,7 % |
| Var % vs Mes Anterior, filtrando **dic 2025** | −11,7 % |

Si algún número no coincide, revisá los tipos de dato (Paso 1) y las relaciones (Paso 2).

## Paso 4 — Tema de colores (2 min)
**Vista → Temas → Buscar temas** → elegí `tema-fds-dark.json` (o `tema-fds-light.json`).
Si Power BI muestra un error al importarlo, avisame y lo simplifico.

Tamaño de página: **Vista → Ajustar página → 16:9 (1280 × 720)**.

## Paso 5 — Páginas del reporte (45–60 min)

### Página 1 · Resumen ejecutivo
```
┌──────────────────────────────────────────────────────────────────────┐
│ FlowData · Ventas 2025            [Segmentador Mes] [Provincia] [Vend.]│
├──────────┬──────────┬──────────┬──────────┬──────────────────────────┤
│ Ventas   │ Pedidos  │ Ticket   │ Cumplim. │                          │
│ + Var %  │          │ promedio │ objetivo │                          │
├──────────┴──────────┴──────────┴──────────┤  Ventas por provincia    │
│ Ventas vs Objetivo por mes                 │  (barras horizontales)   │
│ (columnas = Ventas, línea = Objetivo)      │                          │
│                                            ├──────────────────────────┤
│                                            │  Ventas por categoría    │
│                                            │  (anillo)                │
└────────────────────────────────────────────┴──────────────────────────┘
```
- **Tarjetas (4):** `Ventas`, `Pedidos`, `Ticket Promedio`, `Cumplimiento %`. Debajo de Ventas, una tarjeta chica con `Var % vs Mes Anterior`.
- **Gráfico de columnas y líneas:** eje `Calendario[Mes]`, columnas `Ventas`, línea `Objetivo`.
- **Barras horizontales:** `Clientes[Provincia]` × `Ventas`.
- **Anillo:** `Productos[Categoria]` × `Ventas`.
- **Segmentadores:** `Calendario[Mes]` (estilo mosaico), `Clientes[Provincia]`, `Vendedores[Vendedor]` (desplegables).

### Página 2 · Clientes y productos
- **Tabla/matriz:** `Clientes[Cliente]`, `Clientes[TipoCliente]`, `Ventas`, `Pedidos`, `Ticket Promedio`, `Participación %`, `Ranking Cliente`. Barras de datos en `Ventas` (formato condicional).
- **Treemap:** `Productos[Categoria]` → `Productos[Producto]` × `Ventas`.
- **Dispersión:** eje X `Pedidos`, eje Y `Ticket Promedio`, tamaño `Ventas`, leyenda `Clientes[TipoCliente]`, detalles `Clientes[Cliente]`. Sirve para mostrar qué clientes compran seguido y cuáles compran grande.
- **Líneas:** `Ventas Acumuladas Año` por `Calendario[Mes]`.

### Página 3 · Vendedores y objetivos
- **Tarjetas por vendedor** (o una matriz): `Vendedor`, `Ventas`, `Objetivo`, `Cumplimiento %`, `Brecha vs Objetivo`.
- **Formato condicional** en `Cumplimiento %` → *Color de fondo* → *Valor del campo* → medida `Color Cumplimiento` (verde ≥ 100 %, ámbar ≥ 90 %, rojo < 90 %).
- **Columnas agrupadas:** `Calendario[Mes]` × `Ventas` por `Vendedores[Vendedor]`.
- **Medidor:** `Cumplimiento %` con valor máximo 1,2 y destino 1.

### Detalles de diseño (identidad FDS)
- Títulos de visual cortos, en mayúscula inicial, sin punto final.
- Máximo 6–7 visuales por página; dejá aire entre ellos (márgenes de 16 px).
- Un **cuadro de texto** arriba a la izquierda: "FlowData · Ventas 2025" y, abajo a la derecha, "Datos ficticios".
- Usá el **cian** solo para lo más importante (ventas); el resto en azul y grises.

## Paso 6 — Mostrarlo en el portafolio (15 min)
Publicar en la web desde Power BI requiere una cuenta de trabajo o estudio y que la organización lo permita. **No uses la cuenta de tu empleador** para proyectos de FlowData Solutions. En su lugar:

1. **Capturas:** exportá cada página como imagen (*Archivo → Exportar → PDF* y recortá, o captura de pantalla a 1280 × 720) y guardalas en `capturas/` como `pagina-1.png`, `pagina-2.png`, `pagina-3.png`.
2. **PDF:** *Archivo → Exportar → Exportar a PDF* → guardalo como `dashboard-ventas.pdf`.
3. **Video corto (60–90 s):** grabá la pantalla usando los segmentadores y filtrando (con la Barra de juegos de Windows: `Win + G`). Subilo a YouTube como *no listado* o a LinkedIn.
4. **El archivo `.pbix`:** guardalo como `dashboard-ventas.pbix` en esta carpeta; así un cliente técnico puede abrirlo.
5. Subí todo al repo y avisame: actualizo este README con las capturas y sumo el ejemplo a la web.

---

## Ideas para ampliarlo (más adelante)
- **Pronóstico** de ventas con la función de previsión del gráfico de líneas, o con Python (semana 4 del plan de repaso).
- **Seguridad a nivel de fila (RLS):** que cada vendedor vea solo sus ventas.
- **Página de detalle con *drill-through*** desde un cliente.
- **Actualización automática** desde una carpeta de SharePoint o Google Drive.
