# farmearaura.com — Site Overview

_Last updated: 2026-09-03_

A Spanish/Portuguese/English humor site built around the "aura farming" TikTok meme: an "aura points" personality quiz, several interactive voting/duel games, and a growing SEO content cluster. This document is a snapshot of everything built so far — architecture, features, and per-locale coverage.

---

## 1. Stack & architecture

- **Hosting**: Cloudflare Workers with static assets (not classic Cloudflare Pages). Config in `wrangler.jsonc`.
- **Backend**: `worker.js` — a single Worker `fetch()` handler that only intercepts `/api/*` routes; every other request (all HTML pages, `robots.txt`, etc.) is served directly by Cloudflare's static-assets layer, untouched by Worker code.
- **Database**: Cloudflare D1, database `aura`. Tables use a composite `(loc, id)` primary key so every locale's data lives in the same tables:
  - `candidatos` / `duelos` / `votantes` — everyday-archetype duels
  - `h_candidatos` / `h_duelos` / `h_votantes` — historical-figure duels
  - `f_candidatos` / `f_duelos` / `f_votantes` — celebrity duels
- **Scoring**: Elo-style, K=32, starting aura 1000. Winning a duel steals points from the loser (more if the loser had more aura).
- **Static site generator**: Python build scripts read JSON content from `locales/` and HTML string templates (`.tpl.html`) from `src/`, and write finished pages to `dist/` (git-ignored, CI-only artifact):
  - `build.py` — home/calculator pages + the "qué es farmear aura" guide article + legal pages + `robots.txt` + `_redirects` + `sitemap.xml` scaffold
  - `build_duelos.py` — everyday-archetype duels (votar/ranking/historial)
  - `build_historia.py` — historical-figure duels (votar/ranking)
  - `build_famosos.py` — celebrity duels (votar/ranking)
  - `build_articles.py` — all standalone content pages: the color-of-aura quiz cluster, "reglas de farmear aura", the contador de aura tool, the aura-memes roundup, and each locale's other one-off SEO pages
  - `build_batallas.py` — the interactive real-world "batallas de aura" venue map (SVG per-country map + venue cards), one per locale
  - `nav_data.py` — shared nav/footer link data imported by all the builders above, so the builders never drift out of sync on URLs, labels, or the footer's social links
- **Deploy pipeline**: Cloudflare's Git integration (Workers Builds) runs, on every push to `main`:
  ```
  python3 build.py && python3 build_duelos.py && python3 build_historia.py && python3 build_famosos.py && python3 build_articles.py
  ```
  then `npx wrangler deploy`. **Important**: `build.py` has a strict placeholder check — every `(old, new)` string pair it tries to substitute into a template must actually be found in that template, or the entire build hard-fails (`sys.exit`) for every locale. This has bitten us once already (a template edit without a matching code update silently broke every deploy for several hours). `build_batallas.py` is confirmed deployed too (its pages are live across all 12 locales), but its exact place in the actual build command wasn't independently re-verified this pass — check the Cloudflare dashboard's Build configuration if this list needs to be authoritative again.
- **No local Python** in this dev environment — the build only ever runs on Cloudflare's own CI. Local verification is done by reading `build.py` carefully, pushing, and checking the live result (curl / browser automation), plus `npx wrangler deployments list` to confirm a build actually fired.
- **Repo**: `github.com/josuewill099/farmearaura`, single `main` branch, Cloudflare auto-deploys on push.

---

## 2. Locales (12)

