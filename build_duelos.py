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
from datetime import date
from pathlib import Path

import nav_data

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
TODAY = date.today().isoformat()   # sitemap <lastmod> for this build
LOCS = ["ar", "mx", "es", "br", "cl", "pe", "co", "us", "esus", "uy", "pt", "ec", "ve", "cr", "gt", "bo"]
GA4_ID = "G-XHZ0MM619V"   # dejalo en "" para no cargar analytics en estas paginas

# ar vive en la raiz (nunca tuvo prefijo de pais); el resto cuelga de /{cc}/.
HOME = {"ar": "/", "mx": "/mx/", "es": "/es/", "br": "/br/",
        "cl": "/cl/", "pe": "/pe/", "co": "/co/", "us": "/us/", "esus": "/es-us/",
        "uy": "/uy/", "pt": "/pt/", "ec": "/ec/", "ve": "/ve/", "cr": "/cr/", "gt": "/gt/", "bo": "/bo/"}
HREFLANG = {"ar": ["es-AR", "es", "x-default"], "mx": ["es-MX"],
            "es": ["es-ES"], "br": ["pt-BR"],
            "cl": ["es-CL"], "pe": ["es-PE"], "co": ["es-CO"], "us": ["en-US", "en"],
            "esus": ["es-US"], "uy": ["es-UY"], "pt": ["pt-PT"], "ec": ["es-EC"],
            "ve": ["es-VE"], "cr": ["es-CR"], "gt": ["es-GT"], "bo": ["es-BO"]}
OG = {"ar": "es_AR", "mx": "es_MX", "es": "es_ES", "br": "pt_BR", "us": "en_US",
      "cl": "es_CL", "pe": "es_PE", "co": "es_CO", "esus": "es_US", "uy": "es_UY",
      "pt": "pt_PT", "ec": "es_EC", "ve": "es_VE", "cr": "es_CR", "gt": "es_GT", "bo": "es_BO"}

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
      <h2>{{RANKING_SEO_H2}}</h2>
      <p>{{RANKING_SEO_P}}</p>
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
    "pt": "Vota e mexe no ranking.", "ec": "Vota tú y muévelo.", "ve": "Vota tú y muévelo.",
    "cr": "Vota tú y muévelo.", "gt": "Votá vos y movelo.", "bo": "Votá vos y movelo.",
}
HISTORIAL_CTA = {
    "ar": "Sumá tu duelo.", "mx": "Suma tu duelo.", "es": "Suma tu duelo.",
    "br": "Some o seu duelo.", "cl": "Suma tu duelo.", "pe": "Suma tu duelo.",
    "co": "Suma tu duelo.", "us": "Add your duel.", "esus": "Suma tu duelo.",
    "uy": "Sumá tu duelo.", "pt": "Soma o teu duelo.", "ec": "Suma tu duelo.",
    "ve": "Suma tu duelo.", "cr": "Suma tu duelo.", "gt": "Sumá tu duelo.", "bo": "Sumá tu duelo.",
}

