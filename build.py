#!/usr/bin/env python3
"""
farmearaura.com static build.

  python3 build.py

Reads  : src/app.html  (calculator template, neutral copy)
         locales/*.json
Writes : dist/  — ready to push to Cloudflare Pages

Argentina is the default locale and lives at the root.
"""
import json, re, pathlib, shutil, sys

import nav_data

ROOT   = pathlib.Path(__file__).parent
SRC    = ROOT / "src"
DIST   = ROOT / "dist"
DOMAIN = "https://farmearaura.com"
ORDER  = ["ar", "mx", "es", "br", "cl", "pe", "co", "us", "esus"]    # ar first = default
GENERIC = {"es": "ar", "pt": "br", "en": "us"}   # bare language code -> owning locale

def load(code):
    return json.loads((ROOT / "locales" / f"{code}.json").read_text("utf-8"))

LOC = {c: load(c) for c in ORDER}
LEGAL = {k: json.loads((ROOT / "locales" / f"legal-{k}.json").read_text("utf-8"))
         for k in ("es", "pt", "en")}
LEGAL_OF = {"ar": "es", "mx": "es", "es": "es", "br": "pt",
            "cl": "es", "pe": "es", "co": "es", "us": "en",
            "esus": "es"}   # locale -> legal language
for _c, _l in LOC.items():
    _l["_code"] = _c
DEFAULT = next(l for l in LOC.values() if l["isDefault"])

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ----------------------------------------------------------------- hreflang
def hreflang(kind):
    """kind: 'app' or 'guide'. Returns the full <link> block for the cluster."""
    def url(l):
        if kind == "app":
            return DOMAIN + l["path"]
        return f'{DOMAIN}{l["path"]}{l["guide"]["slug"]}/'
    out = []
    # bare language codes first: unmatched speakers of each language land on its owner
    for lang, code in GENERIC.items():
        out.append(f'<link rel="alternate" hreflang="{lang}" href="{url(LOC[code])}">')
    for c in ORDER:
        out.append(f'<link rel="alternate" hreflang="{LOC[c]["code"]}" href="{url(LOC[c])}">')
    out.append(f'<link rel="alternate" hreflang="x-default" href="{url(DEFAULT)}">')
    return "\n".join(out)

def legal_url(langkey, pagekey):
    L = LEGAL[langkey]
    return f'{DOMAIN}{L["base"]}{L["pages"][pagekey]["slug"]}/'

# es <-> pt <-> en equivalents, so each legal page has a full hreflang cluster
LEGAL_PAIRS = [
    {"es": "privacidad", "pt": "privacidade", "en": "privacy"},
    {"es": "cookies", "pt": "cookies", "en": "cookies"},
    {"es": "sobre-nosotros", "pt": "sobre", "en": "about"},
    {"es": "contacto", "pt": "contato", "en": "contact"},
]

def legal_hreflang(pagekey, langkey):
    pair = next(p for p in LEGAL_PAIRS if p[langkey] == pagekey)
    out = [f'<link rel="alternate" hreflang="{lk}" href="{legal_url(lk, slug)}">'
           for lk, slug in pair.items()]
    out.append(f'<link rel="alternate" hreflang="x-default" href="{legal_url("es", pair["es"])}">')
    return "\n".join(out)

def legal_links(langkey, home):
    L = LEGAL[langkey]
    items = " &middot; ".join(
        f'<a href="{L["base"]}{pg["slug"]}/">{esc(pg["h1"])}</a>'
        for pg in L["pages"].values())
    return f'  <a href="{home}">farmearaura.com</a> &middot; {items}<br>'

PAGE_TPL = (SRC / "page.tpl.html").read_text("utf-8")

