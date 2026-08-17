# farmearaura.com

Static site, no backend. Four locales, generated from JSON copy files by `build.py`.

## URL map

| URL | hreflang | head term | vol/mo |
|---|---|---|---|
| `/` | es-AR + es + x-default | farmear aura | 350 |
| `/mx/` | es-MX | farmear aura | 300 |
| `/es/` | es-ES | aura farming | 1.200 |
| `/br/` | pt-BR + pt | farmar aura | **31.000** |
| `/que-es-farmear-aura/` | es-AR + es + x-default | que es farmear aura | 150 |
| `/mx/que-es-farmear-aura/` | es-MX | que es farmear aura | 200 |
| `/es/aura-farming/` | es-ES | aura farming | 1.200 |
| `/br/o-que-e-farmar-aura/` | pt-BR + pt | o que é farmar aura | **16.000** |
| `/legal/privacidad/` `/cookies/` `/sobre-nosotros/` `/contacto/` | es + x-default | — | — |
| `/br/legal/privacidade/` `/cookies/` `/sobre/` `/contato/` | pt | — | — |

Slugs differ per market on purpose. Spain searches the English term, not the Spanish
verb. Brazil uses "farmar", not "farmear", and has a large sub-cluster around
"campeonato de farmar aura" (~14k) that gets its own H2 on the BR guide.

Legal pages exist in two languages, not four: legal register is formal and neutral,
so voseo would read as an error. AR/MX/ES share `/legal/`, BR has `/br/legal/`.

## Build

    python3 build.py     # -> dist/

Requires Python 3.9+. No dependencies.

Edit copy in `locales/*.json`, never in `dist/` — it is generated and wiped on every
build. `src/app.html` is the calculator template, `src/guide.tpl.html` the guide,
`src/page.tpl.html` the legal pages.

Adding a locale = one JSON file + one entry in `ORDER` in `build.py`.

Guide section count is data-driven: a locale with `extraIntro`/`extraBody` in its
guide gets an extra H2 (that is how Brazil's campeonato section works). The build
asserts headings and sections match and fails loudly on a mismatch.

## Deploy (Cloudflare Pages)

| Setting | Value |
|---|---|
| Framework preset | None |
| Build command | `python3 build.py` |
| Build output directory | `dist` |
| Env var | `PYTHON_VERSION = 3.11` |

Alternative: remove `dist/` from `.gitignore`, commit it, leave the build command
empty and set output directory to `dist`. Cloudflare then just serves the files and
you build locally before each push.

## Before launch

- [ ] Fill the placeholders — see `TODO-LEGAL.md`
- [ ] Create the `hola@` and `contato@` mailboxes
- [ ] Self-host the three fonts (fixes the Google Fonts IP disclosure in the privacy
      policy *and* the share-card rendering failure inside the TikTok webview)
- [ ] OG image per locale
- [ ] Verify no cookies are set, in DevTools, on the live domain

## Domain note

Brazil is ~44k searches/mo against ~1.7k for all three Spanish markets combined, on a
Spanish-named domain, sitting at `/br/`. Worth revisiting after four weeks of Search
Console data — if it takes off, migrate `/br/` to its own exact-match domain rather
than to a subdomain.