| Code | Language tag | Region | Base path | Verb form | Notes |
|---|---|---|---|---|---|
| `ar` | es-AR | Argentina | `/` (root, default locale) | voseo | Owns the bare `es` hreflang fallback |
| `mx` | es-MX | México | `/mx/` | tuteo | |
| `es` | es-ES | España | `/es/` | tuteo | Full 8/8 color-quiz colors built |
| `br` | pt-BR | Brasil | `/br/` | — | Portuguese; own "farmar aura" content cluster, uses "você" |
| `cl` | es-CL | Chile | `/cl/` | tuteo | |
| `pe` | es-PE | Perú | `/pe/` | tuteo | No "reglas de farmear aura" page |
| `co` | es-CO | Colombia | `/co/` | tuteo | No "reglas de farmear aura" page |
| `ec` | es-EC | Ecuador | `/ec/` | tuteo | Newer locale; no "reglas de farmear aura" page either |
| `us` | en-US | United States | `/us/` | — | English; owns the bare `en` hreflang fallback |
| `esus` | es-US | United States (Spanish) | `/es-us/` | tuteo | A **language variant of the US market**, not a separate country — reciprocal en-US/es-US hreflang with `us`; shares `us`'s real-world facts (e.g. same empty/nascent states on the battles map, same local-flavor angle on the memes page) rather than getting independently-researched local content |
| `uy` | es-UY | Uruguay | `/uy/` | voseo | Mirrors AR's full feature set |
| `pt` | pt-PT | Portugal | `/pt/` | — | Portuguese; "tu" register, distinct vocabulary from `br` (e.g. "à tua volta" not "ao seu redor") |

`LEGAL_OF` groups locales by legal-content language: `{ar, mx, es, cl, pe, co, esus, uy, ec} → es`, `{br, pt} → pt`, `{us} → en`. `GENERIC` (bare-language hreflang owners): `ar → es`, `br → pt`, `us → en`. All 12 locales are otherwise at feature parity: 24 duelos candidates, 17 historia candidates, 17 famosos candidates, and 4 legal pages each — confirmed via a full cross-locale audit on 2026-09-03 (see §6).

---

## 3. Features

### 3.1 Calculadora de Aura (home page)
The flagship tool, at each locale's root path. A 7-question quiz across 3 modes (Gamer / Escuela·Colegio·Liceo / Fiesta·Joda·Crush), producing a final "aura score" and a shareable card. Fully client-side — no account, no photos, nothing saved. Includes an About section and an FAQ with `FAQPage` JSON-LD. Recently cleaned up: removed the "farmearaura.com" eyebrow label, removed a duplicate guide-link/legal-links line that sat under the calculator, closed the large empty gap before the name input, and removed `maximum-scale=1` from the viewport meta tag (was blocking pinch-zoom, a Lighthouse a11y/best-practices failure).

### 3.2 Duelos de Aura (everyday-archetype duels)
Head-to-head voting between everyday archetypes reinvented with local slang per country (e.g., Argentina: "se olvidó la SUBE"; Uruguay: "se olvidó la tarjeta STM"). Three pages per locale: **Votar**, **Ranking**, **Historial** (recent duels feed).

### 3.3 Duelos Históricos (historical-figure duels)
Same mechanic, historical figures. Mostly a shared/universal roster (Cleopatra, Einstein, Napoleón, Hipatia...) with a handful of locale-specific swaps (Argentina: San Martín, Gardel, Maradona; Uruguay: Artigas, Galeano, Zitarrosa, Obdulio Varela...). Two pages: **Votar**, **Ranking**.

### 3.4 Duelos entre Famosos (celebrity duels)
Fully locale-specific celebrity rosters (footballers, musicians, actors relevant to each country — researched per market, not reused across locales). Two pages: **Votar**, **Ranking**. Originally shipped nested inside the Duelos dropdown (to avoid a mobile nav overflow bug); later promoted to its own top-level nav item once the mobile CSS was retightened to fit 5 items.

### 3.5 Contador de Aura (aura counter)
A literal tap-counter, deliberately distinct from the calculator's one-shot quiz — built after real search traffic showed demand for "contador de aura" / "contador de farmear aura" with essentially zero competing content. Mechanics:
- Main button: adds/subtracts a random amount (18 possible events per language, each with its own joke reason, mostly positive with a few negative to keep the "aura negativa" bit alive)
- Six quick-preset buttons: **+50 / +100 / +200 / +300 / +500 / +1,000**
- Total persists in the visitor's browser (`localStorage`), with a reset button
- No backend, nothing saved server-side

