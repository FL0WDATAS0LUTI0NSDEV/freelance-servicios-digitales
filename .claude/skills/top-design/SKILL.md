---
name: top-design
description: Diseño UI/UX de calidad de producción (Tier 1), con estética SaaS/B2B moderna estilo Vercel, Linear o Stripe y la identidad visual de FlowData Solutions (dark mode, paleta azul/cyan, Inter / Plus Jakarta Sans). Usar al diseñar o retocar páginas, dashboards, tablas de datos, tarjetas de KPIs, reportes y piezas visuales de la marca.
---

# top-design — Capa 1 (FDS)

## Enfoque UI/UX
- Calidad de producción (Tier 1): nada que parezca plantilla genérica.
- Referencias estéticas: Vercel, Linear, Stripe. Mucho espacio en blanco, jerarquía tipográfica clara, pocos colores bien usados.

## Identidad visual de marca

### Paleta
| Token | Color | Uso |
|---|---|---|
| `--fds-navy` | `#0B1325` | Fondo principal (dark mode) |
| `--fds-cyan` | `#00E5FF` | Acento de datos: gráficos, indicadores, highlights |
| `--fds-blue` | `#0066FF` | Acción principal: botones, links, foco |
| `--fds-neutral` | `#F4F6F8` | Texto principal sobre oscuro / fondo en modo claro |

Derivados sugeridos (mantener coherencia):
```css
:root {
  --fds-navy: #0B1325;
  --fds-navy-2: #111C33;            /* superficies / tarjetas */
  --fds-border: rgba(244,246,248,.08);
  --fds-text: #F4F6F8;
  --fds-muted: rgba(244,246,248,.64);
  --fds-cyan: #00E5FF;
  --fds-blue: #0066FF;
  --fds-glass: rgba(17,28,51,.6);
}
```
- Verificar siempre contraste WCAG: el cyan y el azul eléctrico sobre `#0B1325` sirven para acentos y texto grande; para texto chico sobre azul usar blanco.

### Estilo
- **Dark mode elegante** por defecto; si se ofrece modo claro, usar `#F4F6F8` de fondo y `#0B1325` de texto.
- **Bordes sutiles** de 1 px (`--fds-border`) con **micro-degradados** (ej. `linear-gradient(180deg, rgba(255,255,255,.06), transparent)`).
- **Glassmorphism limpio:** `background: var(--fds-glass); backdrop-filter: blur(12px);` solo en superficies flotantes (navbar, modales), nunca en todo.
- **Tipografía:** Inter o Plus Jakarta Sans (Google Fonts, `display=swap`). Pesos 400/500/600/700. Números de datos con `font-variant-numeric: tabular-nums`.
- Radios de 10–14 px, sombras suaves y difusas, glow cyan muy sutil solo para destacar.

## Componentes clave
- **Dashboards interactivos:** grilla de KPIs arriba, gráficos al medio, tabla de detalle abajo.
- **Tablas de datos con filtros:** encabezado fijo, filas con hover, orden por columna, búsqueda y filtros visibles, números alineados a la derecha.
- **Tarjetas de KPIs:** etiqueta chica en `--fds-muted`, valor grande, variación con flecha y color (verde sube / rojo baja), mini sparkline opcional.
- **Estados de carga (skeletons):** bloques con shimmer suave del mismo tamaño que el contenido final (evita CLS).
- **Micro-interacciones pulidas:** transiciones de 150–250 ms en hover/focus, `transform` y `opacity` (no `width`/`height`), desactivadas con `prefers-reduced-motion`.

## Checklist antes de entregar
- [ ] Usa la paleta y tipografías de marca.
- [ ] Se ve bien en 375 px y en 1280 px.
- [ ] Contraste y foco accesibles.
- [ ] Estados vacíos, de carga y de error contemplados.
- [ ] Nada genérico: jerarquía clara, espaciado consistente, detalles cuidados.

## Combinación obligatoria
Aplicar siempre junto con **frontend-design** (estructura sólida, accesible y rápida). Ver `.claude/skills/frontend-design/SKILL.md`.