# Texto adicional debajo del link de la pagina de ranking -- explica como
# se arma el ranking (distinto del "como funciona un duelo" que ya cubre
# seo_p en votar, para no duplicar contenido entre las dos paginas).
# Mismo split voseo/tuteo que RANKING_CTA de arriba.
_RANKING_SEO_ES_VOSEO = (
    "Este ranking no lo arma nadie desde un escritorio: se arma solo, voto a voto. "
    "Todos los arquetipos empiezan en 1.000 de aura, y cada duelo mueve la aguja según "
    "a quién le ganás — vencer a uno que tenía más aura que vos suma más que vencer a "
    "uno que ya estaba abajo. Por eso el primer puesto cambia seguido: alcanza con que "
    "un arquetipo pegue una racha de duelos ganados para trepar varios lugares de una. "
    "Lo mismo pasa abajo: quedar en aura negativa es fácil si se te juntan varias "
    "derrotas, y de ahí también se sale votando."
)
_RANKING_SEO_ES_TUTEO = (
    "Este ranking no lo arma nadie desde un escritorio: se arma solo, voto a voto. "
    "Todos los arquetipos empiezan en 1.000 de aura, y cada duelo mueve la aguja según "
    "a quién le ganes — vencer a uno que tenía más aura que tú suma más que vencer a "
    "uno que ya estaba abajo. Por eso el primer puesto cambia seguido: alcanza con que "
    "un arquetipo pegue una racha de duelos ganados para trepar varios lugares de una. "
    "Lo mismo pasa abajo: quedar en aura negativa es fácil si se te juntan varias "
    "derrotas, y de ahí también se sale votando."
)
RANKING_SEO_H2 = {
    "ar": "Cómo se arma este ranking", "mx": "Cómo se arma este ranking",
    "es": "Cómo se arma este ranking", "br": "Como esse ranking é montado",
    "cl": "Cómo se arma este ranking", "pe": "Cómo se arma este ranking",
    "co": "Cómo se arma este ranking", "us": "How this ranking gets built",
    "esus": "Cómo se arma este ranking", "uy": "Cómo se arma este ranking",
    "pt": "Como este ranking é construído", "ec": "Cómo se arma este ranking",
    "ve": "Cómo se arma este ranking", "cr": "Cómo se arma este ranking",
    "gt": "Cómo se arma este ranking", "bo": "Cómo se arma este ranking",
}
RANKING_SEO_P = {
    "ar": _RANKING_SEO_ES_VOSEO, "uy": _RANKING_SEO_ES_VOSEO, "gt": _RANKING_SEO_ES_VOSEO,
    "bo": _RANKING_SEO_ES_VOSEO,
    "mx": _RANKING_SEO_ES_TUTEO, "es": _RANKING_SEO_ES_TUTEO,
    "cl": _RANKING_SEO_ES_TUTEO, "pe": _RANKING_SEO_ES_TUTEO,
    "co": _RANKING_SEO_ES_TUTEO, "esus": _RANKING_SEO_ES_TUTEO,
    "ec": _RANKING_SEO_ES_TUTEO, "ve": _RANKING_SEO_ES_TUTEO,
    "cr": _RANKING_SEO_ES_TUTEO,
    "br": (
        "Esse ranking não é decidido por ninguém: ele se monta sozinho, voto a voto. "
        "Todos os arquétipos começam com 1.000 de aura, e cada duelo mexe no placar de "
        "acordo com quem você derrota — vencer alguém com mais aura do que você soma "
        "mais do que vencer alguém que já estava por baixo. Por isso o primeiro lugar "
        "muda direto: basta um arquétipo emplacar uma sequência de vitórias pra subir "
        "vários lugares de uma vez. O mesmo vale lá embaixo: cair pra aura negativa é "
        "fácil se você acumula algumas derrotas seguidas, e dá pra sair de lá votando "
        "também."
    ),
    "pt": (
        "Este ranking não é decidido por ninguém: constrói-se sozinho, voto a voto. "
        "Todos os arquétipos começam com 1.000 de aura, e cada duelo mexe no placar "
        "consoante quem derrotas — vencer alguém com mais aura do que tu soma mais do "
        "que vencer alguém que já estava por baixo. Por isso o primeiro lugar muda com "
        "frequência: basta um arquétipo emplacar uma sequência de vitórias para subir "
        "vários lugares de uma vez. O mesmo vale lá em baixo: cair para aura negativa é "
        "fácil se acumulares algumas derrotas seguidas, e também se sai de lá a votar."
    ),
    "us": (
        "Nobody sets this ranking from a desk — it builds itself, one vote at a time. "
        "Every archetype starts at 1,000 aura, and each duel moves the needle based on "
        "who you beat: beating something with more aura than you earns more than "
        "beating something that was already down. That's why first place changes "
        "often — one winning streak is enough for an archetype to climb several spots "
        "at once. The same goes for the bottom: falling into negative aura is easy "
        "after a few losses in a row, and voting your way back out works just as well."
    ),
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
    "pt": "Duelos entre famosos", "ec": "Duelos entre famosos", "ve": "Duelos entre famosos",
    "cr": "Duelos entre famosos", "gt": "Duelos entre famosos", "bo": "Duelos entre famosos",
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
        og_image = f"{base}/og-{loc}.jpg"

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
             {"VOTAR_URL": votar_url, "RANKING_CTA": esc(RANKING_CTA[loc]),
              "RANKING_SEO_H2": esc(RANKING_SEO_H2[loc]), "RANKING_SEO_P": esc(RANKING_SEO_P[loc])},
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
                ("OGIMAGE", og_image),
                ("CSS", css),
                ("JSONLD", jsonld(L, page, canonical)),
                ("HOME", home),
                ("NAV", nav_html(loc, key)),
                ("H1", esc(page["h1"])),
                ("SUB", esc(page["sub"])),
                ("OFFLINE", esc(L["offline"])),
                ("MAIN", main),
                ("SITEFOOTER", nav_data.site_footer_html(loc, home, L["footer"])),
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
                "<url><loc>%s</loc><lastmod>%s</lastmod>"
                "<changefreq>daily</changefreq></url>\n" % (u, TODAY) for u in nuevas
            )
            xml = re.sub(r"</urlset>", bloque + "</urlset>", xml, count=1)
            sm.write_text(xml, encoding="utf-8")
            print("  -> sitemap.xml (+%d URLs)" % len(nuevas))


if __name__ == "__main__":
    print("Construyendo duelos...")
    build()
    print("Listo.")
