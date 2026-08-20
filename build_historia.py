#!/usr/bin/env python3
"""
Duelos de aura entre personajes historicos, en las cuatro locales.

    python3 build.py && python3 build_duelos.py && python3 build_historia.py

Genera dos paginas por locale (votar + ranking), con hreflang reciproco entre
las cuatro, y seed-historia.sql para cargar las figuras en D1.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
LOCS = ["ar", "mx", "es", "br"]
GA4_ID = "G-XHZ0MM619V"   # "" para no cargar analytics en estas paginas

HREFLANG = {"ar": ["es-AR", "es", "x-default"], "mx": ["es-MX"],
            "es": ["es-ES"], "br": ["pt-BR"]}
OG = {"ar": "es_AR", "mx": "es_MX", "es": "es_ES", "br": "pt_BR"}

ANALYTICS = (
    '<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>\n'
    "<script>window.dataLayer=window.dataLayer||[];"
    "function gtag(){dataLayer.push(arguments);}"
    'gtag("js",new Date());gtag("config","%s");</script>'
)

MAIN_VOTAR = """
    <div class="arena">
      <button class="card" id="c0" type="button"></button>
      <div class="vs">VS</div>
      <button class="card" id="c1" type="button"></button>
    </div>
    <p class="resultado" id="resultado"></p>
    <div class="avance" id="avance" aria-hidden="true"></div>

    <section class="seo">
      <h2>{{SEO_H2}}</h2>
      <p>{{SEO_P}}</p>
      <p><a href="{{RANKING_URL}}">{{SEO_LINK}}</a></p>
    </section>
"""

MAIN_RANKING = """
    <ol class="tabla skeleton" id="tabla"></ol>
    <h2 class="feed-titulo">{{FEED_TITULO}}</h2>
    <ul class="feed skeleton" id="feed"></ul>
    <section class="seo">
      <p><a href="{{VOTAR_URL}}">{{LINK}}</a></p>
    </section>
