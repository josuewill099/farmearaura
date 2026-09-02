#!/usr/bin/env python3
"""
Mapa de "batallas de aura" en Argentina -- un registro curado (no un
calendario en vivo) de lugares donde paso de verdad el fenomeno, con
fecha y fuente por entrada.

    python3 build_batallas.py

Solo Argentina por ahora (ver plan).

El mapa usa las formas reales de las 24 provincias (no puntos ni un
contorno esquematico dibujado a mano): locales/provincias-ar.geo.json
tiene, por provincia, un <path> ya proyectado a pixeles y un punto de
etiqueta (centroide del poligono mas grande de cada provincia, para
Buenos Aires/Tierra del Fuego que son MultiPolygon). Ese archivo sale
de countries/ar/ar-all.geo.json del repo highcharts/map-collection-dist
(datos de Natural Earth, ver ATTRIBUTION mas abajo) -- a diferencia de
los mapas de Wikimedia Commons usados en un intento anterior (~300-400
<path> sin nombre ni id, imposibles de asociar a una provincia sin
adivinar), este trae "name" real por feature, asi que cada forma se
pudo mapear a su slug con certeza. Ver el script de conversion
(convert-geojson.js, no versionado -- fue un scratch de una sola vez)
si hay que regenerar el archivo con otra fuente.
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

VIEW_W, VIEW_H = 460, 800

# Etiqueta corta para provincias chicas donde el nombre completo no entra
# adentro de su propia forma (CABA, Tucuman...). Las demas usan su nombre
# completo tal cual viene en el geojson.
SHORT_LABEL = {
    "formosa": "For.", "misiones": "Mis.", "corrientes": "Ctes.",
    "catamarca": "Cat.", "tucuman": "Tuc.", "santiago-del-estero": "S.E.",
    "entre-rios": "E. Ríos", "buenos-aires": "Bs. As.", "caba": "CABA",
    "tierra-del-fuego": "T. Fuego",
}


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def build_svg(provinces_geo, counts):
    parts = [
        f'<svg viewBox="0 0 {VIEW_W} {VIEW_H}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="Mapa de provincias de Argentina con batallas de aura registradas">'
    ]
    for p in provinces_geo:
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


def build_jsonld(L, canonical):
    graph = [{
        "@type": "WebPage", "@id": canonical, "url": canonical,
        "name": L["h1"], "description": L["desc"], "inLanguage": "es-AR",
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
                            "addressCountry": "AR"},
            },
            "description": v["descripcion"],
        })
    return ('<script type="application/ld+json">' +
            json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False) +
            '</script>')


def build():
    L = json.loads((ROOT / "locales" / "batallas-ar.json").read_text(encoding="utf-8"))
    provinces_geo = json.loads((ROOT / "locales" / "provincias-ar.geo.json").read_text(encoding="utf-8"))
    tpl = (SRC / "batallas.tpl.html").read_text(encoding="utf-8")
    home = DOMAIN + "/"
    canonical = f"{DOMAIN}/{SLUG}/"

    counts = {}
    for v in L["venues"]:
        counts[v["provincia"]] = counts.get(v["provincia"], 0) + 1

    html = tpl
    for k, v in [
        ("TITLE", esc(L["title"])),
        ("DESC", esc(L["desc"])),
        ("CANONICAL", canonical),
        ("OGIMAGE", f"{DOMAIN}/og-ar.jpg"),
        ("JSONLD", build_jsonld(L, canonical)),
        ("HOME", home),
        ("NAV", nav_data.nav_html("ar", "batallas")),
        ("H1", esc(L["h1"])),
        ("SUB", esc(L["sub"])),
        ("INTRO", esc(L["intro"])),
        ("VENUE_COUNT", str(len(L["venues"]))),
        ("MAP_SVG", build_svg(provinces_geo, counts)),
        ("MAP_ATTRIBUTION", ATTRIBUTION),
        ("VENUE_CARDS", build_venue_cards(L["venues"])),
        ("FOOTERNOTE", esc(L["footerNote"])),
        ("LEGALLINKS", nav_data.legal_links_html("ar", home)),
    ]:
        html = html.replace("{{%s}}" % k, v)

    html = html.replace("<!--ANALYTICS-->", ANALYTICS)

    out = DIST / SLUG / "index.html"
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


if __name__ == "__main__":
    build()
    print("build_batallas ok ->", DIST)
