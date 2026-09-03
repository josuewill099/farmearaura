#!/usr/bin/env python3
"""
Mapas de "batallas de aura" por pais -- un registro curado (no un
calendario en vivo) de lugares donde paso de verdad el fenomeno, con
fecha y fuente por entrada.

    python3 build_batallas.py

Cada mapa usa las formas reales de las divisiones de primer nivel del
pais (provincias en Argentina, departamentos en Uruguay), no puntos ni
un contorno esquematico dibujado a mano: locales/<geo_file> tiene, por
division, un <path> ya proyectado a pixeles y un punto de etiqueta
(centroide del poligono mas grande de la feature, para los casos
MultiPolygon como Buenos Aires o Tierra del Fuego). Esos archivos salen
de countries/<cc>/<cc>-all.geo.json del repo highcharts/map-collection-dist
(datos de Natural Earth, ver ATTRIBUTION mas abajo) -- a diferencia de
los mapas de Wikimedia Commons probados primero (~300-400 <path> sin
nombre ni id, imposibles de asociar a una region sin adivinar), estos
traen "name" real por feature, asi que cada forma se pudo mapear a su
slug con certeza. Ver los scripts de conversion (convert-geojson*.js,
no versionados -- fueron scratches de una sola vez) si hay que agregar
otro pais.
"""

import json
import re
from datetime import date
from pathlib import Path

import nav_data

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
DOMAIN = "https://farmearaura.com"
TODAY = date.today().isoformat()
ATTRIBUTION = "Mapa: Natural Earth, vía Highcharts map-collection-dist"
GA4_ID = "G-XHZ0MM619V"   # mismo tag que el resto del sitio
ANALYTICS = (
    '<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>\n'
    "<script>window.dataLayer=window.dataLayer||[];"
    "function gtag(){dataLayer.push(arguments);}"
    'gtag("js",new Date());gtag("config","%s");</script>'
) % (GA4_ID, GA4_ID)

# Etiqueta corta para regiones chicas donde el nombre completo no entra
# adentro de su propia forma. Las demas usan su nombre completo tal cual
# viene en el geojson. Clave = slug de la region (unico en todo el sitio,
# no hay colision entre provincias AR y departamentos UY).
SHORT_LABEL = {
    "formosa": "For.", "misiones": "Mis.", "corrientes": "Ctes.",
    "catamarca": "Cat.", "tucuman": "Tuc.", "santiago-del-estero": "S.E.",
    "entre-rios": "E. Ríos", "buenos-aires": "Bs. As.", "caba": "CABA",
    "tierra-del-fuego": "T. Fuego",
    "cerro-largo": "C. Largo", "tacuarembo": "Tacuar.",
    "treinta-y-tres": "33", "rio-negro": "Río Negro",
    "santa-cruz-tenerife": "Tenerife", "ciudad-real": "C. Real",
    "castellon": "Castel.", "la-rioja-es": "La Rioja",
    "arica-parinacota": "Arica", "metropolitana": "R.M.",
    "san-andres": "S. Andrés", "norte-de-santander": "N. Sant.",
    "valle-del-cauca": "V. Cauca", "madre-de-dios": "M. de Dios",
    "lima-provincia": "Lima Prov.",
}

