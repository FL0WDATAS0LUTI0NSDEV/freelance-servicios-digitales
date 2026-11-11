# Oportunidades para ofrecer los servicios

> Relevamiento del 10 de noviembre de 2026. Priorizado según lo que ya está armado (Workana, Fiverr, LinkedIn, portafolio) y la meta de USD 1.500 netos/mes.

## Prioridad 1 — Lo que ya está andando (esta semana)

| Canal | Qué hacer | Por qué |
|---|---|---|
| **Workana** | Apenas aprueben el perfil: 5 propuestas por día con `redactor-propuestas`. Buscar con filtros "Power BI", "Excel", "Python", "automatización", "dashboard". Postularse primero a proyectos chicos (USD 50–250) para juntar reseñas. | Es la plataforma principal para freelancers en español en Latinoamérica. Hay demanda real de dashboards de ventas y analistas con Excel + Power BI + Python, incluso clientes de Brasil. |
| **Fiverr** | Con los 2 gigs activos (Power BI y facturas PDF a Excel): verificación de identidad, responder en menos de 1 h y revisar **Briefs** todos los días. Medir el 30/11. | Responder rápido y estar verificado mejora la posición en búsquedas; los Briefs son pedidos abiertos de compradores. |
| **LinkedIn (página de empresa)** | Seguir con los posts programados y además usar el perfil personal: comentar en publicaciones de dueños de PyMEs y contadores, y mandar 5 pedidos de conexión por día a ese público. | La página sola crece despacio; el alcance viene del perfil personal. |

## Prioridad 2 — Clientes directos (próximas 2–4 semanas)

1. **Estudios contables como socios.** Cada estudio atiende decenas de PyMEs con planillas desordenadas. Es el público ideal del servicio de **facturas PDF a Libro IVA en Excel** (ejemplo 6 del portafolio). Ofrecerles: carga de facturas para cierres, reportes mensuales automáticos para sus clientes, o comisión por referido. Empezar por el contador propio (de paso, la consulta por monotributo).
2. **Red cercana:** la lista de "10 conocidos / PyMEs cercanas" del plan de lanzamiento sigue pendiente. Llevar el caso de la ferretería como ejemplo (es justo el tipo de comercio al que apunta).
3. **Comercios con stock y ventas en Excel:** ferreterías, distribuidoras, corralones, ópticas, farmacias. Propuesta concreta: "te dejo un reporte mensual de ventas y stock que se arma solo".
4. **Comunidades:** grupos de Power BI y Excel en español (LinkedIn, Facebook, Telegram), respondiendo dudas con ayuda real, sin vender de entrada.

## Prioridad 3 — Mediano plazo

| Oportunidad | Estado | Nota |
|---|---|---|
| **Upwork** | Pendiente desde el plan de lanzamiento | Comisión de 0% a 15% según el caso y cargo por cada propuesta (connects). Más competencia y en inglés; esperar a tener reseñas en Workana/Fiverr. |
| **Malt** | Para evaluar | Fuerte en España y Europa, en español. La comisión baja si se trabaja mucho tiempo con el mismo cliente. |
| **Freelancer.com** | Para evaluar | Tiene proyectos de Power BI y Power Automate, pero con ofertas muy bajas. Prioridad baja. |
| **Programa KIT 4.0 (Argentina)** | **No aplica todavía** | El Estado cubre hasta 50% del kit, acreditado al proveedor. Para inscribirse como proveedor piden CUIT con actividades de Economía del Conocimiento, certificado MiPyME vigente y, según varias fuentes, unos 6 meses de actividad. No hay un kit específico de análisis de datos (el más cercano es BAS-02, monitoreo de producción para fábricas). Consultar con el contador si un monotributista puede inscribirse. |
| **Toptal** | Descartado por ahora | Admite a muy pocos postulantes y pide inglés fluido. |

## Qué ajustar en la oferta
- Los clientes de Workana piden **Excel + Power BI + Python juntos**: ya está en el perfil; reforzarlo en el título y en las propuestas.
- Terminar el **ejemplo de Power BI** (`portafolio/05-dashboard-power-bi/`): es lo que más aparece en los pedidos.
- Armar una **oferta cerrada para contadores** (por ejemplo, "facturas del mes a Libro IVA + reporte mensual para tus clientes PyME") con precio fijo por cliente.

## Oferta para estudios contables: notas internas
La oferta está en `servicios/oferta-estudios-contables.md` (planes de USD 60, 120 y 220 por mes, con piloto sin cargo).

**Por qué conviene:** es un ingreso que se repite todos los meses; 4 estudios en el plan Estudio son USD 480/mes, casi un tercio de la meta. Una vez configurados los formatos, cada mes lleva menos trabajo, y cada estudio conoce decenas de PyMEs que pueden necesitar reportes o Power BI.

**Antes del primer contacto:**
- [ ] Confirmar con el contador cómo facturar (monotributo) y si cobrar en USD o en pesos.
- [ ] Tener a mano un acuerdo de confidencialidad simple.
- [ ] Ampliar `extraer_facturas.py`: Libro IVA Ventas, notas de crédito, alícuotas del 27 % y 2,5 %, percepciones de IVA y conceptos exentos o no gravados (hoy solo Compras, 21 % y 10,5 %, percepciones de IIBB).
- [ ] Sumar el ejemplo 6 a la sección `#portafolio` de la web (hoy el mail apunta a la carpeta en GitHub).
- [ ] Armar la lista de 20 estudios para contactar (LinkedIn, "estudio contable" + ciudad).

## Fuentes
- Workana: [analista de datos con Excel, Power BI y Python](https://www.workana.com/job/analista-de-datos-con-expertise-en-excel-power-bi-y-python), [plantillas de Power BI para tienda online](https://www.workana.com/job/desarrollo-de-plantillas-de-power-bi-reutilizables-para-tienda-online-de-business-intelligence), [dashboards de ventas (Brasil)](https://www.workana.com/job/desenvolvimento-de-dashboards-em-power-bi-para-analise-de-vendas-clientes-e-fornecedores). Sin fecha visible: confirmar que sigan abiertos.
- Plataformas: [Xolo — plataformas en español 2026](https://blog.xolo.io/es/7-mejores-plataformas-para-trabajos-freelance-espanol-2026), [Upwork vs Toptal](https://www.upwork.com/en-gb/resources/upwork-vs-toptal), [Freelancer.com — Power BI](https://www.freelancer.com.co/jobs/power-bi/), [comparativa de plataformas para empresas](https://hackceleration.com/es/labs/mejor/plataformas-freelancers-empresas).
- KIT 4.0: [proveedores de la Economía del Conocimiento](https://www.argentina.gob.ar/economia/industria-y-economia-del-conocimiento/kit-40/proveedores-de-la-economia-del-conocimiento), [formulario de inscripción de proveedores](https://www.argentina.gob.ar/formularios/solicitud-de-inscripcion-al-listado-de-proveedores-kit-40), [acceder al Kit 4.0](https://www.argentina.gob.ar/servicio/acceder-al-kit-40), [acceso para todas las MiPyMEs](https://siap.blogdelcontador.com.ar/?p=88880).
