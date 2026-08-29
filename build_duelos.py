#!/usr/bin/env python3
"""
Genera el modulo de duelos (arquetipos cotidianos) para las siete locales,
dentro de dist/ sin tocar build.py.

    python3 build.py            # el sitio de siempre
    python3 build_duelos.py     # agrega /duelos/, /mx/duelos/, /es/duelos/, ...

Tambien escribe seed.sql (para cargar los candidatos en D1, con su columna
loc) y suma las URLs a dist/sitemap.xml si ese archivo existe.
"""

import json
import re
from pathlib import Path

import nav_data

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
LOCS = ["ar", "mx", "es", "br", "cl", "pe", "co", "us", "esus", "uy"]
GA4_ID = "G-XHZ0MM619V"   # dejalo en "" para no cargar analytics en estas paginas

# ar vive en la raiz (nunca tuvo prefijo de pais); el resto cuelga de /{cc}/.
HOME = {"ar": "/", "mx": "/mx/", "es": "/es/", "br": "/br/",
        "cl": "/cl/", "pe": "/pe/", "co": "/co/", "us": "/us/", "esus": "/es-us/",
        "uy": "/uy/"}
HREFLANG = {"ar": ["es-AR", "es", "x-default"], "mx": ["es-MX"],
            "es": ["es-ES"], "br": ["pt-BR"],
            "cl": ["es-CL"], "pe": ["es-PE"], "co": ["es-CO"], "us": ["en-US", "en"],
            "esus": ["es-US"], "uy": ["es-UY"]}
OG = {"ar": "es_AR", "mx": "es_MX", "es": "es_ES", "br": "pt_BR", "us": "en_US",
      "cl": "es_CL", "pe": "es_PE", "co": "es_CO", "esus": "es_US", "uy": "es_UY"}

ANALYTICS = (
    '<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>\n'
    "<script>window.dataLayer=window.dataLayer||[];"
    "function gtag(){dataLayer.push(arguments);}"
    'gtag("js",new Date());gtag("config","%s");</script>'
)


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


# El menu (calculadora / duelos / duelos historicos) vive en nav_data.py,
# compartido con build.py y build_historia.py. "votar"/"ranking"/"historial"
# son las claves de pagina de este builder; nav_data usa sus propias claves
# ("duelos", "duelos_ranking", "duelos_historial") para marcar aria-current.
NAV_CURRENT = {"votar": "duelos", "ranking": "duelos_ranking", "historial": "duelos_historial"}


def nav_html(loc, actual):
    return nav_data.nav_html(loc, NAV_CURRENT[actual])