LOCALES = {
    "ar": {
        "home": "/", "slug": "batallas-de-aura",
        "geo_file": "provincias-ar.geo.json",
        "view_w": 460, "view_h": 800,
        "lang": "es-AR", "address_country": "AR",
        "update_label": "Mapa actualizado:",
    },
    "uy": {
        "home": "/uy/", "slug": "batallas-de-aura",
        "geo_file": "departamentos-uy.geo.json",
        "view_w": 460, "view_h": 546,
        "lang": "es-UY", "address_country": "UY",
    },
    "es": {
        "home": "/es/", "slug": "batallas-de-aura",
        "geo_file": "provincias-es.geo.json",
        "view_w": 460, "view_h": 424,
        "lang": "es-ES", "address_country": "ES",
    },
    "cl": {
        "home": "/cl/", "slug": "batallas-de-aura",
        "geo_file": "regiones-cl.geo.json",
        "view_w": 460, "view_h": 2776,
        "lang": "es-CL", "address_country": "CL",
    },
    "co": {
        "home": "/co/", "slug": "batallas-de-aura",
        "geo_file": "departamentos-co.geo.json",
        "view_w": 460, "view_h": 567,
        "lang": "es-CO", "address_country": "CO",
    },
    "pe": {
        "home": "/pe/", "slug": "batallas-de-aura",
        "geo_file": "regiones-pe.geo.json",
        "view_w": 460, "view_h": 713,
        "lang": "es-PE", "address_country": "PE",
    },
    "br": {
        "home": "/br/", "slug": "batalhas-de-farmar-aura",
        "geo_file": "estados-br.geo.json",
        "view_w": 460, "view_h": 499,
        "lang": "pt-BR", "address_country": "BR",
    },
    "pt": {
        "home": "/pt/", "slug": "batalhas-de-farmar-aura",
        "geo_file": "distritos-pt.geo.json",
        "view_w": 460, "view_h": 741,
        "lang": "pt-PT", "address_country": "PT",
    },
    "mx": {
        "home": "/mx/", "slug": "batallas-de-aura",
        "geo_file": "estados-mx.geo.json",
        "view_w": 460, "view_h": 329,
        "lang": "es-MX", "address_country": "MX",
    },
    "ec": {
        "home": "/ec/", "slug": "batallas-de-aura",
        "geo_file": "provincias-ec.geo.json",
        "view_w": 460, "view_h": 438,
        "lang": "es-EC", "address_country": "EC",
    },
    # us/esus son el mismo pais, mismo geo_file -- solo cambia el idioma
    # (y, por ahora, los dos arrancan con venues: [] -- ver el commit).
    "us": {
        "home": "/us/", "slug": "aura-battles",
        "geo_file": "states-us.geo.json",
        "view_w": 460, "view_h": 346,
        "lang": "en-US", "address_country": "US",
    },
    "esus": {
        "home": "/es-us/", "slug": "batallas-de-aura",
        "geo_file": "states-us.geo.json",
        "view_w": 460, "view_h": 346,
        "lang": "es-US", "address_country": "US",
    },
}


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def build_svg(cfg, regions_geo, counts, aria_label):
    parts = [
        f'<svg viewBox="0 0 {cfg["view_w"]} {cfg["view_h"]}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="{esc(aria_label)}">'
    ]
    for p in regions_geo:
        slug = p["slug"]
        n = counts.get(slug, 0)
        cls = "prov has-data" if n else "prov"
        label = f"{esc(p['name'])}: {n} lugar{'es' if n != 1 else ''}" if n else esc(p["name"])
        short = SHORT_LABEL.get(slug, p["name"])
        parts.append(
            f'<g data-provincia="{slug}">'
            f'<path class="{cls}" data-provincia="{slug}" d="{p["d"]}"><title>{label}</title></path>'
            f'<text class="prov-label{" has-data" if n else ""}" x="{p["labelX"]}" y="{p["labelY"]}">{esc(short)}</text>'
            f'</g>'
        )
    parts.append('</svg>')
    return "".join(parts)


def build_venue_cards(venues):
    cards = []
    for v in venues:
        fuentes = " ".join(
            f'<a href="{esc(url)}" rel="noopener" target="_blank">{esc(label)}</a>'
            for label, url in v["fuente"]
        )
        fecha = date.fromisoformat(v["fecha"]).strftime("%d/%m/%Y")
        cards.append(
            f'<li class="venue" data-provincia="{v["provincia"]}">'
            f'<p class="venue__place">{esc(v["lugar"])}</p>'
            f'<p class="venue__meta">{esc(v["ciudad"])} · {fecha}</p>'
            f'<p class="venue__desc">{esc(v["descripcion"])}</p>'
            f'<div class="venue__sources">{fuentes}</div>'
            f'</li>'
        )
    return "\n".join(cards)


def build_faq_html(faq):
    return "\n".join(
        f'<details{" open" if i == 0 else ""}><summary>{esc(q)}</summary>'
        f'<div class="a"><p>{esc(a)}</p></div></details>'
        for i, (q, a) in enumerate(faq)
    )


def build_update_banner(cfg):
    # Banda "Mapa actualizado: <fecha de hoy>" -- a proposito muestra la
    # fecha del dia en que el visitante entra (computada en el navegador
    # con Intl.DateTimeFormat), no la fecha real del ultimo venue agregado.
    # Solo las locales con "update_label" en su config de LOCALES la
    # muestran (por ahora, unicamente ar) -- el resto de las locales no
    # tocan este placeholder y build_one() lo deja vacio.
    label = cfg.get("update_label")
    if not label:
        return ""
    intl_locale = cfg["lang"]
    return (
        '<div class="update-banner">'
        '<span class="update-banner__dot"></span>'
        f'<span>{esc(label)} <b id="js-update-date"></b></span>'
        '</div>'
        '<script>(function(){'
        f'var f=new Intl.DateTimeFormat("{intl_locale}",{{day:"numeric",month:"long",year:"numeric"}});'
        'var el=document.getElementById("js-update-date");'
        'if(el)el.textContent=f.format(new Date());'
        '})();</script>'
    )


