# NH Page Beautifier

## What It Delivers

- Skin A (`assets/beauty-A.css`): aligned with existing home style.
- Skin B (`assets/beauty-B.css`): modern landing-page style.
- Shared interaction (`assets/beauty.js`): FAQ accordion + lightweight reveal motion.
- Shared icon set (`assets/icons.svg`): SVG sprite.
- Conditional loading only on test pages (`home-style`, `new-template`) or pages using `[nhpb_landing]` shortcode.

## Enable On WordPress

1. Copy `wordpress-plugin/nh-page-beautifier` to `wp-content/plugins/`.
2. Activate plugin **Newcastle Hub Page Beautifier**.
3. Create/Update pages with shortcode:

```text
[nhpb_landing skin="a"]
[nhpb_landing skin="b"]
```

## Conditional Loading Strategy

- CSS/JS loaded in `wp_enqueue_scripts` only when:
  - current page slug is `home-style` / `new-template`, or
  - page content contains `[nhpb_landing]`.
- JS is deferred.
- Hero image preloaded in `wp_head` with `fetchpriority="high"`.

## Module Mapping (shared structure)

1. Hero
2. Trust / Proof
3. Services / Features
4. Steps / Process
5. Cases / Examples
6. FAQ Accordion
7. Final CTA

## Image + Icon Plan

- Hero image: one per page (A/B variant), everything else icon + cards.
- Icons are SVG symbols (`outline 2px`, rounded joins/caps).

### AI Prompt Suggestions

#### Hero A (Home Style)

```text
Create a clean SaaS-style hero illustration for a local business growth agency.
Style: bright, professional, minimal, blue palette (#0f4fbf #2f7ef7), soft gradients, whitespace-rich.
Include abstract dashboard cards and call-to-action blocks.
Aspect ratio 16:9, export WebP and AVIF.
Target size: desktop 180KB, mobile 110KB.
No text in image.
```

#### Hero B (New Template)

```text
Create a modern premium landing hero visual for digital growth services.
Style: dark navy background, teal/cyan accent glow, subtle glassmorphism cards, high contrast.
Keep it elegant and minimal, no clutter, no heavy textures.
Aspect ratio 16:9, export WebP and AVIF.
Target size: desktop 220KB, mobile 130KB.
No text in image.
```

### Icon Usage by Module

- Services: `pos`, `website`, `seo`, `support`, `shield`, `chat`
- Steps: `checklist`, `clock`
- Trust: optional `shield`

## Performance Guardrails

- No large animation libraries.
- Only `opacity/transform` transitions.
- Keep icon delivery via sprite/inline SVG.
- Use lazy loading for non-hero media.
- Keep hero eager + preload.
