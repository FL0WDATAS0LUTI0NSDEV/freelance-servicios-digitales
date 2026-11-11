# LinkedIn — Calendario de publicaciones automáticas

> Página de empresa de FlowData Solutions. Estrategia y textos base en `perfil-linkedin.md`.
> Las publicaciones se programan con **Metricool** (red `linkedin`) para que salgan solas.

## Cómo funciona la automatización
1. **Metricool** publica en la página a la hora programada (`autoPublish: true`).
2. Los textos y las imágenes salen de este archivo; las imágenes se toman de la web publicada en GitHub Pages (URL pública), así Metricool las puede descargar.
3. Claude programa la tanda con el conector de Metricool; antes de programar, el dueño aprueba los textos.
4. **Tarea programada `linkedin-tanda-semanal`** (app de Claude, jueves 10:00): redacta los posts de la semana siguiente, los agrega a este archivo y hace commit. **No usa Metricool**: la prueba gratis termina alrededor del 25/11/2026, así que desde diciembre se programan a mano en LinkedIn (página → Crear publicación → ícono de reloj). Si la semana ya tiene 2 posts o más, no agrega nada. Corre solo con la app abierta.

### Requisito pendiente
- [x] Crear la página de empresa en LinkedIn (guía en `perfil-linkedin.md`). Creada y con la primera publicación (lanzamiento) hecha a mano, 10/11/2026.
- [x] Metricool: cuenta propia de FlowData (`flowdata.solutions.dev`), marca `8020974`, LinkedIn conectado a la página (10/11/2026). Ojo: la API muestra `urn:li:person` aunque publica en la página.

## Horarios
Martes y jueves 9:00 (hora de Argentina), encuesta opcional el sábado 10:00. Cuando la página tenga historial, ajustar con "mejor momento para publicar" de Metricool.

URL base de imágenes: `https://fl0wdatas0luti0nsdev.github.io/freelance-servicios-digitales/portafolio/capturas/`

---

## Tanda 1 (10 al 23 de noviembre de 2026)

> Fechas adelantadas para que todo salga antes de que termine la prueba de Metricool (~25/11). Fechas finales en el registro.

### 1 · Jueves 12/11 · Lanzamiento
Imagen: `marca/linkedin-portada-1128x191.png` (o sin imagen, se muestra la vista previa de la web).

```
🚀 Nace FlowData Solutions.

Muchas PYMEs pierden horas cada mes armando reportes a mano, corrigiendo planillas o buscando números que deberían estar a un clic.

Para eso estamos:
📊 Dashboards en Power BI con los indicadores que importan.
🧹 Planillas y bases de datos ordenadas y confiables.
⚙️ Reportes que se generan solos.
💻 Herramientas web a medida.

Armamos un portafolio con ejemplos (datos ficticios), como un dashboard de ventas con filtros y una planilla con 58 formas distintas de escribir los mismos datos, convertida en una base confiable:
👉 https://fl0wdatas0luti0nsdev.github.io/freelance-servicios-digitales/

Si conocés una empresa a la que le sirva, compartí esta publicación. ¡Gracias! 🙌

#PowerBI #AnálisisDeDatos #Automatización #PYMEs
```

### 2 · Martes 17/11 · Antes y después (limpieza)
Imagen: `3-limpieza-de-datos.png`

```
"Bar El Faro", "BAR EL FARO" y "  bar el faro ".

Para vos es el mismo cliente. Para Excel son tres.

En un ejemplo con datos ficticios armamos la planilla típica de una distribuidora después de tres meses de carga a mano:
• Fechas en 4 formatos distintos.
• 58 formas distintas de escribir clientes, productos, vendedores y provincias.
• Montos como "$65.100,00", "30000,00" y "15500".
• 6 filas duplicadas.

Resultado: nadie podía decir cuánto le vendió a cada cliente.

Un script en Python lo ordena en un segundo: unifica nombres, convierte montos, completa faltantes y deja un informe con cada cambio. De 77 filas desordenadas a 70 filas confiables.

¿Cuántas versiones del mismo cliente hay en tu planilla? 👀

#Excel #LimpiezaDeDatos #Python #PYMEs
```

