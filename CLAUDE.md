# FlowData Solutions — instrucciones para Claude Code

## Capa 1: Skills de frontend y diseño (FDS)
Este repo define cinco skills en `.claude/skills/`:
1. **frontend-design**: estructura sólida, responsiva (Mobile-First), accesible (WCAG 2.1) y rápida (Core Web Vitals).
2. **top-design**: estética profesional Tier 1 estilo SaaS/B2B (Vercel, Linear, Stripe), dark mode, Inter / Plus Jakarta Sans.
3. **theme-factory**: tokens de diseño (fuente única de colores), temas FDS Dark (default) y FDS Light, acentos, y switcher claro/oscuro con persistencia.
4. **brand-guidelines**: nombre, logo, voz y tono, slogan "Automatización de Procesos & Soluciones de Datos", bordes de foco cian/azul e indicadores de estado de pipelines.
5. **find-skills** (de vercel-labs/skills, licencia MIT): buscar e instalar skills nuevas del ecosistema abierto (skills.sh, `npx skills`). Antes de instalar una skill, leer su contenido y pedir confirmación.

**Directiva de ejecución:** al crear o modificar cualquier código de interfaz (por ejemplo `index.html`, los reportes HTML del portafolio o componentes nuevos), aplicar **siempre** los criterios combinados de `frontend-design` y `top-design`, con los tokens de `theme-factory` y las reglas de `brand-guidelines`.

## Agentes del proyecto
En `.claude/agents/` hay cinco agentes: `redactor-propuestas`, `analista-datos`, `generador-reportes`, `control-calidad` y `contenido-linkedin` (detalle en `gestion/agentes.md`). Usalos cuando la tarea coincida. Los datos de clientes van solo en `clientes-privado/<cliente>/` (ignorado por git).

## Contexto del repo
- Web pública servida con GitHub Pages desde `main` (raíz): https://fl0wdatas0luti0nsdev.github.io/freelance-servicios-digitales/
- Repo público: no subir datos reales de clientes, contratos ni facturas.
- Textos en español rioplatense (voseo) para el público hispano. Fiverr también en español (el dueño no habla inglés): solo el título del gig va en inglés por el "I will" obligatorio, aclarando "in spanish".
- **Para retomar trabajo**, leer primero `gestion/estado-del-proyecto.md` (hecho y pendiente). Actualizarlo al cerrar una sesión con avances.

## Mapa del repo
No hay build, framework ni `package.json`: es un sitio estático + scripts de Python sueltos + documentos en Markdown.

| Ruta | Qué es |
|---|---|
| `index.html` | La web (un solo archivo: HTML + CSS + JS inline). Tokens `--fds-*` en `:root`, tema en `data-theme` y `localStorage['fds-theme']`. Secciones: hero, `#servicios`, `#planes`, `#portafolio`, `#proceso`, `#contacto`. |
| `servicios/` | Ficha de cada servicio (precios "desde"). Mantener en sintonía con `index.html` y `README.md`. |
| `portafolio/01..05/` | Ejemplos con datos ficticios, cada uno con su `README.md`. Las páginas HTML se publican en GitHub Pages. |
| `portafolio/capturas/` | Imágenes para Workana/Fiverr (`fiverr/`: galería del gig, video y PDF). |
| `referencias/caso-centro-medico/` | Caso completo de punta a punta con los agentes (datos → limpieza → reporte → control de calidad), con la facturación ficticia de un centro médico. Es la **implementación de referencia** de un entregable para cliente. `referencias/prueba-ferreteria/` solo guarda una redirección para links viejos. |
| `plantillas/` | Kit de propuestas, presupuesto, propuesta comercial, reporte de entrega. |
| `gestion/` | Estado del proyecto, planes, perfiles de plataformas (Workana, Fiverr, LinkedIn), competencia, seguimiento (`seguimiento-flowdata.xlsx`). |
| `marca/` | Logo e isotipo (SVG/PNG) y reglas de uso en `marca/README.md`. |
| `.claude/` | Skills, agentes y `settings.json` (permisos: `git`, `python3`, `node`, `pip install`, `npx skills`; force push denegado). |

