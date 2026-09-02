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

SLUG = "batallas-de-aura"
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
}

LOCALES = {
    "ar": {
        "home": "/",
        "geo_file": "provincias-ar.geo.json",
        "view_w": 460, "view_h": 800,
        "region_word": "provincia",
        "country_name": "Argentina",
        "lang": "es-AR",
        "address_country": "AR",
        "voseo": True,
    },
    "uy": {
        "home": "/uy/",
        "geo_file": "departamentos-uy.geo.json",
        "view_w": 460, "view_h": 546,
        "region_word": "departamento",
        "country_name": "Uruguay",
        "lang": "es-UY",
        "address_country": "UY",
        "voseo": True,
    },
    "es": {
        "home": "/es/",
        "geo_file": "provincias-es.geo.json",
        "view_w": 460, "view_h": 424,
        "region_word": "provincia",
        "country_name": "España",
        "lang": "es-ES",
        "address_country": "ES",
        "voseo": False,
    },
}


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def build_svg(cfg, regions_geo, counts):
    parts = [
        f'<svg viewBox="0 0 {cfg["view_w"]} {cfg["view_h"]}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="Mapa de {cfg["region_word"]}s de {cfg["country_name"]} '
        f'con batallas de aura registradas">'
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


def build_jsonld(cfg, L, canonical):
    graph = [{
        "@type": "WebPage", "@id": canonical, "url": canonical,
        "name": L["h1"], "description": L["desc"], "inLanguage": cfg["lang"],
        "isPartOf": {"@id": f"{DOMAIN}/#website"},
    }]
    for v in L["venues"]:
        graph.append({
            "@type": "Event",
            "name": f'Batalla de Aura — {v["lugar"]}, {v["ciudad"]}',
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
    return ('<script type="application/ld+json">' +
            json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False) +
            '</script>')


def build_one(loc, cfg):
    L = json.loads((ROOT / "locales" / f"batallas-{loc}.json").read_text(encoding="utf-8"))
    regions_geo = json.loads((ROOT / "locales" / cfg["geo_file"]).read_text(encoding="utf-8"))
    tpl = (SRC / "batallas.tpl.html").read_text(encoding="utf-8")
    home = DOMAIN + cfg["home"]
    canonical = f"{home}{SLUG}/"

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
        ("INTRO", esc(L["intro"])),
        ("MAP_HINT", f'{"Tocá" if cfg["voseo"] else "Toca"} '
                     f'{"una" if cfg["region_word"] == "provincia" else "un"} '
                     f'{cfg["region_word"]} con marca para filtrar'),
        ("VENUE_COUNT", str(len(L["venues"]))),
        ("MAP_SVG", build_svg(cfg, regions_geo, counts)),
        ("MAP_ATTRIBUTION", ATTRIBUTION),
        ("VENUE_CARDS", build_venue_cards(L["venues"])),
        ("FOOTERNOTE", L["footerNote"]),  # contiene un <a> real, no escapar
        ("LEGALLINKS", nav_data.legal_links_html(loc, home)),
    ]:
        html = html.replace("{{%s}}" % k, v)

    html = html.replace("<!--ANALYTICS-->", ANALYTICS)

    home_dir = cfg["home"].strip("/")   # "" for ar (root), "uy" for uruguay
    out = (DIST / SLUG / "index.html") if not home_dir else (DIST / home_dir / SLUG / "index.html")
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