"""


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def sin_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def cargar():
    return {
        loc: json.loads((ROOT / "locales" / ("historia-%s.json" % loc))
                        .read_text(encoding="utf-8"))
        for loc in LOCS
    }


def alternates(datos, tipo):
    clave = "slug_votar" if tipo == "votar" else "slug_ranking"
    out = []
    for loc in LOCS:
        L = datos[loc]
        url = L["base"].rstrip("/") + "/" + L[clave]
        for hl in HREFLANG[loc]:
            out.append('<link rel="alternate" hreflang="%s" href="%s">' % (hl, url))
    return "\n".join(out)


def nav_html(L, actual):
    base = L["base"].rstrip("/")
    items = [("calculadora", base + L["home"]),
             ("votar", base + "/" + L["slug_votar"]),
             ("ranking", base + "/" + L["slug_ranking"])]
    out = []
    for key, href in items:
        cur = ' aria-current="page"' if key == actual else ""
        out.append('<a href="%s"%s>%s</a>' % (href, cur, esc(L["nav"][key])))
    return "".join(out)


# Los otros duelos del sitio, para saltar de uno a otro desde cualquier pagina.
# El de arquetipos (unico, sin variantes por locale) mas los otros tres historia.
ARQUETIPOS_DUELO = ("🇦🇷", "arquetipos", "https://farmearaura.com/duelos/")
HISTORIA_DUELOS = {
    "ar": ("🇦🇷", "Historia AR", "https://farmearaura.com/duelos/historia/"),
    "mx": ("🇲🇽", "Historia MX", "https://farmearaura.com/mx/duelos/historia/"),
    "es": ("🇪🇸", "Historia ES", "https://farmearaura.com/es/duelos-de-aura/"),
    "br": ("🇧🇷", "Historia BR", "https://farmearaura.com/br/batalha-de-aura/"),
}


def duels_html(L, actual_loc):
    items = [(ARQUETIPOS_DUELO[0], esc(L["nav"]["arquetipos"]), ARQUETIPOS_DUELO[2])]
    for loc, (flag, label, href) in HISTORIA_DUELOS.items():
        if loc != actual_loc:
            items.append((flag, esc(label), href))
    return "".join(
        '<a href="%s"><span aria-hidden="true">%s</span>%s</a>' % (href, flag, label)
        for flag, label, href in items
    )


def jsonld(L, page, canonical, figuras):
    graph = [
        {"@type": "WebPage", "@id": canonical, "url": canonical,
         "name": sin_tags(page["h1"]), "description": page["description"],
         "inLanguage": L["locale"],
         "isPartOf": {"@type": "WebSite", "url": L["base"] + "/", "name": "Farmear Aura"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Farmear Aura",
             "item": L["base"] + L["home"]},
            {"@type": "ListItem", "position": 2, "name": sin_tags(page["h1"]),
             "item": canonical}]},
    ]
    if figuras:
        graph.append({
            "@type": "ItemList", "name": sin_tags(page["h1"]),
            "numberOfItems": len(figuras),
            "itemListOrder": "https://schema.org/ItemListUnordered",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1,
                 "item": {"@type": "Person", "name": f["nombre"], "description": f["oficio"]}}
                for i, f in enumerate(figuras)],
        })
    return '<script type="application/ld+json">%s</script>' % json.dumps(
        {"@context": "https://schema.org", "@graph": graph},
        ensure_ascii=False, separators=(",", ":"))


def build():
    datos = cargar()
    tpl = (SRC / "historia.tpl.html").read_text(encoding="utf-8")
    css = ((SRC / "duelos.css").read_text(encoding="utf-8") + "\n"
           + (SRC / "historia.css").read_text(encoding="utf-8"))
    js = (SRC / "historia.js").read_text(encoding="utf-8")

    alt = {"votar": alternates(datos, "votar"), "ranking": alternates(datos, "ranking")}
    urls = []

    for loc in LOCS:
        L = datos[loc]
        base = L["base"].rstrip("/")
        u_votar = base + "/" + L["slug_votar"]
        u_rank = base + "/" + L["slug_ranking"]

        paginas = [
            ("votar", L["votar"], L["slug_votar"], MAIN_VOTAR,
             {"SEO_H2": esc(L["votar"]["seo_h2"]),
              "SEO_P": esc(L["votar"]["seo_p"]),
              "SEO_LINK": esc(L["votar"]["seo_link"]),
              "RANKING_URL": u_rank},
             L["figuras"]),
            ("ranking", L["ranking"], L["slug_ranking"], MAIN_RANKING,
             {"FEED_TITULO": esc(L["ranking"]["feed_titulo"]),
              "LINK": esc(L["ranking"]["link"]),
              "VOTAR_URL": u_votar},
             None),
        ]

        for key, page, slug, main_tpl, main_vars, figuras in paginas:
            canonical = base + "/" + slug
            main = main_tpl
            for k, v in main_vars.items():
                main = main.replace("{{%s}}" % k, v)

            cfg = {"pagina": key, "loc": loc, "k": L["k"],
                   "aura_inicial": L["aura_inicial"], "numfmt": L["numfmt"],
                   "t": dict(L["t"], cta=L["votar"]["cta"],
                             vacio=L["ranking"]["vacio"]),
                   "figuras": L["figuras"]}

            html = tpl
            for k, v in [
                ("LANG", L["lang"]),
                ("TITLE", esc(page["title"])),
                ("DESC", esc(page["description"])),
                ("CANONICAL", canonical),
                ("ALTERNATES", alt[key]),
                ("OGLOCALE", OG[loc]),
                ("CSS", css),
                ("JSONLD", jsonld(L, page, canonical, figuras)),
                ("HOME", base + L["home"]),
                ("NAV", nav_html(L, key)),
                ("DUELS", duels_html(L, loc)),
                ("H1", page["h1"]),
                ("SUB", esc(page["sub"])),
                ("OFFLINE", esc(L["offline"])),
                ("MAIN", main),
                ("FOOTER", esc(L["footer"])),
                ("CONFIG", json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))),
                ("JS", js),
            ]:
                html = html.replace("{{%s}}" % k, v)

            html = html.replace("<!--ANALYTICS-->",
                                (ANALYTICS % (GA4_ID, GA4_ID)) if GA4_ID else "")

            out = DIST / slug / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(html, encoding="utf-8")
            urls.append(canonical)
            print("  ->", out.relative_to(ROOT), "(%.1f KB)" % (len(html) / 1024))

    # seed
    filas = []
    for loc in LOCS:
        for f in datos[loc]["figuras"]:
            filas.append("  ('%s', '%s', %d)" % (loc, f["id"].replace("'", "''"),
                                                 datos[loc]["aura_inicial"]))
    (ROOT / "seed-historia.sql").write_text(
        "-- generado por build_historia.py\n"
        "INSERT OR IGNORE INTO h_candidatos (loc, id, aura) VALUES\n%s;\n"
        % ",\n".join(filas), encoding="utf-8")
    print("  -> seed-historia.sql (%d filas)" % len(filas))

    # sitemap
    sm = DIST / "sitemap.xml"
    if sm.exists():
        xml = sm.read_text(encoding="utf-8")
        nuevas = [u for u in urls if "<loc>%s</loc>" % u not in xml]
        if nuevas:
            bloque = "".join(
                "<url><loc>%s</loc><changefreq>hourly</changefreq>"
                "<priority>0.8</priority></url>\n" % u for u in nuevas)
            xml = re.sub(r"</urlset>", bloque + "</urlset>", xml, count=1)
            sm.write_text(xml, encoding="utf-8")
            print("  -> sitemap.xml (+%d URLs)" % len(nuevas))


if __name__ == "__main__":
    print("Construyendo duelos historicos...")
    build()
    print("Listo.")