### 3 · Jueves 19/11 · Caso del portafolio (dashboard)
Imagen: `1-dashboard-interactivo.png`

```
¿Qué mes vendimos más? ¿Qué cliente pesa más en Córdoba?

Si para responder eso tenés que armar una tabla dinámica cada vez, el problema no es la pregunta: es la herramienta.

Armamos un dashboard de ventas de ejemplo (datos ficticios, 12 meses) que se abre en cualquier navegador o celular, sin instalar nada:
📅 Filtros por período, provincia, vendedor, producto y cliente.
📈 Ventas, pedidos y ticket promedio, comparados con el período anterior.
🖱️ Clic en un mes o en un cliente para filtrar todo el tablero.
⬇️ Exportar a CSV lo que estás viendo.

Probalo acá 👉 https://fl0wdatas0luti0nsdev.github.io/freelance-servicios-digitales/portafolio/04-dashboard-interactivo/

¿Qué indicador te gustaría ver primero cuando abrís el tablero?

#Dashboards #BusinessIntelligence #AnálisisDeDatos #PYMEs
```

### 4 · Sábado 21/11 · Encuesta
Tipo: encuesta, duración 7 días.

```
Pregunta rápida para dueños y equipos de PYMEs 👇

¿Cuántas horas por mes le dedican a armar reportes a mano?

#PYMEs #Productividad #Excel
```
Pregunta de la encuesta: `¿Cuántas horas por mes van a reportes manuales?`
Opciones: `Menos de 2` · `Entre 2 y 8` · `Más de 8` · `Ni idea 😅`

### 5 · Martes 24/11 · Tip de Power BI
Sin imagen (o una captura de la medida en Power BI cuando esté el ejemplo 05).

```
Una medida de Power BI que toda PYME debería tener: ventas contra el mismo período del año anterior.

Ventas AA =
CALCULATE ( [Ventas], SAMEPERIODLASTYEAR ( dCalendario[Fecha] ) )

Var % =
DIVIDE ( [Ventas] - [Ventas AA], [Ventas AA] )

3 cosas para que funcione bien:
1️⃣ Una tabla calendario marcada como "tabla de fechas".
2️⃣ La relación entre el calendario y la tabla de ventas.
3️⃣ DIVIDE en vez de "/", así no aparece un error cuando el año anterior está vacío.

Con eso, cualquier gráfico muestra cuánto creciste (o no) sin tocar una fórmula más.

¿Ya la usás en tus tableros?

#PowerBI #DAX #BusinessIntelligence
```

### 6 · Jueves 26/11 · Mini guía
Imagen: `2-caso-completo-reporte.png`

```
3 indicadores que toda PYME debería mirar cada mes (y casi nadie mira):

1️⃣ Ticket promedio. Si las ventas suben pero el ticket baja, estás vendiendo más barato o a clientes más chicos.

2️⃣ Concentración de clientes. Si 3 clientes son la mitad de la facturación, un solo atraso te complica el mes.

3️⃣ Avance contra el objetivo. No alcanza con saber cuánto vendiste: importa si vas en camino a la meta a mitad de mes, cuando todavía podés hacer algo.

Los tres salen de la misma planilla de ventas que ya tenés. El problema suele ser que está desordenada o que armarlos lleva horas.

Eso es lo que automatizamos: un reporte que se genera solo, con estos números a la vista.

¿Cuál de los tres mirás hoy?

#AnálisisDeDatos #PYMEs #GestiónEmpresarial #Reportes
```

---

## Registro
| # | Fecha | Estado en Metricool | Notas |
|---|---|---|---|
| 1 | 10/11 | Publicada a mano | Lanzamiento, adelantada |
| 2 | 12/11 9:00 | Programada | Adelantada |
| 3 | 17/11 9:00 | Programada | Adelantada |
| 4 | 21/11 10:00 | Programada | Encuesta 7 días |
| 5 | 19/11 9:00 | Programada | Adelantada |
| 6 | 23/11 9:00 | Programada | Adelantada |
