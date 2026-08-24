#!/usr/bin/env python3
"""
Paginas de contenido standalone (no interactivas) para clusters de keywords
que no encajan en la guia principal de cada locale (que ya cubre "que es
farmar aura"). Por ahora solo br: como-farmar-aura, campeonato-de-farmar-aura
y farmar-aura-meme -- todas cuelgan de /br/ y se interlinkean entre si, con
la guia (o-que-e-farmar-aura), la calculadora y los duelos/historia/famosos.

    python3 build.py && python3 build_articles.py

Reusa el mismo guide.tpl.html (misma identidad visual que la guia), pero con
"sections" de forma libre -- parrafo o lista, igual que las paginas legales
de build_legal() -- en vez del esquema fijo ledger/reglas/lose de la guia.
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

# locale -> archivo de articulos. Solo br por ahora; sumar otra locale es
# agregar su entrada aca + locales/articles-{loc}.json con el mismo esquema.
LOCS = {"br": "locales/articles-br.json"}


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
    urls = []
    for loc, path in LOCS.items():
        L = json.loads((ROOT / path).read_text(encoding="utf-8"))
        home_json = json.loads((ROOT / "locales" / f"{loc}.json").read_text(encoding="utf-8"))
        lang, home = home_json["lang"], home_json["path"]
        base = DOMAIN + home.rstrip("/")

        for art in L["articles"]:
            canonical = f"{base}/{art['slug']}/"

            blocks = render_sections(art["sections"])
            if art.get("faq"):
                faq_html = "\n".join(
                    f'  <details{" open" if i == 0 else ""}><summary>{esc(q)}</summary>'
                    f'<div class="a"><p>{a}</p></div></details>'
                    for i, (q, a) in enumerate(art["faq"]))
                blocks.append((art.get("faqHeading", "Perguntas frequentes"), faq_html))

            toc = '    <ol>\n' + "\n".join(
                f'      <li><a href="#s{i+1}">{esc(h)}</a></li>' for i, (h, _) in enumerate(blocks)
            ) + "\n    </ol>"
            sections = "\n\n".join(
                f'  <h2 id="s{i+1}">{esc(h)}</h2>\n{body}' for i, (h, body) in enumerate(blocks))

            related = "\n".join(
                f'    <a href="{url}">{esc(label)}</a>' for label, url in art["related"])

            graph = [
                {"@type": "WebPage", "@id": canonical, "url": canonical, "name": art["h1"],
                 "description": art["desc"], "inLanguage": lang,
                 "isPartOf": {"@id": f"{DOMAIN}/#website"}},
                {"@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Início", "item": base + "/"},
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

            hreflang_tags = (f'<link rel="alternate" hreflang="{lang}" href="{canonical}">\n'
                              f'<link rel="alternate" hreflang="x-default" href="{canonical}">')

            html = GUIDE_TPL.format(
                lang=lang, title=esc(art["title"]), desc=esc(art["desc"]),
                canonical=canonical, hreflang=hreflang_tags,
                oglocale=lang.replace("-", "_"), home=home,
                h1=esc(art["h1"]), answer=art["answer"],
                meta=esc(art.get("meta", "")),
                homeLabel=esc(art.get("homeLabel", "Início")),
                tocLabel=esc(art.get("tocLabel", "NESTA PÁGINA")),
                toc=toc, sections=sections, related=related,
                sourcesH=esc(art.get("sourcesH", "Fontes")),
                sources="\n".join(f"    <li>{x}</li>" for x in art.get("sources", [])),
                promoK=esc(art["promoK"]), promoP=esc(art["promoP"]), promoBtn=esc(art["promoBtn"]),
                ctaNav=esc(art["ctaNav"]), guideLink=esc(art.get("guideLink", art["h1"])),
                footerNote=esc(art["footerNote"]), ld=ld,
                legalLinks=nav_data.legal_links_html(loc, home),
            )

            out = DIST / loc / art["slug"] / "index.html"
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