def build_legal(langkey):
    L = LEGAL[langkey]
    owner = next(LOC[c] for c in ORDER if LEGAL_OF[c] == langkey)
    home = owner["path"]
    out = {}
    for key, pg in L["pages"].items():
        body = []
        for h, blocks in pg["sections"]:
            inner = []
            for b in blocks:
                if isinstance(b, dict):
                    inner.append('  <ul class="plain">\n' + "\n".join(
                        f"    <li>{x}</li>" for x in b["ul"]) + "\n  </ul>")
                else:
                    inner.append(f"  <p>{b}</p>")
            body.append(f"  <h2>{esc(h)}</h2>\n" + "\n".join(inner))
        canonical = legal_url(langkey, key)
        ld = {"@context": "https://schema.org", "@type": "WebPage",
              "@id": canonical + "#webpage", "url": canonical, "name": pg["h1"],
              "description": pg["desc"], "inLanguage": owner["lang"],
              "isPartOf": {"@id": f"{DOMAIN}/#website"},
              "dateModified": "2026-08-14",
              "publisher": {"@type": "Organization", "name": "farmearaura.com",
                            "url": DOMAIN + "/"}}
        out[key] = PAGE_TPL.format(
            lang=owner["lang"], title=esc(pg["title"]), desc=esc(pg["desc"]),
            canonical=canonical, hreflang=legal_hreflang(key, langkey),
            home=home, ctaNav=esc(owner["guide"]["ctaNav"]),
            homeLabel=esc(L["homeLabel"]), navLabel=esc(L["navLabel"]),
            h1=esc(pg["h1"]), updated=esc(L["updated"]), lead=pg["lead"],
            sections="\n\n".join(body),
            legalLinks=legal_links(langkey, home),
            footerNote=esc(owner["guide"]["footerNote"]),
            ld=json.dumps(ld, ensure_ascii=False, indent=2))
    return out

# ----------------------------------------------------------------- calculator
def app_faq_ld(l):
    faq = l["guide"]["faq"]
    ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": re.sub("<[^>]+>", "", q),
             "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}}
            for q, a in faq
        ],
    }
    return '<script type="application/ld+json">%s</script>' % json.dumps(
        ld, ensure_ascii=False, separators=(",", ":"))

# Enlaces internos: la seccion "about" de cada home menciona los duelos en
# texto plano; esto envuelve esas dos frases con un link a duelos/historia
# de esa MISMA locale (nunca cruza a otro pais). Las frases exactas varian
# por idioma, no por locale -- se repiten iguales en las 6-7 locales de cada
# grupo, verificado al escribirlas.
ABOUT_LINK_PHRASES = {
    "es": ("duelos de aura", "personajes históricos"),
    "pt": ("duelos de aura", "personagens históricos"),
    "en": ("aura duels", "historical figures"),
}

def app_about_linked(l):
    code = l["_code"]
    group = "pt" if l["lang"].startswith("pt") else ("en" if l["lang"].startswith("en") else "es")
    duelos_phrase, historia_phrase = ABOUT_LINK_PHRASES[group]
    text = l["app"]["about"][1]
    for phrase, key in ((duelos_phrase, "duelos"), (historia_phrase, "historia")):
        if phrase not in text:
            sys.exit(f"[{code}] about-link phrase not found: {phrase}")
        text = text.replace(phrase, f'<a href="{nav_data.NAV_URLS[code][key]}">{phrase}</a>', 1)
    return text

def app_faq_html(l):
    faq = l["guide"]["faq"]
    return "\n".join(
        f'    <details{" open" if i == 0 else ""}><summary>{esc(q)}</summary>'
        f'<div class="a"><p>{a}</p></div></details>'
        for i, (q, a) in enumerate(faq)
    )

