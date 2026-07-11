---
name: web-artifacts-builder
description: Build polished, self-contained HTML artifacts with React, Tailwind CSS, and shadcn/ui using Bellbird's Warm Tech visual system by default. Use for complex artifacts with state, multiple views, or rich data presentation; not for simple static HTML.
license: Apache-2.0. See LICENSE.txt.
---

# Bellbird Web Artifacts Builder

This is a Bellbird-customized derivative of Anthropic's `web-artifacts-builder` skill. The original source and Apache 2.0 license are retained in this directory; see `UPSTREAM.md`.

## Workflow

1. Initialize a React artifact with `scripts/init-artifact.sh <project-name>`.
2. Build the artifact using the Bellbird Warm Tech system below.
3. Run `pnpm build` and bundle it with `scripts/bundle-artifact.sh`.
4. Share the resulting `bundle.html` and visually inspect it when presentation matters.

## Bellbird Warm Tech System (default)

Use this visual system unless the user explicitly requests another brand.

### Palette

- **Navy `#08375A`** — dominant brand color; use for headers, high-impact panels, and formal milestones.
- **Teal `#188BA1`** — accent only; use for CTAs, key labels, icons, arrows, and focus states.
- **Warm Gray `#787472`** — secondary text, annotations, metadata, and technical detail.
- **Arena `#ECE5DE`** — primary page background and light editorial panels.
- **White** — readable content surfaces when separation is required.

### Typography and layout

- Use an offline system serif stack (`Georgia`, `Times New Roman`, `serif`) for display titles and key statements; it approximates Cormorant Garamond without external font requests.
- Use an offline system sans-serif stack (`Arial`, `Helvetica`, system UI) for body text, data, code, and controls; it keeps dense information legible.
- Make titles editorial and spacious, but keep body copy compact and readable. Use a mono stack only for paths, IDs, commands, and technical metadata.
- Prefer Arena backgrounds for roughly 70% of explanatory content and Navy panels for the remaining high-impact sections, warnings, conclusions, or milestones.
- Use square-to-soft corners (4–8px), restrained shadows, strong alignment, and generous whitespace. Avoid gradients, centered-card dashboards, excessive pills, and generic SaaS styling.

### Contrast and accessibility

- Use Navy text on Arena/white surfaces; use Arena/white text on Navy surfaces.
- Never use Warm Gray as primary body text on Navy. Reserve Teal on Navy for large labels, icons, or clearly contrasted CTAs.
- Keep data/code on clean solid backgrounds. Do not place thin text over textured or image backgrounds unless a solid backing panel exists.
- Provide visible focus states and semantic controls. Do not rely on color alone for status; pair it with text or iconography.

## Bundle requirements

- Artifacts must work without external fonts, image CDNs, or runtime UI dependencies after `bundle.html` is generated.
- Keep all interactive behavior client-side unless a user explicitly requests an integration.
- Before delivery, run `pnpm build`; then bundle to one `bundle.html` using the provided script.