Localized across all 12 locales: same `contador-de-aura` slug for the 9 Spanish-tuteo/voseo markets (joins the existing hreflang sibling group), `contador-de-farmar-aura` for Brazil and Portugal, `aura-counter` for the US. Voseo/tuteo prose split (ar/uy vs the rest) plus a slang swap ("posta?" → "en serio?" outside ar/uy). Has its own nav link next to Calculadora on every locale.

### 3.6 Color de Aura quiz cluster
An SEO content cluster distinct from "farmear aura" (aura-as-carisma) — this one targets "aura reading" (aura-as-esoteric-color) search intent. Pillar page (`color-de-aura`) plus 8 individual color pages (azul, amarilla, verde, blanca, roja, negra, morada, rosa — these are the internal ids used everywhere in code, e.g. `COLOR_EMOJI`, `color_ids`, even where the displayed word differs). Each pillar/quiz-eligible page embeds a real interactive 6-question quiz (`aura-quiz.js`) that tallies answers and reveals a winning color — built to fix a P1 SEO problem where `/us/aura-test/` and `/us/aura-color-test/` were static lists ranking ~position 90 for clear quiz-intent queries.
- All 9 Spanish locales now have the full 8/8 colors (`es` used to have only 4 — closed 2026-09-03).
- US has its own English cluster: `aura-test`, `aura-color-test`, `piccolo-aura-farming`, `how-to-aura-farm` (no dedicated `/us/aura-{color}/` pages — the quiz shows English name+blurb with no "learn more" link there).
- **`br`/`pt` now have the full cluster too** (added 2026-09-03 — previously the only two locales with none of it). Real Portuguese words are used in the slugs, not the Spanish spellings: `aura-amarela` (not `-amarilla`), `aura-branca` (not `-blanca`), `aura-vermelha` (not `-roja`), `aura-preta` (not `-negra`), `aura-roxa` (not `-morada`) — `PT_COLOR_SLUG`/`PT_COLOR_NAME` in `build_articles.py` map the shared internal id to the real slug/display word per language. `build_quiz_widget()` gained a `lang.startswith("pt")` branch (it previously only had `es` vs. an English catch-all, so `br`/`pt` would have silently rendered an **English** quiz once the pillar page existed) with `QUIZ_QUESTIONS_PT_BR` (você) and `QUIZ_QUESTIONS_PT_PT` (tu) — same br/pt-register-split pattern as `GAMER_QUESTIONS_PT_BR/PT_PT`.
- Brazil and Portugal also each have their own separate "farmar aura" content cluster (distinct from this one): `como-farmar-aura`, `campeonato-de-farmar-aura`, `farmar-aura-meme`, etc.