def build_app(l):
    h = (SRC / "app.html").read_text("utf-8")
    a = l["app"]
    canonical = DOMAIN + l["path"]

    # --- head ---
    h = h.replace('<html lang="es">', f'<html lang="{l["lang"]}">', 1)
    h = sub1(h, r'<nav class="nav">.*?</nav>',
             '<nav class="nav">' + nav_data.nav_html(l["_code"], "home") + '</nav>')
    h = h.replace('<a class="logo" href="/">', f'<a class="logo" href="{l["path"]}">', 1)
    h = sub1(h, r"<title>.*?</title>", f'<title>{esc(a["title"])}</title>')
    h = sub1(h, r'<meta name="description" content=".*?">',
             f'<meta name="description" content="{esc(a["desc"])}">')
    head_extra = (f'<link rel="canonical" href="{canonical}">\n' + hreflang("app") +
                  f'\n<meta property="og:locale" content="{l["lang"].replace("-", "_")}">' +
                  "\n" + app_faq_ld(l))
    h = h.replace("<title>", head_extra + "\n<title>", 1)

    # --- JS data blocks ---
    h = sub1(h, r"const MODES = \{.*?\n\};", "const MODES = " + jsobj(modes_js(l)) + ";")
    h = sub1(h, r"const Q = \{.*?\n\]\};", "const Q = "     + jsobj(l["questions"]) + ";")
    h = sub1(h, r"const TIERS = \[.*?\n\];", "const TIERS = " + jsobj(tiers_js(l)) + ";")

    # --- visible strings ---
    for old, new in [
        ("7 situaciones. Un número.", a["tag1"]),
        ("Tu aura real, sin filtros.", a["tag2"]),
        ("Tu nombre o @", a["nameLabel"]),
        ("Sin cuenta. Sin fotos. Sin guardar nada.", a["fine1"]),
        ("Todo pasa dentro de tu celular.", a["fine2"]),
        ("¿Qué es farmear aura?", a["guideLink"]),
        ('href="/que-es-farmear-aura/"', f'href="{a["guideHref"]}"'),
        ("Calcula la tuya en 7 preguntas", a["cardTagline"]),
        ("Calculadora<br>de Aura", f'{a["wordmark"][0]}<br>{a["wordmark"][1]}'),
        ("<!--LEGALLINKS-->", app_legal_links(l)),
        ("<!--LEGALLINKS2-->", app_legal_links(l)),
        ("Saqué ${fmt(S.score)} puntos de aura. Calcula la tuya en farmearaura.com",
         a["shareText"].replace("{score}", "${fmt(S.score)}")),
        ("Sobre farmearaura.com", a["aboutH2"]),
        ("farmearaura.com es una calculadora de puntos de aura: siete situaciones cotidianas, "
         "tres modos y un puntaje final que se convierte en una tarjeta para compartir. No hace "
         "falta cuenta, no se sube ninguna foto y no se guarda nada: todo el cálculo pasa "
         "adentro de tu celular.", a["about"][0]),
        ("Además del test, el sitio tiene duelos de aura: podés votar quién tiene más aura entre "
         "arquetipos cotidianos o entre personajes históricos, y mirar el ranking que arma la "
         "gente votando.", app_about_linked(l)),
        ("Preguntas frecuentes", a["faqH2"]),
        ("<!--FAQITEMS-->", app_faq_html(l)),
    ]:
        if old not in h:
            sys.exit(f"[{l['code']}] string not found in template: {old[:60]}")
        h = h.replace(old, new)
    return h

def app_legal_links(l):
    L = LEGAL[LEGAL_OF[l["_code"]]]
    return "<br>" + " &middot; ".join(
        f'<a href="{L["base"]}{pg["slug"]}/" style="color:#54476A">{esc(pg["h1"])}</a>'
        for pg in L["pages"].values())

def modes_js(l):
    return {k: {"ic": v["ic"], "name": v["name"], "desc": v["desc"],
                "color": ["cyan", "aura", "gold"][i]}
            for i, (k, v) in enumerate(l["modes"].items())}

def tiers_js(l):
    return [{"min": t[0], "rank": t[1], "name": t[2], "line": t[3], "c": t[4]}
            for t in l["tiers"]]

def jsobj(o):
    return json.dumps(o, ensure_ascii=False, indent=1)

def sub1(text, pattern, repl):
    new, n = re.subn(pattern, lambda m: repl, text, count=1, flags=re.S)
    if n != 1:
        sys.exit(f"pattern matched {n} times: {pattern[:50]}")
    return new

