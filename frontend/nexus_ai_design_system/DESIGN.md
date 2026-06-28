---
name: Nexus AI Design System
colors:
  surface: '#131315'
  surface-dim: '#131315'
  surface-bright: '#39393b'
  surface-container-lowest: '#0e0e10'
  surface-container-low: '#1c1b1d'
  surface-container: '#201f22'
  surface-container-high: '#2a2a2c'
  surface-container-highest: '#353437'
  on-surface: '#e5e1e4'
  on-surface-variant: '#c2c6d6'
  inverse-surface: '#e5e1e4'
  inverse-on-surface: '#313032'
  outline: '#8c909f'
  outline-variant: '#424754'
  surface-tint: '#adc6ff'
  primary: '#adc6ff'
  on-primary: '#002e6a'
  primary-container: '#4d8eff'
  on-primary-container: '#00285d'
  inverse-primary: '#005ac2'
  secondary: '#b1c6f9'
  on-secondary: '#182f59'
  secondary-container: '#304671'
  on-secondary-container: '#9fb5e7'
  tertiary: '#ffb786'
  on-tertiary: '#502400'
  tertiary-container: '#df7412'
  on-tertiary-container: '#461f00'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004395'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#b1c6f9'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#304671'
  tertiary-fixed: '#ffdcc6'
  tertiary-fixed-dim: '#ffb786'
  on-tertiary-fixed: '#311400'
  on-tertiary-fixed-variant: '#723600'
  background: '#131315'
  on-background: '#e5e1e4'
  surface-variant: '#353437'
typography:
  display-lg:
    fontFamily: Geist
    fontSize: 48px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.3'
    letterSpacing: -0.02em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: 0em
  label-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0.02em
  code:
    fontFamily: jetbrainsMono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: '1.6'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
  container-max: 1280px
  gutter: 24px
---

## Brand & Style
The design system is engineered for high-performance enterprise environments, specifically targeting developers and technical decision-makers. The brand personality is clinical, precise, and intellectually honest, evoking a sense of calm reliability through extreme clarity and reduction.

The aesthetic follows a **Premium Minimalist** movement, drawing heavily from the "Vercel/Linear" school of thought. It prioritizes function through high-quality typography and a restrained use of depth. Visual interest is generated not through decoration, but through the perfect execution of spacing, micro-interactions, and subtle material properties. The UI should feel like a sophisticated instrument rather than a consumer app.

## Colors
The color palette is strictly functional. We utilize a **Dark-first** default mode to reduce eye strain in technical workflows. 

- **Primary (#3b82f6):** Reserved exclusively for high-intent actions, active states, and critical progress indicators. 
- **Neutral/Background:** We use a deep "Zinc" scale. The base background is `#09090b`, providing a near-black canvas that makes text highly legible.
- **Surface:** Layered elements use `#18181b` and `#27272a` to create subtle hierarchy without the need for heavy shadows.
- **Success/Warning/Error:** Use standard semantic tones (Emerald/Amber/Rose) but desaturated to match the professional tone of the primary blue.

## Typography
This design system utilizes a unified scale combining **Geist** for structural/interface elements and **Inter** for long-form body text.

- **Geist** is used for all headings, buttons, and navigation items to provide a technical, modern edge.
- **Inter** is used for all body copy and descriptions to ensure maximum readability across different display densities.
- **Letter Spacing:** Headlines utilize tight tracking (-0.02em to -0.04em) to maintain a cohesive visual block, while UI labels use slight tracking (0.02em) to improve glanceability.

## Layout & Spacing
A strict **8px Grid System** governs all spatial relationships. Every margin, padding, and height increment must be a multiple of 8px (or 4px for micro-adjustments).

- **Grid Model:** A 12-column fluid grid for desktop with 24px gutters.
- **Consistency:** Horizontal padding for buttons and inputs must match the `md` (16px) unit. Vertical stacking of form elements should consistently use the `md` or `lg` units to ensure a rhythmic flow.
- **Mobile:** On mobile devices, gutters reduce to 16px, and the `2xl` and `3xl` spacing units are halved to maintain density.

## Elevation & Depth
Depth is conveyed through **Tonal Layering** and **Soft Ambient Shadows** rather than traditional skeuomorphism.

- **Base Layer:** Background at `#09090b`.
- **Level 1 (Cards/Inputs):** Background at `#18181b` with a 1px solid border of `#27272a`.
- **Level 2 (Popovers/Modals):** Background at `#1c1c1f` with a 1px border of `#3f3f46` and a soft, diffused shadow: `0 8px 30px rgba(0, 0, 0, 0.5)`.
- **Borders:** All interactive components use a thin 1px border. The border color should subtly brighten on hover to indicate interactivity.

## Shapes
The shape language is sophisticated and consistent. We use a **Rounded** philosophy but distinguish between container levels and interactive levels.

- **Containers & Cards:** Strictly 16px (`rounded-lg` equivalent) to create a soft, premium frame for content.
- **Interactive Elements:** Buttons, input fields, and dropdowns use 8px (the base `rounded` unit) to feel more precise and tool-like.
- **Inner Elements:** Elements inside a 16px container should ideally use an 8px radius to maintain nested corner harmony.

## Components
Consistent dimensions across all form elements are mandatory for the "instrument" feel.

- **Standard Height:** All Buttons, Inputs, and Dropdowns must share a 40px height for the "Medium" (default) size and 32px for "Small."
- **Buttons:** Primary buttons use a `#3b82f6` background with white text. Secondary buttons use a `#27272a` background with a subtle border. Ghost buttons have no background until hover.
- **Inputs:** Dark background (`#18181b`), 1px border (`#27272a`). On focus, the border transitions to the primary blue with a 2px outer "halo" (shadow-based).
- **Cards:** 16px radius, thin border, and no shadow when resting on the base background. When elevated (e.g., draggable), apply the Level 2 ambient shadow.
- **Chips/Badges:** Small 12px Geist Mono text, 4px radius, low-contrast background (Zinc-800).
- **Lists:** Rows should be at least 48px high with subtle separators (`1px solid #27272a`) and a "highlight" hover state using `#18181b`.