### 3.7 Reglas de Farmear Aura
A standalone "rules of the meme" explainer page. Built for `ar, mx, cl, es, uy` (not `pe, co, esus` — no proven demand there yet at the time; `ec` didn't exist yet either). Flagged in the 2026-09-03 consistency audit as worth revisiting now that `pe`/`co`/`ec` have all just received real, keyword-backed content via the aura-memes rollout (§3.11) — no action taken yet, just noted.

### 3.8 Guía / "Qué es farmear aura"
The main long-form explainer article per locale: origin story, a fictional points ledger, 7 "rules", a "what makes you lose aura" list, a glossary, and a 10-item FAQ with schema. Slug varies by locale/market convention (e.g. `es` uses `aura-farming`, `br` uses `o-que-e-farmar-aura`, `us` uses `what-is-aura-farming`).

### 3.9 Legal pages
About / Privacy / Cookies / Contact, shared per language group (not per country) via `LEGAL_OF`. Business identity: **Farmear Aura SRL, Argentina**.

### 3.10 Batallas de Aura (real-world venue map)
An interactive map of real, in-person "aura battle" gatherings — physical posing/charisma-duel meetups that spread from the online meme in mid-2026. Positioned as a **curated showcase**, not a live directory (several competitor sites already do that): every venue entry is a real event with a date and a news-article source, no fabricated or hotlinked-only entries.

- One page per locale, slug `batallas-de-aura` (Spanish, plural — distinct from an older, unrelated `batalla-de-farmear-aura` singular satellite page some locales also have) or `batalhas-de-farmar-aura` (br/pt); `aura-battles` for `us`. Full URL map lives in `nav_data.NAV_URLS["batallas"]`.
- Built by `build_batallas.py`: each locale's `locales/batallas-{loc}.json` holds `mapHint`/`mapAriaLabel`/`venueCountLabel` (fully pre-written per locale — an earlier version tried to *assemble* these from Spanish grammar fragments, which broke for Chile/Peru's feminine "región" and would have broken completely for Portuguese; now every locale just writes its own full sentences) plus a `venues[]` list.
- Map artwork is real per-country geometry, not stock SVGs: converted from Highcharts' `map-collection-dist` (Natural Earth data, properly per-feature named) via one-off `convert-geojson*.js` scratch scripts (uncommitted) into `locales/*.geo.json` — bounding-box-fit projection, area-weighted polygon centroids for label placement, `fill-rule:evenodd` for provinces with holes (Spain, Portugal).
- **Honest empty state**: Portugal, US, and US-Spanish ship with `venues: []` because no event meeting the sourcing bar was found there — the page's intro copy says so explicitly rather than presenting a silently empty map or padding it with weak entries.
- Nav integration: the first nav item (normally "Calculadora") is swapped to "Batallas" + a link to this page, for every locale that has one (currently all 12) — see `nav_data.nav_html()`'s `"batallas" in U` check. Brazil/Portugal specifically use the nav label **"Mapa"**, not "Batalhas", because both already use "Batalhas" for an unrelated pre-existing historical-duels feature at `/br/batalha-de-aura/`.
- Each page also carries an FAQ (5 items, `FAQPage` JSON-LD) covering what these battles are and how a winner is decided — added 2026-09 across all 12 locales, positioned directly above the "cada entrada tiene su fuente" footer note. The Spanish FAQ text is fully impersonal/third-person, so the identical copy is reused verbatim across all 9 Spanish locales without a voseo/tuteo split.

