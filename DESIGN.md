# Design System: Solomon HR OCR Workbench

## 1. Visual Theme & Atmosphere
這是一個高密度、內部營運用的 HR OCR 工作台。設計語言應該像安靜的 operations cockpit：資訊清楚、狀態明確、表格容易掃描，避免 marketing-style hero、裝飾性大圖、霓虹漸層或過度卡片化。

- **Density:** Cockpit Dense 7/10
- **Variance:** Predictable Asymmetric 3/10
- **Motion:** Restrained CSS Micro-motion 3/10

## 2. Color Palette & Roles
- **Canvas Mist** (`#F2F5F9`) - App background.
- **Pure Surface** (`#FFFFFF`) - Panels, table bodies, input surfaces.
- **Soft Surface** (`#F8FAFC`) - Toolbars, subtle table hover, upload wells.
- **Charcoal Ink** (`#172033`) - Primary text.
- **Strong Ink** (`#111827`) - Headings and strong labels.
- **Muted Steel** (`#667085`) - Secondary text and metadata.
- **Whisper Border** (`#D9E0EA`) - Structural 1px lines.
- **Steel Border** (`#B9C4D3`) - Stronger hover and emphasis borders.
- **Operational Blue** (`#1D6FD8`) - The single accent for active steps, primary actions, focus rings.
- **Success Mint** (`#ECFDF3`) - Confirmed, parsed, completed states.
- **Warning Sand** (`#FFF7DB`) - Needs review.
- **Error Rose** (`#FFE9E7`) - Missing, unresolved, failed states.

Rules: max one accent color. No neon glow, no purple/blue AI gradient treatment, no pure black.

## 3. Typography Rules
- **UI Sans:** `Aptos`, `Segoe UI`, `Noto Sans TC`, `Arial`, sans-serif.
- **Mono/Data:** `Cascadia Mono`, `Consolas`, `SFMono-Regular`, monospace.
- Use tabular numbers everywhere.
- Headings are controlled and compact; hierarchy comes from weight, spacing, and color.
- Body/help text should stay below 72 characters where practical.
- Serif fonts are banned in this dashboard.

## 4. Component Stylings
- **Buttons:** 6px radius, one blue filled primary, white secondary. Active press moves down 1px. No outer glow.
- **Workflow Steps:** Active step uses Operational Blue with restrained sheen motion. Done state uses Success Mint.
- **Panels:** 8px radius, light border, subtle tinted shadow. Do not nest cards inside cards.
- **Toolbars:** Soft Surface background, 1px border, compact controls grouped in one row where possible.
- **Inputs:** Label above when space allows. Focus ring uses Operational Blue at low opacity.
- **Tables:** Sticky headers, compact row height, hover highlight, tabular numbers, no decorative striping.
- **Status Chips:** Green for parsed/ok, yellow for warning, rose for missing/error, blue for reviewed or confidence notes.

## 5. Layout Principles
- Preserve the five-step workflow and route/API contracts.
- Keep content in a `1440px` max-width shell.
- Use grid for fixed-format regions and tables; avoid flex percentage math.
- In schedule review, prefer staff-level rows with shift chips over raw day-by-day rows.
- Keep table horizontal scroll inside table containers only; the page itself must not overflow horizontally.
- On mobile, controls stack vertically and touch targets must be at least 44px where practical.

## 6. Motion & Interaction
- Motion is only for state feedback: active workflow sheen, hover transitions, active button press.
- Animate `transform` and `opacity` only.
- Respect `prefers-reduced-motion`.
- Do not add scroll hijacking, custom cursor, bouncing cues, or decorative animation.

## 7. Anti-Patterns
- No emojis.
- No pure black.
- No neon glow.
- No oversaturated accent palette.
- No generic 3-card marketing layout.
- No centered landing-page hero inside the app.
- No decorative orbs or bokeh.
- No placeholder names in UI examples.
- No fake precision metrics.
- No AI copywriting phrases such as "Elevate", "Seamless", "Unleash", or "Next-Gen".
