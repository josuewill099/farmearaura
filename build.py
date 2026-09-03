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
from datetime import date

import nav_data

ROOT   = pathlib.Path(__file__).parent
SRC    = ROOT / "src"
DIST   = ROOT / "dist"
DOMAIN = "https://farmearaura.com"
ORDER  = ["ar", "mx", "es", "br", "cl", "pe", "co", "us", "esus", "uy", "pt", "ec", "ve"]    # ar first = default
GENERIC = {"es": "ar", "pt": "br", "en": "us"}   # bare language code -> owning locale
TODAY  = date.today().isoformat()   # sitemap <lastmod> for this build -- shared with
                                     # build_articles.py/build_duelos.py/build_historia.py/
                                     # build_famosos.py so every sitemap entry from a given
                                     # deploy carries the same real date instead of a
                                     # hand-edited constant that goes stale.

# Mismo tag que build_duelos.py/build_historia.py/build_famosos.py -- antes
# solo esos tres builders lo cargaban; la calculadora, la guia y las
# paginas legales quedaban fuera de Analytics por completo.
GA4_ID = "G-XHZ0MM619V"   # dejalo en "" para no cargar analytics en estas paginas
ANALYTICS = (
    '<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>\n'
    "<script>window.dataLayer=window.dataLayer||[];"
    "function gtag(){dataLayer.push(arguments);}"
    'gtag("js",new Date());gtag("config","%s");</script>'
)
analytics_tag = (ANALYTICS % (GA4_ID, GA4_ID)) if GA4_ID else ""

def load(code):
    return json.loads((ROOT / "locales" / f"{code}.json").read_text("utf-8"))

LOC = {c: load(c) for c in ORDER}
LEGAL = {k: json.loads((ROOT / "locales" / f"legal-{k}.json").read_text("utf-8"))
         for k in ("es", "pt", "en")}
LEGAL_OF = {"ar": "es", "mx": "es", "es": "es", "br": "pt",
            "cl": "es", "pe": "es", "co": "es", "us": "en",
            "esus": "es", "uy": "es", "pt": "pt", "ec": "es", "ve": "es"}   # locale -> legal language
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
    return f'  <a href="{home}">farmearaura.com</a> &middot; {items} &middot; {nav_data.SOCIAL_LINKS}<br>'

PAGE_TPL = (SRC / "page.tpl.html").read_text("utf-8")

# Privacidad y cookies van noindex -- son paginas de compliance, no
# contenido que deba competir por rankear. Sobre nosotros/contacto se
# quedan indexables. Las claves varian por idioma (privacidad/privacy/
# privacidade) pero "cookies" es igual en las tres.
NOINDEX_LEGAL = {"privacidad", "privacy", "privacidade", "cookies"}


def build_legal(langkey):
    L = LEGAL[langkey]
    owner = next(LOC[c] for c in ORDER if LEGAL_OF[c] == langkey)
    home = owner["path"]
    out = {}
    for key, pg in L["pages"].items():
        robots = "noindex,follow" if key in NOINDEX_LEGAL else "index,follow"
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
            analytics=analytics_tag, robots=robots,
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
    og_image = f'{DOMAIN}/og-{l["_code"]}.jpg'
    h = h.replace('<meta property="og:title" content="Calculadora de Puntos de Aura">',
                  f'<meta property="og:title" content="{esc(a["title"])}">', 1)
    h = h.replace('<meta property="og:description" content="7 preguntas. Un número. Tu aura real.">',
                  f'<meta property="og:description" content="{esc(a["desc"])}">', 1)
    head_extra = (f'<link rel="canonical" href="{canonical}">\n' + hreflang("app") +
                  f'\n<meta property="og:locale" content="{l["lang"].replace("-", "_")}">'
                  f'\n<meta property="og:url" content="{canonical}">'
                  f'\n<meta property="og:image" content="{og_image}">'
                  '\n<meta property="og:image:width" content="1200">'
                  '\n<meta property="og:image:height" content="630">'
                  '\n<meta name="twitter:card" content="summary_large_image">'
                  f'\n<meta name="twitter:image" content="{og_image}">'
                  "\n" + app_faq_ld(l))
    h = h.replace("<title>", head_extra + "\n<title>", 1)
    duelos_url = nav_data.NAV_URLS[l["_code"]]["duelos"]
    spec_rules = ('<script type="speculationrules">' +
                  json.dumps({"prefetch": [{"source": "list", "urls": [duelos_url],
                                             "eagerness": "moderate"}]}) +
                  "</script>")
    h = h.replace("</head>", spec_rules + "\n</head>", 1)

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
        ("<!--LEGALLINKS2-->", app_legal_links(l)),
        ("<!--DUELCARDS-->", app_duel_cards(l)),
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
    h = h.replace("<!--ANALYTICS-->", analytics_tag)
    return h

