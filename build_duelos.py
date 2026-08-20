#!/usr/bin/env python3
"""
Genera el modulo de duelos dentro de dist/ sin tocar build.py.

    python3 build.py            # el sitio de siempre
    python3 build_duelos.py     # agrega /duelos/, /duelos/ranking/, /duelos/historial/

Tambien escribe seed.sql (para cargar los candidatos en D1) y suma las tres
URLs a dist/sitemap.xml si ese archivo existe.
"""

import json
import re
from pathlib import Path

import nav_data

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
GA4_ID = "G-XHZ0MM619V"   # dejalo en "" para no cargar analytics en estas paginas

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


def nav_html(actual):
    return nav_data.nav_html("ar", NAV_CURRENT[actual])


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
      <p><a href="{{HOME}}">{{SEO_LINK}}</a></p>
    </section>
"""

MAIN_RANKING = """
    <ol class="tabla skeleton" id="tabla"></ol>
    <section class="seo">
      <p><a href="{{VOTAR_URL}}">Votá vos y movelo.</a></p>
    </section>
"""

MAIN_HISTORIAL = """
    <ul class="feed skeleton" id="feed"></ul>
    <section class="seo">
      <p><a href="{{VOTAR_URL}}">Sumá tu duelo.</a></p>
    </section>
"""


def build():
    L = json.loads((ROOT / "locales" / "duelos-ar.json").read_text(encoding="utf-8"))
    tpl = (SRC / "duelos.tpl.html").read_text(encoding="utf-8")
    css = (SRC / "duelos.css").read_text(encoding="utf-8")
    js = (SRC / "duelos.js").read_text(encoding="utf-8")
    base = L["base"].rstrip("/")
    home = base + "/"
    votar_url = base + "/" + L["votar"]["slug"]

    paginas = [
        ("votar", L["votar"], MAIN_VOTAR, {
            "SEO_H2": esc(L["votar"]["seo_h2"]),
            "SEO_P": esc(L["votar"]["seo_p"]),
            "SEO_LINK": esc(L["votar"]["seo_link"]),
            "HOME": home,
        }, {"cta": L["votar"]["cta"], "robo": L["votar"]["robo"],
            "de_aura": L["votar"]["de_aura"]}),
        ("ranking", L["ranking"], MAIN_RANKING, {"VOTAR_URL": votar_url},
         {"vacio": L["ranking"]["vacio"]}),
        ("historial", L["historial"], MAIN_HISTORIAL, {"VOTAR_URL": votar_url},
         {"vacio": L["historial"]["vacio"], "robo": L["votar"]["robo"],
          "de_aura": L["votar"]["de_aura"]}),
    ]

    urls = []
    for key, page, main_tpl, main_vars, textos in paginas:
        canonical = base + "/" + page["slug"]
        main = main_tpl
        for k, v in main_vars.items():
            main = main.replace("{{%s}}" % k, v)

        cfg = {
            "pagina": key,
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
            ("CSS", css),
            ("JSONLD", jsonld(L, page, canonical)),
            ("HOME", home),
            ("NAV", nav_html(key)),
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

    # seed.sql
    filas = ",\n".join(
        "  ('%s', %d)" % (c["id"].replace("'", "''"), L["aura_inicial"])
        for c in L["candidatos"]
    )
    (ROOT / "seed.sql").write_text(
        "-- generado por build_duelos.py\n"
        "INSERT OR IGNORE INTO candidatos (id, aura) VALUES\n%s;\n" % filas,
        encoding="utf-8",
    )
    print("  -> seed.sql (%d candidatos)" % len(L["candidatos"]))

    # sitemap
    sm = DIST / "sitemap.xml"
    if sm.exists():
        xml = sm.read_text(encoding="utf-8")
        nuevas = [u for u in urls if "<loc>%s</loc>" % u not in xml]
        if nuevas:
            bloque = "".join(
                "<url><loc>%s</loc><changefreq>hourly</changefreq>"
                "<priority>0.8</priority></url>\n" % u for u in nuevas
            )
            xml = re.sub(r"</urlset>", bloque + "</urlset>", xml, count=1)
            sm.write_text(xml, encoding="utf-8")
            print("  -> sitemap.xml (+%d URLs)" % len(nuevas))


if __name__ == "__main__":
    print("Construyendo duelos...")
    build()
    print("Listo.")