def jsonld(L, page, canonical):
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canonical,
                "url": canonical,
                "name": page["h1"],
                "description": page["description"],
                "inLanguage": L["locale"],
                "isPartOf": {"@type": "WebSite", "url": L["base"] + "/", "name": "Farmear Aura"},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Farmear Aura",
                     "item": L["base"] + "/"},
                    {"@type": "ListItem", "position": 2, "name": page["h1"], "item": canonical},
                ],
            },
        ],
    }
    return '<script type="application/ld+json">%s</script>' % json.dumps(
        data, ensure_ascii=False, separators=(",", ":")
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
      <p><a href="{{HOME}}">{{SEO_LINK}}</a> &middot; <a href="{{GUIDE_URL}}">{{GUIDE_LABEL}}</a>{{FAMOSOS_LINK}}</p>
    </section>
"""

MAIN_RANKING = """
    <ol class="tabla skeleton" id="tabla"></ol>
    <section class="seo">
      <p><a href="{{VOTAR_URL}}">{{RANKING_CTA}}</a></p>
    </section>
"""

MAIN_HISTORIAL = """
    <ul class="feed skeleton" id="feed"></ul>
    <section class="seo">
      <p><a href="{{VOTAR_URL}}">{{HISTORIAL_CTA}}</a></p>
    </section>
"""

# "Vota y movelo" / "Suma tu duelo": microcopy que el AR original tenia
# hardcodeada en voseo dentro de la plantilla. Al sumar mas locales no puede
# seguir hardcodeada -- ninguno de los duelos-{loc}.json trae un campo para
# esto, asi que vive aca en vez de pedirle una vuelta mas a cada archivo.
RANKING_CTA = {
    "ar": "Votá vos y movelo.", "mx": "Vota tú y muévelo.", "es": "Vota tú y muévelo.",
    "br": "Vote e mexa o ranking.", "cl": "Vota tú y muévelo.", "pe": "Vota tú y muévelo.",
    "co": "Vota tú y muévelo.", "us": "Cast your vote and move the needle.",
    "esus": "Vota tú y muévelo.", "uy": "Votá vos y movelo.",
}
HISTORIAL_CTA = {
    "ar": "Sumá tu duelo.", "mx": "Suma tu duelo.", "es": "Suma tu duelo.",
    "br": "Some o seu duelo.", "cl": "Suma tu duelo.", "pe": "Suma tu duelo.",
    "co": "Suma tu duelo.", "us": "Add your duel.", "esus": "Suma tu duelo.",
    "uy": "Sumá tu duelo.",
}

# Link contextual a famosos (celebridades del propio pais) desde la seccion
# SEO de la pagina de votar. nav_data.NAV_URLS ya tiene la URL correcta por
# locale -- se usa esa en vez de duplicarla aca.
FAMOSOS_LABEL = {
    "ar": "Duelos entre famosos", "mx": "Duelos entre famosos",
    "es": "Duelos entre famosos", "br": "Batalhas entre famosos",
    "cl": "Duelos entre famosos", "pe": "Duelos entre famosos",
    "co": "Duelos entre famosos", "us": "Celebrity duels",
    "esus": "Duelos entre famosos", "uy": "Duelos entre famosos",
}


def famosos_link(loc):
    return ' &middot; <a href="%s">%s</a>' % (
        nav_data.NAV_URLS[loc]["famosos"], esc(FAMOSOS_LABEL[loc]))


def cargar():
    return {
        loc: json.loads((ROOT / "locales" / ("duelos-%s.json" % loc))
                        .read_text(encoding="utf-8"))
        for loc in LOCS
    }


def alternates(datos, tipo):
    out = []
    for loc in LOCS:
        L = datos[loc]
        url = L["base"].rstrip("/") + "/" + L[tipo]["slug"]
        for hl in HREFLANG[loc]:
            out.append('<link rel="alternate" hreflang="%s" href="%s">' % (hl, url))
    return "\n".join(out)


def build():
    datos = cargar()
    tpl = (SRC / "duelos.tpl.html").read_text(encoding="utf-8")
    css = (SRC / "duelos.css").read_text(encoding="utf-8")
    js = (SRC / "duelos.js").read_text(encoding="utf-8")

    alt = {tipo: alternates(datos, tipo) for tipo in ("votar", "ranking", "historial")}
    urls = []

    for loc in LOCS:
        L = datos[loc]
        base = L["base"].rstrip("/")
        home = base + HOME[loc]
        votar_url = base + "/" + L["votar"]["slug"]

        paginas = [
            ("votar", L["votar"], MAIN_VOTAR, {
                "SEO_H2": esc(L["votar"]["seo_h2"]),
                "SEO_P": esc(L["votar"]["seo_p"]),
                "SEO_LINK": esc(L["votar"]["seo_link"]),
                "HOME": home,
                "GUIDE_URL": nav_data.GUIDE_URLS[loc],
                "GUIDE_LABEL": esc(nav_data.GUIDE_LABELS[loc]),
                "FAMOSOS_LINK": famosos_link(loc),
            }, {"cta": L["votar"]["cta"], "robo": L["votar"]["robo"],
                "de_aura": L["votar"]["de_aura"]}),
            ("ranking", L["ranking"], MAIN_RANKING,
             {"VOTAR_URL": votar_url, "RANKING_CTA": esc(RANKING_CTA[loc])},
             {"vacio": L["ranking"]["vacio"]}),
            ("historial", L["historial"], MAIN_HISTORIAL,
             {"VOTAR_URL": votar_url, "HISTORIAL_CTA": esc(HISTORIAL_CTA[loc])},
             {"vacio": L["historial"]["vacio"], "robo": L["votar"]["robo"],
              "de_aura": L["votar"]["de_aura"]}),
        ]

        for key, page, main_tpl, main_vars, textos in paginas:
            canonical = base + "/" + page["slug"]
            main = main_tpl
            for k, v in main_vars.items():
                main = main.replace("{{%s}}" % k, v)

            cfg = {
                "pagina": key,
                "loc": loc,
                "k": L["k"],
                "aura_inicial": L["aura_inicial"],
                "candidatos": L["candidatos"],
                "t": textos,
            }

            html = tpl
            for k, v in [
                ("LANG", L["lang"]),
                ("TITLE", esc(page["title"])),
                ("DESC", esc(page["description"])),
                ("CANONICAL", canonical),
                ("ALTERNATES", alt[key]),
                ("OGLOCALE", OG[loc]),
                ("CSS", css),
                ("JSONLD", jsonld(L, page, canonical)),
                ("HOME", home),
                ("NAV", nav_html(loc, key)),
                ("LEGALLINKS", nav_data.legal_links_html(loc, home)),
                ("H1", esc(page["h1"])),
                ("SUB", esc(page["sub"])),
                ("OFFLINE", esc(L["offline"])),
                ("MAIN", main),
                ("FOOTER", esc(L["footer"])),
                ("CONFIG", json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))),
                ("JS", js),
            ]:
                html = html.replace("{{%s}}" % k, v)

            html = html.replace(
                "<!--ANALYTICS-->", (ANALYTICS % (GA4_ID, GA4_ID)) if GA4_ID else ""
            )

            out = DIST / page["slug"] / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(html, encoding="utf-8")
            urls.append(canonical)
            print("  ->", out.relative_to(ROOT), "(%.1f KB)" % (len(html) / 1024))

    # seed.sql -- todas las locales juntas, con loc por fila
    filas = []
    for loc in LOCS:
        for c in datos[loc]["candidatos"]:
            filas.append("  ('%s', '%s', %d)" % (
                loc, c["id"].replace("'", "''"), datos[loc]["aura_inicial"]))
    (ROOT / "seed.sql").write_text(
        "-- generado por build_duelos.py\n"
        "INSERT OR IGNORE INTO candidatos (loc, id, aura) VALUES\n%s;\n" % ",\n".join(filas),
        encoding="utf-8",
    )
    print("  -> seed.sql (%d candidatos)" % len(filas))

    # sitemap
    sm = DIST / "sitemap.xml"
    if sm.exists():
        xml = sm.read_text(encoding="utf-8")
        nuevas = [u for u in urls if "<loc>%s</loc>" % u not in xml]
        if nuevas:
            bloque = "".join(
                "<url><loc>%s</loc><changefreq>daily</changefreq>"
                "<priority>0.8</priority></url>\n" % u for u in nuevas
            )
            xml = re.sub(r"</urlset>", bloque + "</urlset>", xml, count=1)
            sm.write_text(xml, encoding="utf-8")
            print("  -> sitemap.xml (+%d URLs)" % len(nuevas))


if __name__ == "__main__":
    print("Construyendo duelos...")
    build()
    print("Listo.")