def app_legal_links(l):
    L = LEGAL[LEGAL_OF[l["_code"]]]
    items = " &middot; ".join(
        f'<a href="{L["base"]}{pg["slug"]}/" style="color:#54476A">{esc(pg["h1"])}</a>'
        for pg in L["pages"].values())
    social = (
        '<a href="https://www.facebook.com/farmearauracom" style="color:#54476A" rel="noopener" target="_blank">Facebook</a>'
        ' &middot; '
        '<a href="https://www.instagram.com/farmear_aura_com" style="color:#54476A" rel="noopener" target="_blank">Instagram</a>'
    )
    return "<br>" + items + " &middot; " + social

# Tarjetas de duelos que aparecen debajo del fineprint de la calculadora,
# con el mismo look que .mode -- reusan nav_data (labels/URLs ya existen
# por locale, asi que esto no pide ningun campo nuevo en los JSON).
DUEL_CARD_DESC = {
    "es": {"duelos": "Arquetipos cotidianos, cara a cara",
           "historia": "Personajes históricos, cara a cara",
           "famosos": "Famosos, cara a cara"},
    "pt": {"duelos": "Arquétipos do dia a dia, cara a cara",
           "historia": "Personagens históricos, cara a cara",
           "famosos": "Famosos, cara a cara"},
    "en": {"duelos": "Everyday archetypes, head to head",
           "historia": "Historical figures, head to head",
           "famosos": "Celebrities, head to head"},
}
DUEL_CARD_ICON = {"duelos": "⚔️", "historia": "🏛️", "famosos": "🌟"}

def app_duel_cards(l):
    code = l["_code"]
    U, L = nav_data.NAV_URLS[code], nav_data.NAV_LABELS[code]
    lang = "pt" if l["lang"].startswith("pt") else "en" if l["lang"].startswith("en") else "es"
    desc = DUEL_CARD_DESC[lang]
    return "".join(
        f'<a class="mode" href="{U[key]}">'
        f'<span class="ic">{DUEL_CARD_ICON[key]}</span>'
        f'<span><span class="t">{esc(L[key].upper())}</span><span class="d">{esc(desc[key])}</span></span>'
        f'<span class="go">▶</span></a>'
        for key in ("duelos", "historia", "famosos"))

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
        ogimage=f'{DOMAIN}/og-{l["_code"]}.jpg',
        h1=esc(g["h1"]), answer=g["answer"],
        meta=g.get("meta", "Actualizado: agosto de 2026 · Lectura: 5 min"),
        homeLabel=esc(g.get("homeLabel", "Inicio")),
        tocLabel=esc(g.get("tocLabel", "EN ESTA P&Aacute;GINA")).replace("&amp;", "&"),
        quizWidget="", analytics=analytics_tag, toc=toc, sections=sections, related=related,
        sourcesH=esc(g.get("sourcesH", "Fuentes")),
        sources="\n".join(f"    <li>{x}</li>" for x in srcs),
        promoK=esc(g["promoK"]), promoP=esc(g["promoP"]), promoBtn=esc(g["promoBtn"]),
        promoUrl=l["path"],
        ctaNav=esc(g["ctaNav"]), guideLink=esc(a["guideLink"]),
        navblock=f'<a class="cta" href="{l["path"]}">{esc(g["ctaNav"])}</a>',
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

# ------------------------------------------------------------------ seasonal
# locales/seasonal-{loc}.json: calendario de eventos estacionales por mercado
# (ver el analisis de contenido estacional, agosto 2026 -- back-to-school,
# Carnaval, Enem, Dia de Muertos, etc. son eventos DISTINTOS por mercado, no
# una sola pagina traducida). Cada build imprime lo que vence en los proximos
# 30 dias para no perder una ventana por estar metido en otra cosa.
def check_seasonal():
    today = date.today()
    for f in sorted(ROOT.glob("locales/seasonal-*.json")):
        loc = f.stem.replace("seasonal-", "")
        events = json.loads(f.read_text("utf-8"))["events"]
        for ev in events:
            pub = date.fromisoformat(ev["publish_date"])
            happens = date.fromisoformat(ev["event_date"])
            if happens < today or ev.get("status") == "done":
                continue
            days_to_pub = (pub - today).days
            if days_to_pub <= 30:
                flag = "OVERDUE" if days_to_pub < 0 else "DUE"
                print(f"  [seasonal:{flag}] {loc} '{ev['name']}' -- publish by {ev['publish_date']} "
                      f"(event {ev['event_date']}, status={ev.get('status', '?')}) -> {ev['url']}")

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
                        f'    <lastmod>{TODAY}</lastmod>\n  </url>')
    for pair in LEGAL_PAIRS:
        # privacidad/cookies se sirven con robots noindex (ver build_legal()),
        # asi que no van al sitemap: enviarlas daba "Submitted URL marked
        # noindex" en Search Console.
        if any(slug in NOINDEX_LEGAL for slug in pair.values()):
            continue
        legal_urls = {lk: legal_url(lk, slug) for lk, slug in pair.items()}
        alt = "\n".join(
            f'    <xhtml:link rel="alternate" hreflang="{lk}" href="{u}"/>'
            for lk, u in legal_urls.items())
        alt += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{legal_urls["es"]}"/>'
        for u in legal_urls.values():
            urls.append(f'  <url>\n    <loc>{u}</loc>\n{alt}\n'
                        f'    <lastmod>{TODAY}</lastmod>\n  </url>')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" {X}>\n'
            + "\n".join(urls) + "\n</urlset>\n")

