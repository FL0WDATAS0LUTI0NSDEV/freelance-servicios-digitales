# Agentes de Claude Code — FlowData Solutions

Cinco agentes especializados, guardados en `.claude/agents/`. Claude Code los usa solo cuando la tarea coincide, o podés pedirlos por nombre: *"usá el agente redactor-propuestas con este proyecto: …"*.

| Agente | Qué automatiza | Cómo pedirlo |
|---|---|---|
| **redactor-propuestas** | Lee un proyecto de Workana/Upwork/Fiverr, dice si conviene postularse, sugiere precio y escribe la propuesta lista para pegar | "Armame la propuesta para este proyecto: [pegá el texto]" |
| **analista-datos** | Diagnostica y limpia la planilla de un cliente con un script reproducible e informe de cambios | "Analizá el archivo de [cliente] que dejé en `clientes-privado/[cliente]/`" |
| **generador-reportes** | Arma reportes automáticos (HTML/Excel), dashboards web o guías de Power BI con tu diseño | "Generá el reporte mensual de [cliente] con los datos limpios" |
| **control-calidad** | Revisa una entrega antes de mandarla: que funcione, que los números cierren, diseño y privacidad | "Revisá la entrega de [cliente] antes de mandarla" |
| **contenido-linkedin** | Escribe publicaciones y respuestas para la página de empresa de LinkedIn con tu voz de marca | "Escribí un post sobre el dashboard interactivo" |

## Flujo típico de un proyecto
1. **redactor-propuestas** → mandás la propuesta.
2. Te contratan → guardás los archivos del cliente en `clientes-privado/<cliente>/`.
3. **analista-datos** → diagnóstico y limpieza.
4. **generador-reportes** → reporte o dashboard.
5. **control-calidad** → revisión final.
6. Entregás y ofrecés el **mantenimiento mensual** (mensaje en el kit).
7. **contenido-linkedin** → publicás un caso (sin datos del cliente, o con su permiso).

## Privacidad
- `clientes-privado/` está en `.gitignore`: lo que pongas ahí **no se sube** al repo público.
- Los agentes tienen la instrucción de no copiar datos de clientes fuera de esa carpeta y de revisar `git status` antes de terminar.
- Igual, antes de cada commit, mirá qué archivos se suben.

## Límites
- Los agentes **no envían nada por vos**: no publican en LinkedIn ni mandan propuestas o mails. Te dejan el texto listo y vos lo enviás.
- Funcionan en Claude Code (en la web o en tu computadora) cuando abrís una sesión con este repo.
