#!/usr/bin/env python3
"""
Mapa de "batallas de aura" en Argentina -- un registro curado (no un
calendario en vivo) de lugares donde paso de verdad el fenomeno, con
fecha y fuente por entrada.

    python3 build_batallas.py

Solo Argentina por ahora (ver plan). Mapa esquematico de provincias por
posicion (lat/lon proyectadas a mano), no un shapefile real: los SVG de
provincias disponibles en Wikimedia Commons no traen un <path> separado
y etiquetado por provincia (son ilustraciones cartograficas de una sola
pieza), asi que en vez de adivinar cual de ~300 paths sin nombre es cada
provincia, cada una es un punto (su capital aproximada) ubicado por
proyeccion lineal de lat/lon -- simple, correcto en las posiciones
relativas, y cada punto es su propio elemento clickeable desde el dia 1.
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
GA4_ID = "G-XHZ0MM619V"   # mismo tag que el resto del sitio
ANALYTICS = (
    '<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>\n'
    "<script>window.dataLayer=window.dataLayer||[];"
    "function gtag(){dataLayer.push(arguments);}"
    'gtag("js",new Date());gtag("config","%s");</script>'
) % (GA4_ID, GA4_ID)

# (slug, nombre completo, etiqueta corta para el mapa, lat, lon)
# lat/lon = capital provincial aproximada, con pequenos ajustes a mano en
# grupos que la capital real deja demasiado juntos para el radio de un
# marcador (jujuy/salta, chaco/corrientes, santa-fe/entre-rios -- las
# primeras coordenadas, sin ajustar, dejaban esos pares a 3-13px de
# distancia con circulos de 11-15px de radio, superpuestos en el mapa
# real; verificado en el navegador, no solo calculado). Proyeccion lineal
# simple mas abajo (build_svg): no es una proyeccion cartografica real,
# solo ubica cada punto en su posicion relativa correcta dentro del pais.
PROVINCES = [
    ("jujuy", "Jujuy", "Jujuy", -23.0, -65.5),
    ("salta", "Salta", "Salta", -25.5, -65.2),
    ("formosa", "Formosa", "For.", -26.18, -58.18),
    ("chaco", "Chaco", "Chaco", -26.8, -59.8),
    ("misiones", "Misiones", "Mis.", -27.37, -55.90),
    ("corrientes", "Corrientes", "Ctes.", -28.7, -57.5),
    ("catamarca", "Catamarca", "Cat.", -28.47, -65.78),
    ("tucuman", "Tucumán", "Tuc.", -26.82, -65.22),
    ("santiago-del-estero", "Santiago del Estero", "S.E.", -27.78, -64.26),
    ("la-rioja", "La Rioja", "La Rioja", -29.41, -66.85),
    ("san-juan", "San Juan", "San Juan", -31.54, -68.54),
    ("mendoza", "Mendoza", "Mendoza", -32.89, -68.84),
    ("cordoba", "Córdoba", "Córdoba", -31.42, -64.18),
    ("santa-fe", "Santa Fe", "Santa Fe", -31.2, -61.3),
    ("entre-rios", "Entre Ríos", "E. Ríos", -32.3, -59.2),
    ("san-luis", "San Luis", "San Luis", -33.30, -66.34),
    ("la-pampa", "La Pampa", "La Pampa", -36.62, -64.29),
    ("buenos-aires", "Buenos Aires", "Bs. As.", -37.5, -60.5),
    ("caba", "CABA", "CABA", -34.61, -58.38),
    ("neuquen", "Neuquén", "Neuquén", -38.95, -68.06),
    ("rio-negro", "Río Negro", "Río Negro", -40.81, -63.00),
    ("chubut", "Chubut", "Chubut", -43.30, -65.10),
    ("santa-cruz", "Santa Cruz", "Santa Cruz", -51.62, -69.22),
    ("tierra-del-fuego", "Tierra del Fuego", "T. Fuego", -54.80, -68.30),
]

LON_MIN, LON_MAX = -73, -54
LAT_MIN, LAT_MAX = -55, -21
PAD_X, PAD_Y = 55, 35
VIEW_W, VIEW_H = 460, 800


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def project(lat, lon):
    x = PAD_X + (lon - LON_MIN) / (LON_MAX - LON_MIN) * (VIEW_W - 2 * PAD_X)
    y = PAD_Y + (LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * (VIEW_H - 2 * PAD_Y)
    return round(x, 1), round(y, 1)


def build_svg(counts):
    parts = [
        f'<svg viewBox="0 0 {VIEW_W} {VIEW_H}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="Mapa de provincias de Argentina con batallas de aura registradas">'
    ]
    for slug, name, short, lat, lon in PROVINCES:
        x, y = project(lat, lon)
        n = counts.get(slug, 0)
        cls = "prov has-data" if n else "prov"
        r = 15 if n else 11
        label = f"{esc(name)}: {n} lugar{'es' if n != 1 else ''}" if n else esc(name)
        parts.append(
            f'<g data-provincia="{slug}">'
            f'<circle class="{cls}" data-provincia="{slug}" cx="{x}" cy="{y}" r="{r}">'
            f'<title>{label}</title></circle>'
            f'<text class="prov-label{" has-data" if n else ""}" x="{x}" y="{y + r + 11}">{esc(short)}</text>'
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
        ("MAP_SVG", build_svg(counts)),
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
