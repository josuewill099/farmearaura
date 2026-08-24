#!/usr/bin/env python3
"""
Paginas de contenido standalone (no interactivas) para clusters de keywords
que no encajan en las paginas principales de cada locale:

  br   -- como-farmar-aura, campeonato-de-farmar-aura, farmar-aura-meme
  ar/mx/es -- el cluster "color de aura" (lectura de aura, publico distinto
              al de "farmar aura"): pillar color-de-aura/ + una pagina por
              color. ar/mx suman ademas aura-farming/ (el termino en ingles
              se busca mas que "farmar aura" en esos dos mercados).
  us   -- aura-test, aura-color-test, piccolo-aura-farming (hub que cubre
           tambien Gojo/Sung Jin Woo/Agamemnon), how-to-aura-farm.

    python3 build.py && python3 build_articles.py

Reusa el mismo guide.tpl.html (misma identidad visual que la guia), pero con
"sections" de forma libre -- parrafo o lista, igual que las paginas legales
de build_legal() -- en vez del esquema fijo ledger/reglas/lose de la guia.

Los slugs compartidos entre locales (los colores y aura-farming, presentes
en mas de una entrada de LOCS) se tratan como la MISMA pagina apuntada a
mercados distintos y llevan hreflang reciproco entre si, igual que
build_duelos.py/build_historia.py/build_famosos.py hacen entre locales.
"""

import json
import re
from pathlib import Path

import nav_data

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
DOMAIN = "https://farmearaura.com"

GUIDE_TPL = (SRC / "guide.tpl.html").read_text(encoding="utf-8")

# locale -> archivo de articulos. Sumar otra locale es agregar su entrada
# aca + locales/articles-{loc}.json con el mismo esquema.
LOCS = {
    "br": "locales/articles-br.json",
    "us": "locales/articles-us.json",
    "ar": "locales/articles-ar.json",
    "mx": "locales/articles-mx.json",
    "es": "locales/articles-es.json",
}

# Defaults por locale para los textos de chrome (breadcrumb "home", label del
# TOC, encabezado de fuentes) -- cada articulo puede pisarlos con su propia
# clave si hace falta, pero la mayoria no necesita repetirlos.
HOME_LABEL = {"br": "Início", "us": "Home", "ar": "Inicio", "mx": "Inicio", "es": "Inicio"}
TOC_LABEL = {"br": "NESTA PÁGINA", "us": "ON THIS PAGE", "ar": "EN ESTA PÁGINA",
             "mx": "EN ESTA PÁGINA", "es": "EN ESTA PÁGINA"}
SOURCES_H = {"br": "Fontes", "us": "Sources", "ar": "Fuentes", "mx": "Fuentes", "es": "Fuentes"}
FAQ_HEADING = {"br": "Perguntas frequentes", "us": "FAQ", "ar": "Preguntas frecuentes",
               "mx": "Preguntas frecuentes", "es": "Preguntas frecuentes"}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_sections(sections):
    out = []
    for h, blocks in sections:
        inner = []
        for b in blocks:
            if isinstance(b, dict):
                inner.append('  <ul class="plain">\n' + "\n".join(
                    f"    <li>{x}</li>" for x in b["ul"]) + "\n  </ul>")
            else:
                inner.append(f"  <p>{b}</p>")
        out.append((h, "\n".join(inner)))
    return out


