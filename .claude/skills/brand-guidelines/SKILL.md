---
name: brand-guidelines
description: Guía de marca de FlowData Solutions (FDS): nombre, logotipo e isotipo, voz y tono, slogan e identidad gráfica en código (bordes de foco cian/azul e indicadores de estado de pipelines de datos). Usar al escribir textos de marca, diseñar logos o piezas, y al construir interfaces que muestren estados de procesos.
---

# brand-guidelines — Capa 1 (FDS)

## Nombre de marca
- Nombre completo: **FlowData Solutions**. Abreviatura: **FDS**.
- Escribir siempre "FlowData" junto, con F y D mayúsculas. Nunca "Flow Data", "Flowdata" ni "FLOWDATA" en texto corrido.

## Logotipo e isotipo
- **Isotipo:** emblema técnico con las letras **FDS** integrando **líneas de circuito / vectores de flujo de datos** (trazos que conectan nodos, como un pipeline).
- **Logotipo:** isotipo + "FlowData Solutions" en Inter o Plus Jakarta Sans, peso 600–700.
- **Colores:** isotipo en Cyan Data `#00E5FF` → Electric Blue `#0066FF` (degradado o sólido) sobre fondo `#0B1325`. Versión monocroma en `#F4F6F8` (fondo oscuro) o `#0F172A` (fondo claro).
- **Uso:** dejar aire alrededor (mínimo la altura de la "F"); no deformar, rotar ni agregar sombras pesadas.

## Voz y tono
**Técnico, preciso, moderno y profesional.**
- Frases cortas y concretas; números reales cuando los hay ("de 77 filas a 70", "de medio día a un minuto").
- Explicar el resultado para el negocio, no solo la técnica.
- Evitar: exageraciones ("revolucionario", "el mejor"), jerga innecesaria, signos de exclamación en exceso.
- En español, voseo rioplatense para el público local; inglés claro y simple en Fiverr.

| ✅ Así | ❌ Así no |
|---|---|
| "Automatizamos el reporte mensual: ahora se genera en un minuto." | "¡¡Revolucionamos tu negocio con IA de última generación!!" |
| "Unificamos 58 variantes de nombres en 17 valores." | "Hacemos magia con tus datos." |

## Slogan / posicionamiento
> **"Automatización de Procesos & Soluciones de Datos"**

Usarlo debajo del logotipo, en portadas (LinkedIn, Fiverr) y en el `<title>`/encabezado de la web cuando corresponda.

## Identidad gráfica en código
Colores tomados de `theme-factory`.

### Elementos activos o enfocados
- Borde cian/azul en el elemento activo o con foco:
```css
:focus-visible {
  outline: 2px solid var(--fds-cyan);
  outline-offset: 2px;
}
/* En modo claro el cian no alcanza contraste 3:1 sobre blanco: usar azul */
:root[data-theme="light"] :focus-visible { outline-color: var(--fds-blue); }
.is-active,
.card:focus-within {
  border-color: var(--fds-blue);
  box-shadow: 0 0 0 1px var(--fds-blue), 0 0 16px rgba(0, 229, 255, .15);
}
```

### Indicadores de estado de pipelines de datos
| Estado | Color | Ícono / forma | Texto |
|---|---|---|---|
| Éxito | `#10B981` (Success Green) | ● sólido / ✓ | "Completado" |
| Error | `#EF4444` | ● sólido / ✕ | "Error" |
| En proceso | `#00E5FF` (Cyan Data) | ● con pulso animado | "Procesando…" |
| Pendiente | `--fds-muted` | ○ contorno | "En espera" |

```html
<span class="status status--running" role="status">
  <span class="status__dot" aria-hidden="true"></span>Procesando…
</span>
```
```css
.status { display: inline-flex; align-items: center; gap: .5rem; font-size: .875rem; }
.status__dot { width: .5rem; height: .5rem; border-radius: 50%; background: currentColor; }
.status--success { color: var(--fds-green); }
.status--error   { color: var(--fds-red); }
.status--running { color: var(--fds-cyan); }
.status--pending { color: var(--fds-muted); }
.status--running .status__dot { animation: fds-pulse 1.2s ease-in-out infinite; }
@keyframes fds-pulse { 50% { opacity: .3; transform: scale(.8); } }
@media (prefers-reduced-motion: reduce) { .status--running .status__dot { animation: none; } }
```
- El estado **nunca** se comunica solo con color: siempre va acompañado de texto o ícono (accesibilidad).