# ----------------------------------------------------------------- guide
def build_guide(l):
    g, a = l["guide"], l["app"]
    canonical = f'{DOMAIN}{l["path"]}{g["slug"]}/'
    hd = g["headings"]

    def ul(items):
        return '  <ul class="plain">\n' + "\n".join(
            f'    <li>{x}</li>' for x in items) + "\n  </ul>"

    # Secciones opcionales, locale-especificas, insertables en 3 puntos del
    # pipeline fijo (antes de origin / entre origin y ledger / despues de
    # lose). Cada entrada es [heading, [parrafos]]. Todas las locales sin
    # estas claves en su guide.json se comportan exactamente igual que antes
    # -- esto reemplaza el viejo mecanismo de un unico extraIntro/extraBody.
    def extra_blocks(key):
        return [(heading, "\n".join(f"  <p>{p}</p>" for p in paras))
                for heading, paras in g.get(key, [])]

    blocks = []                                   # (heading, html)
    blocks += extra_blocks("extras_pre")
    blocks.append((hd[len(blocks)], "\n".join(f"  <p>{p}</p>" for p in g["origin"])))
    blocks += extra_blocks("extras_mid")

    lh = g.get("ledgerHead", ["SITUACI&Oacute;N", "AURA"])
    ledger = ('  <p>%s</p>\n  <div class="ledger">\n'
              '    <div class="head"><span>%s</span><span>%s</span></div>\n' %
              (g["pointsIntro"], lh[0], lh[1]))
    ledger += "\n".join(
        f'    <div class="row {d}"><span>{esc(t)}</span><span class="v">{v}</span></div>'
        for t, v, d in g["ledger"])
    ledger += f'\n  </div>\n  <p>{g["pointsOutro"]}</p>'
    blocks.append((hd[len(blocks)], ledger))

    blocks.append((hd[len(blocks)], f'  <p>{g["rulesIntro"]}</p>\n' +
                   ul(f'<strong>{esc(b)}</strong> {t}' for b, t in g["rules"])))
    blocks.append((hd[len(blocks)], f'  <p>{g["loseIntro"]}</p>\n' + ul(esc(x) for x in g["lose"])))

    blocks += extra_blocks("extras_post")

    blocks.append((hd[-2], '  <dl class="glo">\n' + "\n".join(
        f'    <dt>{esc(t)}</dt><dd>{d}</dd>' for t, d in g["glossary"]) + "\n  </dl>"))

    faq = "\n".join(
        f'  <details{" open" if i == 0 else ""}><summary>{esc(q)}</summary>'
        f'<div class="a"><p>{ans}</p></div></details>'
        for i, (q, ans) in enumerate(g["faq"]))
    blocks.append((hd[-1], faq))

    if len(blocks) != len(hd):
        sys.exit(f'[{l["code"]}] {len(hd)} headings but {len(blocks)} sections')

    toc = '    <ol>\n' + "\n".join(
        f'      <li><a href="#s{i+1}">{esc(h)}</a></li>' for i, (h, _) in enumerate(blocks)
    ) + "\n    </ol>"
    sections = "\n\n".join(
        f'  <h2 id="s{i+1}">{esc(h)}</h2>\n{body}' for i, (h, body) in enumerate(blocks))

    code = l["_code"]
    NL, NU = nav_data.NAV_LABELS[code], nav_data.NAV_URLS[code]
    related_links = [
        f'    <a href="{NU["duelos"]}">{esc(NL["duelos"])}</a>',
        f'    <a href="{NU["historia"]}">{esc(NL["historia"])}</a>',
    ]
    if "famosos" in NU:
        related_links.append(f'    <a href="{NU["famosos"]}">{esc(NL["famosos"])}</a>')
    for label, url in g.get("related_extra", []):
        related_links.append(f'    <a href="{url}">{esc(label)}</a>')
    related = "\n".join(related_links)

    srcs = g.get("sources", [
        "BBC &mdash; entrevista con Rayyan Arkan Dikha sobre el origen del baile.",
        'Wikipedia &mdash; <a href="https://en.wikipedia.org/wiki/Aura_farming" '
        'rel="nofollow noopener" target="_blank">Aura farming</a>.',
        "Infobae y El Heraldo de M&eacute;xico &mdash; cobertura en espa&ntilde;ol del Pacu Jalur."])

    return GUIDE_TPL.format(
        lang=l["lang"], title=esc(g["title"]), desc=esc(g["desc"]),
        canonical=canonical, hreflang=hreflang("guide"),
        oglocale=l["lang"].replace("-", "_"), home=l["path"],
        h1=esc(g["h1"]), answer=g["answer"],
        meta=g.get("meta", "Actualizado: agosto de 2026 &middot; Lectura: 5 min"),
        homeLabel=esc(g.get("homeLabel", "Inicio")),
        tocLabel=esc(g.get("tocLabel", "EN ESTA P&Aacute;GINA")).replace("&amp;", "&"),
        toc=toc, sections=sections, related=related,
        sourcesH=esc(g.get("sourcesH", "Fuentes")),
        sources="\n".join(f"    <li>{x}</li>" for x in srcs),
        promoK=esc(g["promoK"]), promoP=esc(g["promoP"]), promoBtn=esc(g["promoBtn"]),
        ctaNav=esc(g["ctaNav"]), guideLink=esc(a["guideLink"]),
        footerNote=esc(g["footerNote"]), ld=json.dumps(schema(l), ensure_ascii=False, indent=2),
        legalLinks=legal_links(LEGAL_OF[l["_code"]], l["path"]),
    )

