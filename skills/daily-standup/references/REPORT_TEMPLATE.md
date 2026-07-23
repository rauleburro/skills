# Plantilla del reporte

El equipo mantiene los títulos `yesterday`/`today` (según `output.headings`) aunque el cuerpo
esté en el idioma de `output.language`. Preferí resultados sobre actividad vaga. Nunca inventes
trabajo para una ventana vacía.

## Markdown (Slack y por defecto)

```
Yesterday

- Terminé <resultado verificado> (PR #123 mergeada a develop).
- Cerré <resultado> — <issue TASK-45>.

Today

- Sigo con <plan concreto> (<issue del tracker si aplica>).
- @Nombre necesito tu review de la PR #124 para poder mergear.
```

## HTML (Teams)

```html
<p><strong>yesterday</strong></p>
<ul>
  <li>Terminé <strong>[resultado verificado]</strong>.</li>
  <li>Cerré <a href="https://example.com/item">[resultado]</a>.</li>
</ul>
<p><strong>today</strong></p>
<ul>
  <li>Sigo con <strong>[plan concreto]</strong>.</li>
  <li>Voy a <strong>[próximo paso]</strong>.</li>
</ul>
```

Cuando el proveedor soporta HTML, mandá por su campo de contenido HTML, no como texto escapado.

## Nota privada al usuario (no se envía al canal)

Aparte del borrador, presentá al usuario:

- **Compromisos incumplidos**: "prometiste X el <fecha> y no hay evidencia" (estado `carried`).
- **Vencidas del tracker**: issues/tareas con fecha pasada, candidatas a Today.
- **Bloqueos de agenda**: reuniones de hoy (incluye personales solo aquí, nunca en el canal).
- **Fuentes no disponibles**: qué bajó la confianza del reporte.