### Cadena de datos del portafolio
- `01-limpieza-de-datos/limpiar.py` → `ventas_limpias.csv` → lo consume `02-reporte-automatico/generar_reporte.py`.
- `04-dashboard-interactivo/generar_datos.py` (semilla fija) → `ventas_2025.csv` + `datos.js` (`window.FDS_DATA`) → lo consume `05-dashboard-power-bi/preparar_datos.py` → `datos/*.csv` (modelo estrella).
- Si se cambian los datos de un paso, regenerar los siguientes. Los archivos generados (CSV, HTML, XLSX, `datos.js`) están versionados a propósito porque se publican.

## Comandos
Requisitos: Python 3 con `pandas` y `openpyxl`. En Windows el comando suele ser `python` (no `python3`). Correr cada script desde su carpeta.

```bash
# Portafolio
cd portafolio/01-limpieza-de-datos && python limpiar.py ventas_original.csv ventas_limpias.csv
cd portafolio/02-reporte-automatico && python generar_reporte.py ../01-limpieza-de-datos/ventas_limpias.csv
cd portafolio/04-dashboard-interactivo && python generar_datos.py
cd portafolio/05-dashboard-power-bi && python preparar_datos.py

# Caso de referencia (centro médico)
cd referencias/caso-centro-medico && python generar_datos.py && python limpiar.py
cd referencias/caso-centro-medico/reporte && python generar_reporte.py            # --salida DIR, --sin-recalcular
node verificar_reporte.js reporte_facturacion_2026-10.html                            # requiere Playwright
```
- `generar_reporte.py` del caso de referencia recalcula el Excel con **LibreOffice** (busca `soffice` en el PATH, la variable `SOFFICE` o rutas habituales); sin LibreOffice igual genera el reporte.
- `verificar_reporte.js` (Playwright) prueba 375/1280 px × oscuro/claro: errores de consola, scroll horizontal, pedidos externos, foco y signo menos, y guarda capturas. No hay tests automáticos aparte de este.

## Convenciones de código y entregables
- Scripts de Python: docstring al inicio con uso y qué corrige/genera, catálogos de valores "oficiales" arriba, `main()` con argumentos posicionales opcionales y valores por defecto. Nunca modificar el archivo original del cliente; generar un `informe_limpieza.md` con cada cambio.
- Reportes para clientes: seguir las "Lecciones aprendidas" de `.claude/agents/generador-reportes.md` (ningún texto dependiente de datos escrito a mano, bloque CONFIG al inicio, signo menos `−` U+2212, foco azul `#0066FF` en modo claro, sin Google Fonts ni pedidos externos en reportes confidenciales). La web pública sí usa Google Fonts.
- Formato argentino: montos `$ 1.234.567` (punto de miles), meses y días en español.
- **Regla de links:** propuestas y perfiles de Workana, Fiverr y Upwork no llevan links, mails, teléfonos ni invitaciones a contactar por fuera (detalle en `.claude/agents/redactor-propuestas.md`).
- Nunca inventar clientes, resultados ni testimonios; los ejemplos se presentan como "con datos ficticios".

## Forma de trabajo de Claude en este proyecto
El dueño del proyecto quiere que Claude avance con autonomía. Estas reglas describen cómo trabajar; no otorgan permisos (los permisos los define el dueño en el modo de la sesión y en `.claude/settings.json`).

**Lo hace solo, sin preguntar:**
- Editar la web, el portafolio, los textos de servicios, perfiles y plantillas.
- Correr los scripts del portafolio y verificar que funcionen.
- Hacer commits con mensajes claros en español y subir los cambios a `main`.
- Revisar cómo se ve la web en celular y escritorio después de cada cambio de interfaz.

**Pregunta antes de:**
- Borrar archivos o carpetas, o reescribir el historial de git (force push).
- Cambiar la visibilidad del repo o la configuración de GitHub Pages.
- Instalar skills, plugins o dependencias nuevas (leyendo antes su contenido).
- Gastar dinero o contratar servicios.
- Publicar o enviar algo fuera del repo en nombre de FlowData Solutions (redes, plataformas, emails).
- Subir cualquier dato real de clientes.

**Al terminar cada tarea:** resumir qué se hizo, qué se verificó y qué quedó pendiente.
