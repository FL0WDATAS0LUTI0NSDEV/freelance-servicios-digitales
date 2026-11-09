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