def schema(l):
    g = l["guide"]
    base = f'{DOMAIN}{l["path"]}'
    page = f'{base}{g["slug"]}/'
    return {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "@id": f"{DOMAIN}/#website", "url": DOMAIN + "/",
         "name": "farmearaura.com", "inLanguage": l["lang"]},
        {"@type": "WebApplication", "@id": f"{base}#app", "url": base,
         "name": "Calculadora de Puntos de Aura", "applicationCategory": "GameApplication",
         "operatingSystem": "Any", "browserRequirements": "Requiere JavaScript",
         "inLanguage": l["lang"], "isAccessibleForFree": True,
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}},
        {"@type": "BreadcrumbList", "@id": f"{page}#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": base},
            {"@type": "ListItem", "position": 2, "name": g["h1"], "item": page}]},
        {"@type": "DefinedTermSet", "@id": f"{page}#glosario",
         "name": "Glosario del aura farming", "inLanguage": l["lang"],
         "hasDefinedTerm": [
             {"@type": "DefinedTerm", "@id": f"{page}#termino",
              "name": g["headTerm"], "alternateName": ["aura farming", "farmear aura"],
              "description": re.sub("<[^>]+>", "", g["answer"]),
              "inDefinedTermSet": f"{page}#glosario"},
             {"@type": "DefinedTerm", "@id": f"{page}#puntos-de-aura",
              "name": "Puntos de aura", "alternateName": ["aura points"],
              "description": re.sub("<[^>]+>", "", g["glossary"][1][1]),
              "inDefinedTermSet": f"{page}#glosario"},
             {"@type": "DefinedTerm", "@id": f"{page}#aura-negativa",
              "name": "Aura negativa", "alternateName": ["bancarrota de aura"],
              "description": re.sub("<[^>]+>", "", g["glossary"][2][1]),
              "inDefinedTermSet": f"{page}#glosario"}]},
        {"@type": "Article", "@id": f"{page}#article",
         "isPartOf": {"@id": f"{DOMAIN}/#website"}, "headline": g["h1"],
         "description": g["desc"], "inLanguage": l["lang"],
         "datePublished": "2026-08-14", "dateModified": "2026-08-14",
         "author": {"@type": "Organization", "name": "farmearaura.com", "url": DOMAIN + "/"},
         "publisher": {"@type": "Organization", "name": "farmearaura.com", "url": DOMAIN + "/"},
         "about": {"@id": f"{page}#termino"},
         "mentions": [{"@type": "Thing", "name": "Pacu Jalur",
                       "location": {"@type": "Place", "name": "Riau, Indonesia"}}]},
        {"@type": "FAQPage", "@id": f"{page}#faq",
         "isPartOf": {"@id": f"{page}#article"}, "inLanguage": l["lang"],
         "mainEntity": [{"@type": "Question", "name": q,
                         "acceptedAnswer": {"@type": "Answer",
                                            "text": re.sub("<[^>]+>", "", a)}}
                        for q, a in g["faq"]]},
    ]}

GUIDE_TPL = (SRC / "guide.tpl.html").read_text("utf-8") if (SRC / "guide.tpl.html").exists() else ""

# ----------------------------------------------------------------- crawl files
def build_sitemap():
    X = 'xmlns:xhtml="http://www.w3.org/1999/xhtml"'
    def alts(kind):
        def u(l):
            return DOMAIN + l["path"] if kind == "app" else f'{DOMAIN}{l["path"]}{l["guide"]["slug"]}/'
        rows = [f'    <xhtml:link rel="alternate" hreflang="{LOC[c]["code"]}" href="{u(LOC[c])}"/>'
                for c in ORDER]
        rows.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{u(DEFAULT)}"/>')
        return "\n".join(rows)
    urls = []
    for kind in ("app", "guide"):
        for c in ORDER:
            l = LOC[c]
            loc = DOMAIN + l["path"] if kind == "app" else f'{DOMAIN}{l["path"]}{l["guide"]["slug"]}/'
            urls.append(f'  <url>\n    <loc>{loc}</loc>\n{alts(kind)}\n'
                        f'    <lastmod>2026-08-14</lastmod>\n'
                        f'    <priority>{"1.0" if kind == "app" else "0.8"}</priority>\n  </url>')
    for pair in LEGAL_PAIRS:
        legal_urls = {lk: legal_url(lk, slug) for lk, slug in pair.items()}
        alt = "\n".join(
            f'    <xhtml:link rel="alternate" hreflang="{lk}" href="{u}"/>'
            for lk, u in legal_urls.items())
        alt += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{legal_urls["es"]}"/>'
        for u in legal_urls.values():
            urls.append(f'  <url>\n    <loc>{u}</loc>\n{alt}\n'
                        f'    <lastmod>2026-08-14</lastmod>\n'
                        f'    <priority>0.3</priority>\n  </url>')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" {X}>\n'
            + "\n".join(urls) + "\n</urlset>\n")

