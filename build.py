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

ROOT   = pathlib.Path(__file__).parent
SRC    = ROOT / "src"
DIST   = ROOT / "dist"
DOMAIN = "https://farmearaura.com"
ORDER  = ["ar", "mx", "es", "br"]    # ar first = default
GENERIC = {"es": "ar", "pt": "br"}   # bare language code -> owning locale

def load(code):
    return json.loads((ROOT / "locales" / f"{code}.json").read_text("utf-8"))

LOC = {c: load(c) for c in ORDER}
LEGAL = {k: json.loads((ROOT / "locales" / f"legal-{k}.json").read_text("utf-8"))
         for k in ("es", "pt")}
LEGAL_OF = {"ar": "es", "mx": "es", "es": "es", "br": "pt"}   # locale -> legal language
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

# es <-> pt equivalents, so each legal page has a 2-locale hreflang cluster
LEGAL_PAIRS = [("privacidad", "privacidade"), ("cookies", "cookies"),
               ("sobre-nosotros", "sobre"), ("contacto", "contato")]

def legal_hreflang(pagekey, langkey):
    pair = next(p for p in LEGAL_PAIRS if p[0 if langkey == "es" else 1] == pagekey)
    es_u, pt_u = legal_url("es", pair[0]), legal_url("pt", pair[1])
    return "\n".join([
        f'<link rel="alternate" hreflang="es" href="{es_u}">',
        f'<link rel="alternate" hreflang="pt" href="{pt_u}">',
        f'<link rel="alternate" hreflang="x-default" href="{es_u}">'])

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
def build_app(l):
    h = (SRC / "app.html").read_text("utf-8")
    a = l["app"]
    canonical = DOMAIN + l["path"]

    # --- head ---
    h = h.replace('<html lang="es">', f'<html lang="{l["lang"]}">', 1)
    h = sub1(h, r"<title>.*?</title>", f'<title>{esc(a["title"])}</title>')
    h = sub1(h, r'<meta name="description" content=".*?">',
             f'<meta name="description" content="{esc(a["desc"])}">')
    head_extra = (f'<link rel="canonical" href="{canonical}">\n' + hreflang("app") +
                  f'\n<meta property="og:locale" content="{l["lang"].replace("-", "_")}">')
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
        ("<!--LEGALLINKS-->", app_legal_links(l)),
        ("Saqué ${fmt(S.score)} puntos de aura. Calcula la tuya en farmearaura.com",
         a["shareText"].replace("{score}", "${fmt(S.score)}")),
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

    blocks = []                                   # (heading, html)
    blocks.append((hd[0], "\n".join(f"  <p>{p}</p>" for p in g["origin"])))

    lh = g.get("ledgerHead", ["SITUACI&Oacute;N", "AURA"])
    ledger = ('  <p>%s</p>\n  <div class="ledger">\n'
              '    <div class="head"><span>%s</span><span>%s</span></div>\n' %
              (g["pointsIntro"], lh[0], lh[1]))
    ledger += "\n".join(
        f'    <div class="row {d}"><span>{esc(t)}</span><span class="v">{v}</span></div>'
        for t, v, d in g["ledger"])
    ledger += f'\n  </div>\n  <p>{g["pointsOutro"]}</p>'
    blocks.append((hd[1], ledger))

    blocks.append((hd[2], f'  <p>{g["rulesIntro"]}</p>\n' +
                   ul(f'<strong>{esc(b)}</strong> {t}' for b, t in g["rules"])))
    blocks.append((hd[3], f'  <p>{g["loseIntro"]}</p>\n' + ul(esc(x) for x in g["lose"])))

    if "extraIntro" in g:                          # optional locale-specific section
        blocks.append((hd[4], f'  <p>{g["extraIntro"]}</p>\n  <p>{g["extraBody"]}</p>'))

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
        toc=toc, sections=sections,
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
         "mentions": [{"@type": "Event", "name": "Pacu Jalur",
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
        es_u, pt_u = legal_url("es", pair[0]), legal_url("pt", pair[1])
        alt = (f'    <xhtml:link rel="alternate" hreflang="es" href="{es_u}"/>\n'
               f'    <xhtml:link rel="alternate" hreflang="pt" href="{pt_u}"/>\n'
               f'    <xhtml:link rel="alternate" hreflang="x-default" href="{es_u}"/>')
        for u in (es_u, pt_u):
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

LLMS = f"""# farmearaura.com

> Calculadora de puntos de aura y guía de referencia sobre el aura farming en español.

## Versiones por región
- Argentina (predeterminada): {DOMAIN}/ · guía: {DOMAIN}/que-es-farmear-aura/
- México: {DOMAIN}/mx/ · guía: {DOMAIN}/mx/que-es-farmear-aura/
- España: {DOMAIN}/es/ · guía: {DOMAIN}/es/aura-farming/
- Brasil (português): {DOMAIN}/br/ · guia: {DOMAIN}/br/o-que-e-farmar-aura/

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
Contenido de humor. Los puntos de aura no existen como medida real.
El test funciona en el navegador: no requiere cuenta, no admite fotos y no almacena datos.
"""

# ----------------------------------------------------------------- run
def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    for c in ORDER:
        l = LOC[c]
        appdir = DIST / l["path"].strip("/")
        appdir.mkdir(parents=True, exist_ok=True)
        (appdir / "index.html").write_text(build_app(l), "utf-8")
        gdir = appdir / l["guide"]["slug"]
        gdir.mkdir(parents=True, exist_ok=True)
        (gdir / "index.html").write_text(build_guide(l), "utf-8")
        print(f"  {l['code']:6} -> {l['path']} + {l['path']}{l['guide']['slug']}/")
    for langkey in ("es", "pt"):
        for key, html in build_legal(langkey).items():
            slug = LEGAL[langkey]["pages"][key]["slug"]
            d = DIST / (LEGAL[langkey]["base"].strip("/")) / slug
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(html, "utf-8")
        print(f"  legal/{langkey} -> {LEGAL[langkey]['base']}*")
    (DIST / "sitemap.xml").write_text(build_sitemap(), "utf-8")
    (DIST / "robots.txt").write_text(ROBOTS, "utf-8")
    (DIST / "_redirects").write_text(REDIRECTS, "utf-8")
    (DIST / "llms.txt").write_text(LLMS, "utf-8")
    print("build ok ->", DIST)

if __name__ == "__main__":
    main()
