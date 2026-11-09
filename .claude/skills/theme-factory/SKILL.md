---
name: theme-factory
description: Motor de temas de FlowData Solutions. Define los tokens de diseño (variables CSS o tailwind.config.js) para los temas FDS Dark (por defecto) y FDS Light, los colores de acento, y el switcher claro/oscuro con persistencia. Usar al crear estilos, configurar Tailwind o agregar un toggle de tema.
---

# theme-factory — Capa 1 (FDS)

## Paletas soportadas

| Token | FDS Dark (default) | FDS Light |
|---|---|---|
| `--fds-bg` (fondo) | `#0B1325` | `#F8FAFC` |
| `--fds-card` (tarjetas) | `#131F37` | `#FFFFFF` |
| `--fds-border` (bordes) | `#1E2D4A` | `#E2E8F0` |
| `--fds-text` (texto) | `#F4F6F8` | `#0F172A` |

| Acento | Color | Uso |
|---|---|---|
| `--fds-cyan` — Cyan Data | `#00E5FF` | Datos, gráficos, highlights, foco |
| `--fds-blue` — Electric Blue | `#0066FF` | Acción principal, links, botones |
| `--fds-green` — Success Green | `#10B981` | Éxito, variaciones positivas |

Derivados permitidos: `--fds-muted` (texto secundario) = `--fds-text` al 64 % de opacidad. Rojo de error recomendado: `#EF4444`; ámbar de "en proceso": `#F59E0B`.

## Implementación con variables CSS

```css
:root,
:root[data-theme="dark"] {
  --fds-bg: #0B1325;
  --fds-card: #131F37;
  --fds-border: #1E2D4A;
  --fds-text: #F4F6F8;
  --fds-muted: rgba(244, 246, 248, .64);
  color-scheme: dark;
}
:root[data-theme="light"] {
  --fds-bg: #F8FAFC;
  --fds-card: #FFFFFF;
  --fds-border: #E2E8F0;
  --fds-text: #0F172A;
  --fds-muted: rgba(15, 23, 42, .64);
  color-scheme: light;
}
:root {
  --fds-cyan: #00E5FF;
  --fds-blue: #0066FF;
  --fds-green: #10B981;
  --fds-red: #EF4444;
  --fds-amber: #F59E0B;
}
body { background: var(--fds-bg); color: var(--fds-text); }
```

- FDS Dark es el **default**: si no hay preferencia guardada, usar dark.
- En modo claro, el cyan `#00E5FF` **no** sirve para texto (contraste bajo): usarlo solo en gráficos y bordes; para texto de acento usar `--fds-blue`.

## Implementación con Tailwind (`tailwind.config.js`)

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        fds: {
          bg: 'var(--fds-bg)',
          card: 'var(--fds-card)',
          border: 'var(--fds-border)',
          text: 'var(--fds-text)',
          muted: 'var(--fds-muted)',
          cyan: '#00E5FF',
          blue: '#0066FF',
          green: '#10B981',
        },
      },
      fontFamily: {
        sans: ['Inter', '"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
    },
  },
};
```
Las variables CSS de arriba se definen igual en el CSS global; Tailwind solo las referencia, así el cambio de tema no requiere clases duplicadas.

## Switcher claro/oscuro con persistencia

```html
<button id="theme-toggle" type="button" aria-label="Cambiar tema">◐</button>
<script>
  // Aplicar el tema antes de pintar para evitar parpadeo (poner en <head>)
  (function () {
    let t = 'dark';
    try { t = localStorage.getItem('fds-theme') || 'dark'; } catch (e) {}
    document.documentElement.dataset.theme = t;
  })();
</script>
```
```js
const toggle = document.getElementById('theme-toggle');
toggle?.addEventListener('click', () => {
  const root = document.documentElement;
  const next = root.dataset.theme === 'light' ? 'dark' : 'light';
  root.dataset.theme = next;
  try { localStorage.setItem('fds-theme', next); } catch (e) {}
  toggle.setAttribute('aria-pressed', String(next === 'light'));
});
```
- Persistencia en `localStorage` (clave `fds-theme`), envuelta en `try/catch` por navegadores con almacenamiento bloqueado. Usar cookie (`fds-theme=dark; path=/; max-age=31536000`) solo si el tema se necesita del lado del servidor (Next.js SSR).
- El script de inicialización va en el `<head>` para que no haya parpadeo de tema.
- El botón debe ser accesible por teclado y tener `aria-label`.

## Relación con las otras skills
- Los tokens de esta skill son la **fuente única de colores**: `top-design` y `brand-guidelines` los usan.
- La estructura y accesibilidad del switcher siguen `frontend-design`.