### 3.11 Aura Memes (curated meme roundup)
A "best memes about aura farming" page, slug `aura-memes` shared verbatim across all 12 locales (same cross-locale-sibling-page pattern as `piccolo-aura-farming` — reusing an identical slug string across locales' `articles-{loc}.json` makes `build_articles.py` treat them as reciprocal hreflang siblings automatically, no extra code needed). Built via `build_articles.py`'s existing free-form `sections` schema (heading + paragraphs, no bespoke page type).

- **4 memes are identical across every locale** (translated, not re-researched, since they're global TikTok phenomena, not local events): the "Aura Points" scoring format, Piccolo Aura Farming (kept brief + linked out to the dedicated page for locales that have one — `ar`/`mx`/`br`/`us`; written in full for the other 8), Pure Aura Girl (IShowSpeed), and a Tom &amp; Jerry aura-edit trend. "Feels the Aura" is covered in every locale too but **without** an embed, since no single representative post could be verified.
- **Each locale's closing section is independently researched and sourced**, not translated from Argentina's — several tie directly into venues already documented on that locale's own batallas-de-aura map. Real, verified examples found: Argentina (streamer La Cobra popularizing "aura" via Messi comparisons), Brazil (Endrick's viral goal celebration vs. Egypt), Mexico (Toluca FC's Jesús Gallardo "+999 aura" moment), Spain (Lamine Yamal naming Cristiano Ronaldo as the definitive "aura" example), Colombia (streamer Westcol's "Juegos del Aura W" tournament), Ecuador (influencers Alex Vizuete &amp; Anthony Swagg hosting Guayaquil's first battle), US/es-US (Travis Kelce recreating the viral "boat kid" dance on his own TikTok, 14M+ views — es-US reuses this same story translated, rather than an independent one, since it's the same country's reality). Uruguay (Diego Forlán, via street interviews at a real event), Chile (a school inspector's viral battle with students), and Portugal (honestly notes the local scene is still nascent) came back **without** a verifiable public-figure example after genuine research effort — used the best real, sourced story available instead of forcing or fabricating one.
- **Embeds are real, official TikTok oEmbed blockquotes**, not hotlinked images or screenshots — each candidate URL was verified by calling `https://www.tiktok.com/oembed?url=...` and confirming it returns valid JSON *before* use, never guessed from a search snippet. This is the site's first-ever third-party script (`tiktok.com/embed.js`); it triggers TikTok's own cookie-consent prompt once an embed loads, a real, disclosed UX tradeoff of this approach. `render_sections()` in `build_articles.py` gained a `{"embed": "<raw html>"}` block type (renders without the `<p>` wrapper that would otherwise break the embed's `<blockquote>`) — same dispatch pattern already used for `{"ul": [...]}`/`{"dl": [...]}`.
- 5-item FAQ (`FAQPage` JSON-LD) per locale. **Known trap already hit once**: FAQ *question* text passes through an `esc()` helper that escapes `&` but not quotes — so an `&ldquo;`/`&rdquo;` entity used in a question renders as literal `&amp;ldquo;` text. FAQ *answers* and body-section text are not escaped, so entities work fine there. Fix used: don't quote terms in FAQ questions at all (matches how every pre-existing FAQ question on the site was already phrased anyway).
- Per-locale local-flavor research for this feature was parallelized across background agents (one per locale) rather than done serially, each independently required to verify sources and flag (not fabricate) when no strong example existed — see §5 for the general pattern.

### 3.12 Footer / social links
Every page's footer legal-links line now ends with **Facebook** (`facebook.com/farmearauracom`) and **Instagram** (`instagram.com/farmear_aura_com`), `rel="noopener" target="_blank"`, unstyled/plain-text like the rest of that line (matching, not deviating from, the site's existing footer convention rather than introducing icon buttons). Only 3 functions build this line site-wide, so one small edit to each covered all 12 locales and every page type: `nav_data.legal_links_html()` (covers articles, batallas, duelos, historia, famosos) and `build.py`'s own duplicated `legal_links()` (main guide + legal pages) and `app_legal_links()` (home/calculator page) — `build.py` keeps its own copies of this logic rather than importing `nav_data` for it (see nav_data.py's own docstring on why the duplication is deliberate), so a future change to the social links needs to touch both files' functions, not just one.

### 3.13 Navigation
Top-level nav, present on every page via `nav_data.nav_html()`: **Batallas (or Calculadora, for the locale-vs-page-type explained in §3.10) · Contador · Duelos (▾ Ranking, Historial) · Duelos Historia (▾ Ranking) · Famosos (▾ Ranking)**. Mobile CSS is deliberately tightened (`@media max-width:480px`, in both `src/app.html` and `src/duelos.css`) to fit all 5 top-level items in a 375px viewport without the layout-widening bug that hit this project twice (a hidden dropdown, then a too-wide row, both silently forcing the whole page wider on mobile browsers).

---

## 4. SEO infrastructure