def build():
    data = {}   # loc -> {"L": articles-list, "lang":, "home":, "base":}
    for loc, path in LOCS.items():
        L = json.loads((ROOT / path).read_text(encoding="utf-8"))
        home_json = json.loads((ROOT / "locales" / f"{loc}.json").read_text(encoding="utf-8"))
        lang, home = home_json["lang"], home_json["path"]
        data[loc] = {"L": L, "lang": lang, "home": home, "base": DOMAIN + home.rstrip("/")}

    # Paginas con el mismo slug en mas de una locale (los colores y el meme,
    # compartidos entre ar/mx/es) son la MISMA pagina apuntada a mercados
    # distintos, asi que cada una debe listar a sus hermanas en hreflang --
    # el mismo patron reciproco que build_duelos.py usa entre locales.
    siblings = {}   # slug -> [(hreflang_code, url), ...]
    for loc, d in data.items():
        for art in d["L"]["articles"]:
            siblings.setdefault(art["slug"], []).append(
                (d["lang"], f"{d['base']}/{art['slug']}/"))

    urls = []
    for loc, d in data.items():
        L, lang, home, base = d["L"], d["lang"], d["home"], d["base"]

        for art in L["articles"]:
            canonical = f"{base}/{art['slug']}/"

            blocks = render_sections(art["sections"])
            if art.get("faq"):
                faq_html = "\n".join(
                    f'  <details{" open" if i == 0 else ""}><summary>{esc(q)}</summary>'
                    f'<div class="a"><p>{a}</p></div></details>'
                    for i, (q, a) in enumerate(art["faq"]))
                blocks.append((art.get("faqHeading", FAQ_HEADING[loc]), faq_html))

            toc = '    <ol>\n' + "\n".join(
                f'      <li><a href="#s{i+1}">{esc(h)}</a></li>' for i, (h, _) in enumerate(blocks)
            ) + "\n    </ol>"
            sections = "\n\n".join(
                f'  <h2 id="s{i+1}">{esc(h)}</h2>\n{body}' for i, (h, body) in enumerate(blocks))

            related = "\n".join(
                f'    <a href="{url}">{esc(label)}</a>' for label, url in art["related"])

            home_label = art.get("homeLabel", HOME_LABEL[loc])
            graph = [
                {"@type": "WebPage", "@id": canonical, "url": canonical, "name": art["h1"],
                 "description": art["desc"], "inLanguage": lang,
                 "isPartOf": {"@id": f"{DOMAIN}/#website"}},
                {"@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": home_label, "item": base + "/"},
                    {"@type": "ListItem", "position": 2, "name": art["h1"], "item": canonical}]},
                {"@type": "Article", "@id": canonical + "#article", "headline": art["h1"],
                 "description": art["desc"], "inLanguage": lang,
                 "datePublished": "2026-08-24", "dateModified": "2026-08-24",
                 "author": {"@type": "Organization", "name": "farmearaura.com", "url": DOMAIN + "/"},
                 "publisher": {"@type": "Organization", "name": "farmearaura.com", "url": DOMAIN + "/"}},
            ]
            if art.get("faq"):
                graph.append({"@type": "FAQPage", "@id": canonical + "#faq",
                               "mainEntity": [
                                   {"@type": "Question", "name": q,
                                    "acceptedAnswer": {"@type": "Answer",
                                                        "text": re.sub("<[^>]+>", "", a)}}
                                   for q, a in art["faq"]]})
            ld = json.dumps({"@context": "https://schema.org", "@graph": graph},
                             ensure_ascii=False, indent=2)

            group = siblings[art["slug"]]
            hreflang_tags = "\n".join(
                f'<link rel="alternate" hreflang="{hl}" href="{u}">' for hl, u in group)
            # x-default apunta a la version del locale por defecto (ar) si
            # esta presente en el grupo; si no, a la primera version.
            default_url = next((u for hl, u in group if hl == "es-AR"), group[0][1])
            hreflang_tags += f'\n<link rel="alternate" hreflang="x-default" href="{default_url}">'

            html = GUIDE_TPL.format(
                lang=lang, title=esc(art["title"]), desc=esc(art["desc"]),
                canonical=canonical, hreflang=hreflang_tags,
                oglocale=lang.replace("-", "_"), home=home,
                h1=esc(art["h1"]), answer=art["answer"],
                meta=esc(art.get("meta", "")),
                homeLabel=esc(home_label),
                tocLabel=esc(art.get("tocLabel", TOC_LABEL[loc])),
                toc=toc, sections=sections, related=related,
                sourcesH=esc(art.get("sourcesH", SOURCES_H[loc])),
                sources="\n".join(f"    <li>{x}</li>" for x in art.get("sources", [])),
                promoK=esc(art["promoK"]), promoP=esc(art["promoP"]), promoBtn=esc(art["promoBtn"]),
                promoUrl=art.get("promoUrl", home),
                ctaNav=esc(art["ctaNav"]), guideLink=esc(art.get("guideLink", art["h1"])),
                footerNote=esc(art["footerNote"]), ld=ld,
                legalLinks=nav_data.legal_links_html(loc, home),
            )

            # home.strip("/") es "" para ar (locale por defecto, vive en /);
            # pathlib ignora los componentes vacios al unir paths, asi que
            # el resultado cae directo en dist/, no en dist/ar/.
            out = DIST / home.strip("/") / art["slug"] / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(html, encoding="utf-8")
            urls.append(canonical)
            print("  ->", out.relative_to(ROOT), "(%.1f KB)" % (len(html) / 1024))

    # sitemap
    sm = DIST / "sitemap.xml"
    if sm.exists():
        xml = sm.read_text(encoding="utf-8")
        nuevas = [u for u in urls if "<loc>%s</loc>" % u not in xml]
        if nuevas:
            bloque = "".join(
                "<url><loc>%s</loc><changefreq>monthly</changefreq>"
                "<priority>0.7</priority></url>\n" % u for u in nuevas)
            xml = re.sub(r"</urlset>", bloque + "</urlset>", xml, count=1)
            sm.write_text(xml, encoding="utf-8")
            print("  -> sitemap.xml (+%d URLs)" % len(nuevas))


if __name__ == "__main__":
    print("Construyendo articulos standalone...")
    build()
    print("Listo.")