# /api/* son los endpoints de voto/estado que duelos.js/historia.js/famosos.js
# piden por fetch() en cada pagina interactiva -- puro JSON de puntajes en
# vivo, sin contenido indexable (eso ya esta en el HTML estatico servido
# sin JS). Bloquearlo no le saca nada a la indexacion, pero le devuelve al
# crawler presupuesto de rastreo que antes se iba en JSON: Googlebot
# renderiza cada pagina de duelo con Chrome headless para su "segunda ola"
# de indexacion, lo que dispara esos fetch() y contaba como rastreo de
# JSON en vez de HTML.
ROBOTS = f"""User-agent: *
Allow: /
Disallow: /api/

User-agent: GPTBot
Allow: /
Disallow: /api/
User-agent: OAI-SearchBot
Allow: /
Disallow: /api/
User-agent: PerplexityBot
Allow: /
Disallow: /api/
User-agent: ClaudeBot
Allow: /
Disallow: /api/
User-agent: Google-Extended
Allow: /
Disallow: /api/

Sitemap: {DOMAIN}/sitemap.xml
"""

SECURITY_TXT = """Contact: mailto:hola@farmearaura.com
Expires: 2027-08-31T23:59:59.000Z
Preferred-Languages: es, pt, en
Canonical: https://farmearaura.com/.well-known/security.txt
"""

ADS_TXT = "google.com, pub-9154720924448333, DIRECT, f08c47fec0942fa0\n"

# /ar/ is not a real page — Argentina is the root. 301 anyone who links it.
REDIRECTS = """/ar/                     /                         301
/ar/que-es-farmear-aura/ /que-es-farmear-aura/     301
/es/que-es-farmear-aura/ /es/aura-farming/         301
/br/aura-farming/        /br/o-que-e-farmar-aura/  301
/us/duels/historial/     /us/duels/recent/         301
"""

# Todo el JS/CSS del sitio va inline en el HTML (no hay /assets/ propio
# todavia), asi que script-src/style-src necesitan 'unsafe-inline' por
# ahora. Las tipografias ya son autohospedadas (/fonts/), asi que
# fonts.googleapis.com/fonts.gstatic.com salieron de la CSP. Report-Only:
# no bloquea nada, solo deja ver violaciones en la consola del navegador.
HEADERS = """/*
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
  Cross-Origin-Opener-Policy: same-origin
  Content-Security-Policy-Report-Only: default-src 'self'; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self' https://www.google-analytics.com https://*.google-analytics.com https://*.analytics.google.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'

/fonts/*
  Cache-Control: public, max-age=31536000, immutable

/og-*.jpg
  Cache-Control: public, max-age=604800
"""

def build_llms():
    U = nav_data.NAV_URLS
    REGIONES = [("ar", "Argentina"), ("mx", "México"), ("es", "España"),
                ("br", "Brasil (português)"), ("cl", "Chile"), ("pe", "Perú"),
                ("co", "Colombia"), ("us", "United States (English)"),
                ("esus", "Estados Unidos (español)"), ("uy", "Uruguay"),
                ("pt", "Portugal (português)"), ("ec", "Ecuador"), ("ve", "Venezuela")]
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
    shutil.copytree(SRC / "static", DIST, dirs_exist_ok=True)
    print("  static -> favicon.svg, favicon.ico, apple-touch-icon.png, icon-192.png, "
          "icon-512.png, site.webmanifest, og-*.jpg, fonts/*.woff2")
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
    (DIST / "ads.txt").write_text(ADS_TXT, "utf-8")
    (DIST / "_redirects").write_text(REDIRECTS, "utf-8")
    (DIST / "_headers").write_text(HEADERS, "utf-8")
    (DIST / ".well-known").mkdir(exist_ok=True)
    (DIST / ".well-known" / "security.txt").write_text(SECURITY_TXT, "utf-8")
    (DIST / "llms.txt").write_text(build_llms(), "utf-8")
    check_seasonal()
    print("build ok ->", DIST)

if __name__ == "__main__":
    main()