ROBOTS = f"""User-agent: *
Allow: /

User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Google-Extended
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
"""

# /ar/ is not a real page — Argentina is the root. 301 anyone who links it.
REDIRECTS = """/ar/                     /                         301
/ar/que-es-farmear-aura/ /que-es-farmear-aura/     301
/es/que-es-farmear-aura/ /es/aura-farming/         301
/pt/*                    /br/:splat                301
/br/aura-farming/        /br/o-que-e-farmar-aura/  301
"""

def build_llms():
    U = nav_data.NAV_URLS
    REGIONES = [("ar", "Argentina"), ("mx", "México"), ("es", "España"),
                ("br", "Brasil (português)"), ("cl", "Chile"), ("pe", "Perú"),
                ("co", "Colombia"), ("us", "United States (English)"),
                ("esus", "Estados Unidos (español)")]
    calculadora = "\n".join(
        f"- {label}{' (predeterminada)' if c == 'ar' else ''}: {U[c]['home']} · "
        f"guía: {DOMAIN}{LOC[c]['path']}{LOC[c]['guide']['slug']}/"
        for c, label in REGIONES
    )
    duelos = "\n".join(
        f"- {label}: {U[c]['duelos']} · ranking: {U[c]['duelos_ranking']} · "
        f"historial: {U[c]['duelos_historial']}"
        for c, label in REGIONES
    )
    historicos = "\n".join(
        f"- {label}: {U[c]['historia']} · ranking: {U[c]['historia_ranking']}"
        for c, label in REGIONES
    )
    return f"""# farmearaura.com

> Calculadora de puntos de aura, duelos de aura y guía de referencia sobre el aura
> farming, en español y portugués.

## Calculadora (test de 7 preguntas)
{calculadora}

## Duelos de aura (arquetipos cotidianos, con modismos locales por región)
{duelos}

## Duelos históricos (personajes de la historia, por región)
{historicos}

## Definición canónica
Farmear aura (en inglés, aura farming) significa acumular puntos imaginarios de carisma
mediante acciones que proyectan calma y seguridad sin esfuerzo aparente. Es jerga de
internet popularizada en TikTok; no guarda relación con el aura del esoterismo ni con
la migraña con aura.

## Definição canônica (pt-BR)
Farmar aura significa acumular pontos imaginários de carisma por meio de ações que
transmitem calma e segurança sem esforço aparente. É gíria de internet popularizada
no TikTok. O "campeonato de farmar aura" é uma disputa informal de poses, sem
organização oficial.

## Notas
Contenido de humor. Los puntos de aura no existen como medida real. Los rankings de
duelos se deciden por votos de la comunidad (sistema Elo), no por hechos verificables.
El test funciona en el navegador: no requiere cuenta, no admite fotos y no almacena datos.
"""

# ----------------------------------------------------------------- run
def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    for f in (SRC / "static").iterdir():
        shutil.copy2(f, DIST / f.name)
    print("  static -> favicon.svg, favicon.ico, apple-touch-icon.png, icon-192.png, "
          "icon-512.png, site.webmanifest")
    for c in ORDER:
        l = LOC[c]
        appdir = DIST / l["path"].strip("/")
        appdir.mkdir(parents=True, exist_ok=True)
        (appdir / "index.html").write_text(build_app(l), "utf-8")
        gdir = appdir / l["guide"]["slug"]
        gdir.mkdir(parents=True, exist_ok=True)
        (gdir / "index.html").write_text(build_guide(l), "utf-8")
        print(f"  {l['code']:6} -> {l['path']} + {l['path']}{l['guide']['slug']}/")
    for langkey in ("es", "pt", "en"):
        for key, html in build_legal(langkey).items():
            slug = LEGAL[langkey]["pages"][key]["slug"]
            d = DIST / (LEGAL[langkey]["base"].strip("/")) / slug
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(html, "utf-8")
        print(f"  legal/{langkey} -> {LEGAL[langkey]['base']}*")
    (DIST / "sitemap.xml").write_text(build_sitemap(), "utf-8")
    (DIST / "robots.txt").write_text(ROBOTS, "utf-8")
    (DIST / "_redirects").write_text(REDIRECTS, "utf-8")
    (DIST / "llms.txt").write_text(build_llms(), "utf-8")
    print("build ok ->", DIST)

if __name__ == "__main__":
    main()
