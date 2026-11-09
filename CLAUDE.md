# FlowData Solutions — instrucciones para Claude Code

## Capa 1: Skills de frontend y diseño (FDS)
Este repo define cinco skills en `.claude/skills/`:
1. **frontend-design**: estructura sólida, responsiva (Mobile-First), accesible (WCAG 2.1) y rápida (Core Web Vitals).
2. **top-design**: estética profesional Tier 1 estilo SaaS/B2B (Vercel, Linear, Stripe), dark mode, Inter / Plus Jakarta Sans.
3. **theme-factory**: tokens de diseño (fuente única de colores), temas FDS Dark (default) y FDS Light, acentos, y switcher claro/oscuro con persistencia.
4. **brand-guidelines**: nombre, logo, voz y tono, slogan "Automatización de Procesos & Soluciones de Datos", bordes de foco cian/azul e indicadores de estado de pipelines.
5. **find-skills** (de vercel-labs/skills, licencia MIT): buscar e instalar skills nuevas del ecosistema abierto (skills.sh, `npx skills`). Antes de instalar una skill, leer su contenido y pedir confirmación.

**Directiva de ejecución:** al crear o modificar cualquier código de interfaz (por ejemplo `index.html`, los reportes HTML del portafolio o componentes nuevos), aplicar **siempre** los criterios combinados de `frontend-design` y `top-design`, con los tokens de `theme-factory` y las reglas de `brand-guidelines`.

## Contexto del repo
- Web pública servida con GitHub Pages desde `main` (raíz): https://fl0wdatas0luti0nsdev.github.io/freelance-servicios-digitales/
- Repo público: no subir datos reales de clientes, contratos ni facturas.
- Textos en español rioplatense (voseo) para el público hispano; Fiverr en inglés.

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
