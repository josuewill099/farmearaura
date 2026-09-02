#!/usr/bin/env python3
"""
Mapa de "batallas de aura" en Argentina -- un registro curado (no un
calendario en vivo) de lugares donde paso de verdad el fenomeno, con
fecha y fuente por entrada.

    python3 build_batallas.py

Solo Argentina por ahora (ver plan). Mapa esquematico de provincias por
posicion, no un shapefile real: los SVG de provincias disponibles en
Wikimedia Commons no traen un <path> separado y etiquetado por
provincia (son ilustraciones cartograficas de una sola pieza), asi que
en vez de adivinar cual de ~300 paths sin nombre es cada provincia,
cada una es un punto clickeable desde el dia 1.

Las coordenadas de PROVINCES son pixeles finales, no lat/lon: arrancaron
como una proyeccion lineal de la capital real de cada provincia, pero
esa proyeccion cruda dejaba varios pares pegados o superpuestos (jujuy/
salta, chaco/corrientes, santa-fe/entre-rios, catamarca vs. su propia
etiqueta de texto sobre la-rioja, etc. -- confirmado en el navegador,
no solo a ojo). Se resolvio con un relajamiento iterativo simple
(separar cualquier par mas cerca de lo que su radio + su etiqueta de
texto necesitan, con un tironeo suave de vuelta a la posicion real) y
el resultado ya verificado se dejo fijo aca -- no recalcular desde
lat/lon de nuevo sin repetir esa verificacion de colisiones.
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

# (slug, nombre completo, etiqueta corta para el mapa, x, y, radio)
# x/y en pixeles dentro del viewBox 0 0 460 800 (ver "por que estan fijas
# y no calculadas" en el docstring de arriba). radio 15 = con datos desde
# el arranque (Cordoba, Santa Fe, Tucuman, Buenos Aires), 11 = el resto.
PROVINCES = [
    ("jujuy", "Jujuy", "Jujuy", 215.8, 97.6, 11),
    ("salta", "Salta", "Salta", 171.3, 110.7, 11),
    ("formosa", "Formosa", "For.", 332.3, 141.4, 11),
    ("chaco", "Chaco", "Chaco", 290.8, 164.8, 11),
    ("misiones", "Misiones", "Mis.", 373.9, 170.0, 11),
    ("corrientes", "Corrientes", "Ctes.", 330.1, 189.1, 11),
    ("catamarca", "Catamarca", "Cat.", 199.1, 209.0, 11),
    ("tucuman", "Tucumán", "Tuc.", 189.6, 158.3, 15),
    ("santiago-del-estero", "Santiago del Estero", "S.E.", 235.9, 179.6, 11),
    ("la-rioja", "La Rioja", "La Rioja", 152.4, 210.2, 11),
    ("san-juan", "San Juan", "San Juan", 137.0, 255.3, 11),
    ("mendoza", "Mendoza", "Mendoza", 129.8, 301.9, 11),
    ("cordoba", "Córdoba", "Córdoba", 215.6, 259.3, 15),
    ("santa-fe", "Santa Fe", "Santa Fe", 269.3, 243.8, 15),
    ("entre-rios", "Entre Ríos", "E. Ríos", 298.9, 284.2, 11),
    ("san-luis", "San Luis", "San Luis", 177.7, 299.1, 11),
    ("la-pampa", "La Pampa", "La Pampa", 215.4, 370.4, 11),
    ("buenos-aires", "Buenos Aires", "Bs. As.", 285.3, 389.3, 15),
    ("caba", "CABA", "CABA", 324.3, 327.2, 11),
    ("neuquen", "Neuquén", "Neuquén", 146.0, 420.4, 11),
    ("rio-negro", "Río Negro", "Río Negro", 239.2, 460.3, 11),
    ("chubut", "Chubut", "Chubut", 200.5, 513.8, 11),
    ("santa-cruz", "Santa Cruz", "Santa Cruz", 124.6, 692.4, 11),
    ("tierra-del-fuego", "Tierra del Fuego", "T. Fuego", 141.6, 760.7, 11),
]

VIEW_W, VIEW_H = 460, 800

# Silueta simplificada del pais (continente + Tierra del Fuego), a mano,
# calibrada con la MISMA proyeccion lineal de lat/lon que se uso para
# ubicar los puntos de provincia antes de fijarlos en pixeles -- por
# construccion, no por ajuste visual, asi que el contorno y los puntos
# coinciden. No es un trazado catastral (~25 vertices, no miles), es
# contexto geografico para que el mapa no sean puntos flotando en la
# nada -- lo que pidio el usuario al ver la primera version.
OUTLINE_MAINLAND = (
    "M191.3,56.5 226.3,58.6 294.5,62.9 393.9,131.6 370,174.6 320.3,174.6 "
    "338.7,232.5 323.9,296.9 355.3,363.5 252.1,421.5 239.2,464.4 202.4,513.8 "
    "156.3,569.6 185.8,610.4 139.7,664.1 128.7,698.4 101.1,707 67.9,636.2 "
    "77.1,571.8 82.6,485.9 110.3,400 110.3,292.6 141.6,217.5 169.2,99.4 Z"
)
OUTLINE_TDF = (
    "M136.1,713.5 156.3,724.2 196.8,754.3 160,762.9 136.1,752.1 130.5,732.8 Z"
)


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def build_svg(counts):
    parts = [
        f'<svg viewBox="0 0 {VIEW_W} {VIEW_H}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="Mapa de provincias de Argentina con batallas de aura registradas">'
        f'<path class="country-outline" d="{OUTLINE_MAINLAND}"/>'
        f'<path class="country-outline" d="{OUTLINE_TDF}"/>'
    ]
    for slug, name, short, x, y, r in PROVINCES:
        n = counts.get(slug, 0)
        cls = "prov has-data" if n else "prov"
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