def build_jsonld(cfg, L, canonical):
    # "Batalla" en espanol, "Batalha" en portugues -- unica palabra que
    # cambia en este nombre, asi que se resuelve por idioma en vez de
    # sumar otro campo mas al JSON de cada locale.
    event_word = "Batalha" if cfg["lang"].startswith("pt") else "Batalla"
    graph = [{
        "@type": "WebPage", "@id": canonical, "url": canonical,
        "name": L["h1"], "description": L["desc"], "inLanguage": cfg["lang"],
        "isPartOf": {"@id": f"{DOMAIN}/#website"},
    }]
    for v in L["venues"]:
        graph.append({
            "@type": "Event",
            "name": f'{event_word} de Aura — {v["lugar"]}, {v["ciudad"]}',
            "startDate": v["fecha"],
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "location": {
                "@type": "Place",
                "name": v["lugar"],
                "address": {"@type": "PostalAddress", "addressLocality": v["ciudad"],
                            "addressCountry": cfg["address_country"]},
            },
            "description": v["descripcion"],
        })
    if L.get("faq"):
        graph.append({
            "@type": "FAQPage", "@id": canonical + "#faq",
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in L["faq"]
            ],
        })
    return ('<script type="application/ld+json">' +
            json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False) +
            '</script>')


def build_one(loc, cfg):
    L = json.loads((ROOT / "locales" / f"batallas-{loc}.json").read_text(encoding="utf-8"))
    regions_geo = json.loads((ROOT / "locales" / cfg["geo_file"]).read_text(encoding="utf-8"))
    tpl = (SRC / "batallas.tpl.html").read_text(encoding="utf-8")
    home = DOMAIN + cfg["home"]
    canonical = f"{home}{cfg['slug']}/"

    counts = {}
    for v in L["venues"]:
        counts[v["provincia"]] = counts.get(v["provincia"], 0) + 1

    html = tpl
    for k, v in [
        ("LANG", cfg["lang"]),
        ("TITLE", esc(L["title"])),
        ("DESC", esc(L["desc"])),
        ("CANONICAL", canonical),
        ("OGLOCALE", cfg["lang"].replace("-", "_")),
        ("OGIMAGE", f"{DOMAIN}/og-{loc}.jpg"),
        ("JSONLD", build_jsonld(cfg, L, canonical)),
        ("HOME", home),
        ("NAV", nav_data.nav_html(loc, "batallas")),
        ("H1", esc(L["h1"])),
        ("SUB", esc(L["sub"])),
        ("UPDATE_BANNER", build_update_banner(cfg)),
        ("INTRO", esc(L["intro"])),
        # mapHint/mapAriaLabel/venueCountLabel son oraciones completas ya
        # escritas en el idioma de cada locale (no armadas por Python a
        # partir de piezas) -- con dos idiomas (es/pt) y variantes internas
        # (voseo/tuteo, provincia/departamento/region, estado/distrito,
        # genero de cada palabra), tratar de ensamblar la oracion aca
        # termina rompiendo la gramatica de alguna combinacion tarde o
        # temprano (paso dos veces: "un region" en vez de "una region",
        # "regions" en vez de "regiones").
        ("MAP_HINT", esc(L["mapHint"])),
        ("VENUE_COUNT", str(len(L["venues"]))),
        ("VENUE_COUNT_LABEL", esc(L["venueCountLabel"])),
        ("MAP_SVG", build_svg(cfg, regions_geo, counts, L["mapAriaLabel"])),
        ("MAP_ATTRIBUTION", ATTRIBUTION),
        ("VENUE_CARDS", build_venue_cards(L["venues"])),
        ("FAQ_HEADING", esc(L["faqHeading"])),
        ("FAQ_HTML", build_faq_html(L["faq"])),
        ("FOOTERNOTE", L["footerNote"]),  # contiene un <a> real, no escapar
        ("LEGALLINKS", nav_data.legal_links_html(loc, home)),
    ]:
        html = html.replace("{{%s}}" % k, v)

    html = html.replace("<!--ANALYTICS-->", ANALYTICS)

    home_dir = cfg["home"].strip("/")   # "" for ar (root), "uy" for uruguay
    slug = cfg["slug"]
    out = (DIST / slug / "index.html") if not home_dir else (DIST / home_dir / slug / "index.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("  ->", out.relative_to(ROOT), "(%.1f KB)" % (len(html) / 1024))

    sm = DIST / "sitemap.xml"
    if sm.exists():
        xml = sm.read_text(encoding="utf-8")
        if f"<loc>{canonical}</loc>" not in xml:
            bloque = (f"<url><loc>{canonical}</loc><lastmod>{TODAY}</lastmod>"
                      f"<changefreq>weekly</changefreq></url>\n")
            xml = re.sub(r"</urlset>", bloque + "</urlset>", xml, count=1)
            sm.write_text(xml, encoding="utf-8")
            print("  -> sitemap.xml (+1 URL)")


def build():
    for loc, cfg in LOCALES.items():
        build_one(loc, cfg)


if __name__ == "__main__":
    build()
    print("build_batallas ok ->", DIST)
