---
name: frontend-design
description: Construcción de interfaces web responsivas, limpias, accesibles (WCAG 2.1) y rápidas (Core Web Vitals) con HTML5, CSS moderno, JavaScript ES6+ y, según el caso, React / Next.js / Tailwind CSS. Usar al crear o modificar cualquier código de interfaz (páginas, componentes, estilos, reportes HTML) de FlowData Solutions.
---

# frontend-design — Capa 1 (FDS)

## Stack principal
- HTML5 semántico (`header`, `main`, `section`, `nav`, `footer`, `button` en vez de `div` clickeables).
- CSS3 moderno: Flexbox, Grid y variables CSS (`:root { --color-... }`).
- JavaScript ES6+ (módulos, `const`/`let`, funciones flecha, `async/await`).
- React / Next.js / Tailwind CSS **solo cuando el proyecto lo requiera**. Para páginas estáticas simples (como la web de GitHub Pages de este repo) usar HTML + CSS + JS sin build.

## Enfoque
- **Mobile-First:** escribir primero los estilos para celular y agregar `@media (min-width: ...)` para pantallas más grandes.
- **Responsivo:** sin scroll horizontal; márgenes laterales mínimos de 16 px en celular.
- **Accesible (WCAG 2.1 AA):**
  - Contraste mínimo 4.5:1 en texto normal y 3:1 en texto grande.
  - Todo elemento interactivo usable con teclado y con `:focus-visible` visible.
  - `alt` en imágenes, `aria-label` en botones solo-ícono, `lang` en `<html>`.
  - Respetar `prefers-reduced-motion`.
- **Rendimiento (Core Web Vitals):**
  - LCP: imágenes con `width`/`height`, `loading="lazy"` fuera de la primera pantalla, fuentes con `display=swap`.
  - CLS: reservar espacio para imágenes y componentes que cargan después.
  - INP: JavaScript mínimo, sin librerías pesadas si no hacen falta.

## Directrices de código
- Componentes **modulares, limpios y reutilizables**: una responsabilidad por componente, sin estilos duplicados.
- Arquitectura de carpetas clara cuando el proyecto crece:
  ```
  /components   # piezas reutilizables (Card, KpiCard, DataTable...)
  /styles       # variables, base y utilidades
  /assets       # imágenes, íconos, fuentes
  ```
- Nombres de clases y variables descriptivos y consistentes.
- Sin código muerto ni comentarios obvios; comentar solo el *por qué*.
- Probar cada cambio en ancho de celular (375 px) y escritorio (1280 px) antes de darlo por terminado.

## Combinación obligatoria
Al crear o modificar interfaz, aplicar siempre **frontend-design** (estructura) junto con **top-design** (estética). Ver `.claude/skills/top-design/SKILL.md`.