- **hreflang**: full per-locale tags + a bare-language fallback (`es → ar`, `pt → br`, `en → us`) for shared content, so Spanish speakers in countries without their own locale (Venezuela, Ecuador, Guatemala, Costa Rica, Puerto Rico, Honduras, Paraguay, and Uruguay before it existed) land somewhere coherent instead of being split arbitrarily across markets — plus `x-default`.
- **Sitemap.xml**: appended to automatically by every build script; duel pages use `changefreq: daily` (down from `hourly`), articles use `monthly`. Format standardized to drop `<priority>` entirely and always write a real, dynamic `<lastmod>` (the actual build date) rather than a static/omitted one.
- **robots.txt**: `Disallow: /api/` for every listed crawler (Googlebot default, GPTBot, OAI-SearchBot, PerplexityBot, ClaudeBot, Google-Extended) — fixed an issue where Googlebot's headless renderer was fetching 54 JSON API endpoints per crawl session that carry no indexable content, pushing HTML crawl share down to 69%.
- **Structured data**: `WebPage`, `BreadcrumbList`, `Article`, `FAQPage`, `ItemList` JSON-LD across the site as appropriate.
- **External resources**: the site was 100% first-party (GA4 analytics only) until the aura-memes rollout (§3.11) added `tiktok.com/embed.js` — the first third-party script anywhere on the site. Worth remembering when reasoning about CSP, page weight, or cookie-consent behavior on those specific pages; every other page type remains script-free apart from analytics.
- **Fixes shipped this project** (from a GSC search-performance audit): missing bare-`es` hreflang fallback (was scattering ~19% of site traffic across markets inconsistently), duplicate titles across markets, a Spanish slug living on the English site (`/us/duels/historial/` → `/us/duels/recent/`, with a 301), unfilled legal-page template placeholders live in production, and the robots.txt/crawl-budget issue above.
- **Known non-issue investigated**: a GSC Host-status "robots.txt fetch — high fail rate" alert was diagnosed as most likely a Cloudflare edge/bot-management interaction (robots.txt itself always served 200 correctly) — recommended checking Bot Fight Mode / Security Level / WAF rules in the Cloudflare dashboard.

---

## 5. Content research & workflow notes

- Keyword/volume research uses an Ahrefs-backed MCP toolset; cross-referenced against the site's own GSC traffic, since "aura farming" is bleeding-edge TikTok slang that real search volume often outpaces third-party keyword databases for (several features here — the contador tool, the Uruguay locale's top FAQ entry — were built on real GSC traffic with **zero** tracked Ahrefs volume at build time). Also used to settle head-term/slug choices directly (e.g. confirming "aura meme" outweighs "memes de aura" ~20:1 in Argentina before naming that page).
- Bulk content generation (the color cluster, reglas, the counter's per-locale article text, aura-memes, batallas venues) is done via one-off Node scripts kept in the session scratchpad, not committed to the repo. The safe pattern for editing a large shared JSON file: build the new entry as a real JS object and let `JSON.stringify` handle escaping (not manual backslash-escaping of a hand-written string), then splice the generated text into the target file at a precisely-matched insertion point and `JSON.parse` the whole result before writing — never a full-file `JSON.parse`-then-`stringify` round trip, since that silently reformats every other entry's whitespace too.
- Voseo/tuteo text is handled with inline `"vos-form/tú-form"` markers resolved by a `fix_voseo()`/`fixVoseo()` helper (present in both `build_articles.py` and the Node generator scripts) — except where verb tense already happens to be identical between the two (e.g. the counter's event list is written entirely in preterite, which needs no marker at all). Confirmed the same is usually true of any *impersonal/third-person* Spanish copy (FAQ answers, encyclopedia-style descriptions): it needs no voseo/tuteo split at all and can be reused verbatim across all 9 Spanish locales — this is why the batallas FAQ and 4 of the 6 aura-memes sections are identical strings across locales, not `fix_voseo()`-processed. br/pt register differences (você vs. tu) are handled the opposite way: two fully separate hand-written arrays/strings per locale (see `GAMER_QUESTIONS_PT_BR/PT_PT`, `QUIZ_QUESTIONS_PT_BR/PT_PT`), not a marker-substitution helper — the vocabulary differences go beyond pronoun conjugation (e.g. "crush" vs. "paixonete", "nesses" vs. "nestes"), so a shared-marker approach was judged not worth it.
- Real-world local sourcing (batallas venues, aura-memes' per-locale closing section) has a hard no-fabrication bar: every claim needs an independently-verifiable news article or, for memes specifically, a TikTok URL confirmed via its own `oembed` endpoint before use — never a guessed video ID or an unconfirmed AI-search summary. When no example clears that bar (Portugal's battles map, several locales' meme-page local section), the honest answer is an explicit "not found yet" in the copy, not a weaker substitute presented as equivalent.
- For a research task that's naturally parallel across locales (e.g. "find one real local example per country"), background research agents — one per locale, each given the same strict sourcing/verification instructions — run concurrently rather than serially, with the calling session doing all the actual writing/JSON assembly itself afterward rather than delegating that part. Cut a 9-locale research pass from a serial afternoon to a handful of parallel rounds.

---

## 6. Open items / things to watch

- Crawl-budget fix (robots.txt `Disallow: /api/`) was deployed but its effect on GSC's Crawl Stats report typically takes 1–2 weeks to become visible — no recheck done yet.
- City-level query variants (e.g. "farmear aura valencia") — **substantially addressed** by the batallas-de-aura map (§3.10): Spain's page now documents real dated events in A Coruña, Vigo, Sevilla, Pamplona, Barcelona, and Palma with sources, covering most of the earlier concern. Valencia specifically still isn't covered (no qualifying sourced event found there yet); revisit if one surfaces.
- Cloudflare's Git-integration build pipeline has silently failed before without any user-visible error outside the Cloudflare dashboard's build log — worth spot-checking `npx wrangler deployments list` after any push that touches a shared template (`app.html`, `guide.tpl.html`, etc.). This pass's build_articles.py change (adding a `lang.startswith("pt")` branch to `build_quiz_widget()`, §3.6) was verified live afterward — including actually playing through the new br/pt quizzes end-to-end in a browser to confirm the result screen renders correctly — rather than assuming the deploy succeeded from the push alone.
- **Full 12-locale consistency audit run 2026-09-03** (prompted by a direct ask to check for consistency): duelos/historia/famosos/legal pages were already at exact parity (24/17/17/4 respectively) across all 12 locales — no action needed there. The color-de-aura cluster was the one real gap found (br/pt had none of it) and has since been closed (§3.6). Remaining known-and-intentional asymmetries, not gaps: `reglas-de-farmear-aura` in only 5 Spanish locales (§3.7, flagged to revisit); `piccolo-aura-farming` as its own page in only `ar`/`mx`/`br`/`us` (folded into the aura-memes page's text everywhere else instead); a handful of single-market quizzes (`aura-futbol`/AR, `aura-anime`/BR, `aura-crush`/AR, `aura-de-estudiante`/AR, `duelo-de-dia-de-muertos`/MX) that were always meant to be local flavor, not a template for every locale; batallas-de-aura's 0-venue "honest empty state" for `pt`/`us`/`esus` (§3.10). If asked to re-audit, the fast check is: diff each locale's `articles-{loc}.json` slug list against the others, don't assume a raw slug-string diff is meaningful on its own — `br`/`pt` use different slug spellings for equivalent concepts (`farmar` not `farmear`, real Portuguese color names), so cross-reference by concept, not string match.
- `locales/seasonal-{loc}.json` (only `ar`/`br`/`es`/`mx` currently have one) is **not** a rendered page — it's a pure build-time console reminder (`build.py`'s `check_seasonal()`) that prints upcoming seasonal-content deadlines (back-to-school, Carnaval, Día de Muertos, etc.) due within 30 days. Its absence in the other 8 locales just means no seasonal opportunity has been identified there yet, not a missing feature.
