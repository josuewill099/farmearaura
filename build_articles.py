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
    "cl": "locales/articles-cl.json",
    "pe": "locales/articles-pe.json",
    "co": "locales/articles-co.json",
    "esus": "locales/articles-esus.json",
    "uy": "locales/articles-uy.json",
}

# Defaults por locale para los textos de chrome (breadcrumb "home", label del
# TOC, encabezado de fuentes) -- cada articulo puede pisarlos con su propia
# clave si hace falta, pero la mayoria no necesita repetirlos.
HOME_LABEL = {"br": "Início", "us": "Home", "ar": "Inicio", "mx": "Inicio", "es": "Inicio",
              "cl": "Inicio", "pe": "Inicio", "co": "Inicio", "esus": "Inicio", "uy": "Inicio"}
TOC_LABEL = {"br": "NESTA PÁGINA", "us": "ON THIS PAGE", "ar": "EN ESTA PÁGINA",
             "mx": "EN ESTA PÁGINA", "es": "EN ESTA PÁGINA", "cl": "EN ESTA PÁGINA",
             "pe": "EN ESTA PÁGINA", "co": "EN ESTA PÁGINA", "esus": "EN ESTA PÁGINA",
             "uy": "EN ESTA PÁGINA"}
SOURCES_H = {"br": "Fontes", "us": "Sources", "ar": "Fuentes", "mx": "Fuentes", "es": "Fuentes",
             "cl": "Fuentes", "pe": "Fuentes", "co": "Fuentes", "esus": "Fuentes", "uy": "Fuentes"}
FAQ_HEADING = {"br": "Perguntas frequentes", "us": "FAQ", "ar": "Preguntas frecuentes",
               "mx": "Preguntas frecuentes", "es": "Preguntas frecuentes",
               "cl": "Preguntas frecuentes", "pe": "Preguntas frecuentes",
               "co": "Preguntas frecuentes", "esus": "Preguntas frecuentes",
               "uy": "Preguntas frecuentes"}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------- aura quiz
# P1 del audit de GSC: /us/aura-color-test/ y /us/aura-test/ rankeaban en
# posicion ~90 para queries de intencion clarisima de quiz ("what is my
# aura color", "how to find out my aura color") porque la pagina era una
# lista estatica de descripciones, no un quiz real. Este widget cliente
# (sin backend, nada se guarda, mismo espiritu que la calculadora de
# puntos) resuelve eso. 6 preguntas x 4 opciones, cada color aparece en
# exactamente 3 preguntas. Solo se arma para locales con los 8 colores
# (es tiene nomas 4, se deja con la version estatica por ahora).
QUIZ_QUESTIONS_ES = [
    {"q": "Alguien te dice algo injusto sin querer lastimarte. ¿Cómo reaccionás/reaccionas?", "opts": [
        {"t": "Me tomo un segundo, respiro y respondo con calma.", "c": "azul"},
        {"t": "Le resto importancia con una broma y sigo con mi día.", "c": "amarilla"},
        {"t": "Le digo lo que pienso ahí mismo, sin filtro.", "c": "roja"},
        {"t": "Me lo guardo y lo pienso a solas más tarde.", "c": "negra"},
    ]},
    {"q": "¿Qué te hace sentir más en paz?", "opts": [
        {"t": "Un rato en la naturaleza, sin nadie alrededor.", "c": "verde"},
        {"t": "Empezar algo nuevo después de cerrar una etapa.", "c": "blanca"},
        {"t": "Una conversación profunda sobre algo que me haga pensar.", "c": "morada"},
        {"t": "Pasar tiempo con la gente que quiero.", "c": "rosa"},
    ]},
    {"q": "En un grupo de amigos, tu rol natural es...", "opts": [
        {"t": "El o la que escucha y da un consejo cuando hace falta.", "c": "azul"},
        {"t": "El o la que calma las cosas cuando hay tensión.", "c": "verde"},
        {"t": "El o la que toma la iniciativa y arma el plan.", "c": "roja"},
        {"t": "El o la que nota cosas que los demás no ven.", "c": "morada"},
    ]},
    {"q": "Te ofrecen un cambio grande (mudanza, trabajo nuevo). ¿Qué pensás/piensas primero?", "opts": [
        {"t": "Qué emocionante, ¡nuevas posibilidades!", "c": "amarilla"},
        {"t": "Es el momento justo para empezar de nuevo.", "c": "blanca"},
        {"t": "Necesito tiempo a solas para pensarlo bien.", "c": "negra"},
        {"t": "¿Cómo afecta esto a la gente que quiero?", "c": "rosa"},
    ]},
    {"q": "¿Cómo te recuperás/recuperas después de un mal día?", "opts": [
        {"t": "Hablando con alguien de confianza, con calma.", "c": "azul"},
        {"t": "Dejando esa etapa atrás y mirando para adelante.", "c": "blanca"},
        {"t": "Reflexionando a solas hasta entender qué pasó.", "c": "morada"},
        {"t": "Buscando a alguien que me haga sentir mejor.", "c": "rosa"},
    ]},
    {"q": "Te dan una tarea sin instrucciones claras. ¿Qué hacés/haces?", "opts": [
        {"t": "Improviso algo creativo sobre la marcha.", "c": "amarilla"},
        {"t": "Pregunto con calma hasta que quede claro.", "c": "verde"},
        {"t": "Empiezo ya, después ajusto lo que haga falta.", "c": "roja"},
        {"t": "Lo pienso bien antes de dar el primer paso.", "c": "negra"},
    ]},
]

QUIZ_QUESTIONS_EN = [
    {"q": "Someone says something unfair without meaning to hurt you. How do you react?", "opts": [
        {"t": "I take a breath and respond calmly.", "c": "azul"},
        {"t": "I brush it off with a joke and move on.", "c": "amarilla"},
        {"t": "I say what I think right then, no filter.", "c": "roja"},
        {"t": "I keep it to myself and think it over later.", "c": "negra"},
    ]},
    {"q": "What makes you feel most at peace?", "opts": [
        {"t": "Time in nature, away from everyone.", "c": "verde"},
        {"t": "Starting something new after closing a chapter.", "c": "blanca"},
        {"t": "A deep conversation that makes me think.", "c": "morada"},
        {"t": "Spending time with people I love.", "c": "rosa"},
    ]},
    {"q": "In a friend group, your natural role is...", "opts": [
        {"t": "The one who listens and gives advice when needed.", "c": "azul"},
        {"t": "The one who calms things down when there's tension.", "c": "verde"},
        {"t": "The one who takes charge and makes the plan.", "c": "roja"},
        {"t": "The one who notices things others miss.", "c": "morada"},
    ]},
    {"q": "You're offered a big change (move, new job). What's your first thought?", "opts": [
        {"t": "How exciting, new possibilities!", "c": "amarilla"},
        {"t": "This is the right time for a fresh start.", "c": "blanca"},
        {"t": "I need time alone to think it through.", "c": "negra"},
        {"t": "How does this affect the people I love?", "c": "rosa"},
    ]},
    {"q": "How do you recover after a bad day?", "opts": [
        {"t": "Talking it out calmly with someone I trust.", "c": "azul"},
        {"t": "Leaving that chapter behind and looking forward.", "c": "blanca"},
        {"t": "Reflecting alone until I understand what happened.", "c": "morada"},
        {"t": "Finding someone who makes me feel better.", "c": "rosa"},
    ]},
    {"q": "You're given a task with no clear instructions. What do you do?", "opts": [
        {"t": "I improvise something creative on the spot.", "c": "amarilla"},
        {"t": "I calmly ask questions until it's clear.", "c": "verde"},
        {"t": "I start right away and adjust as I go.", "c": "roja"},
        {"t": "I think it through carefully before the first step.", "c": "negra"},
    ]},
]

QUIZ_STRINGS = {
    "es": {"resultLabel": "Tu aura es", "seeMore": "Ver el significado completo", "retry": "Volver a hacer el test"},
    "en": {"resultLabel": "Your aura is", "seeMore": "See the full meaning", "retry": "Retake the quiz"},
}

QUIZ_JS = (SRC / "aura-quiz.js").read_text(encoding="utf-8")
# Fija sin/con voseo -- reutiliza las mismas marcas "X/Y" que ya usa el
# cluster de colores, resueltas segun si la locale es voseante.
_VOSEO_PAIRS = [("reaccionás/reaccionas", "reaccionás", "reaccionas"),
                ("pensás/piensas", "pensás", "piensas"),
                ("recuperás/recuperas", "recuperás", "recuperas"),
                ("hacés/haces", "hacés", "haces")]


def fix_voseo(s, voseo):
    for marker, si, no in _VOSEO_PAIRS:
        s = s.replace(marker, si if voseo else no)
    return s


COLOR_EMOJI = {"azul": "🔵", "amarilla": "🟡", "verde": "🟢", "blanca": "⚪",
               "roja": "🔴", "negra": "⚫", "morada": "🟣", "rosa": "🩷"}

# us no tiene paginas /us/aura-{color}/ dedicadas (esas solo existen para
# los mercados hispanos) -- el resultado del quiz en ingles muestra nombre
# + blurb sin link "ver mas" en vez de inventar un cluster de paginas nuevo
# solo para esto.
ENGLISH_COLOR_INFO = {
    "azul": ("Blue", "Blue auras are associated with calm, communication, and intuition. People with this energy tend to be good listeners who think before they speak and bring a sense of calm wherever they go."),
    "amarilla": ("Yellow", "Yellow auras are associated with optimism, creativity, and mental energy. It's the color most linked to joy and a constant drive to learn new things."),
    "verde": ("Green", "Green auras are associated with balance, healing, and a connection to nature. It shows up most in people who look for harmony between what they feel and what they do."),
    "blanca": ("White", "White auras are associated with purity, elevated spirituality, and new beginnings. It tends to show up in people going through (or seeking) a major change or a period of unusual inner clarity."),
    "roja": ("Red", "Red auras are associated with passion, physical energy, and willpower. It's the color most linked to leadership and action -- people with this energy don't wait for things to happen."),
    "negra": ("Black", "Black auras are often misread. It doesn't mean \"bad energy\" -- it's associated with protection, deep introspection, and sometimes a period of exhaustion that calls for rest."),
    "morada": ("Purple", "Purple (or violet) auras are associated with spirituality, intuition, and wisdom. It's one of the rarer aura colors, and tends to show up in people who are unusually sensitive to what's happening around them."),
    "rosa": ("Pink", "Pink auras are associated with love, tenderness, and emotional sensitivity. It's the color that shows up most in people for whom relationships and caring for others are at the center of everything."),
}


def build_quiz_widget(loc, lang, base, articles_by_slug, voseo):
    color_ids = ["azul", "amarilla", "verde", "blanca", "roja", "negra", "morada", "rosa"]
    colors = {}

    if lang.startswith("es"):
        questions, strings = QUIZ_QUESTIONS_ES, QUIZ_STRINGS["es"]
        for cid in color_ids:
            art = articles_by_slug.get(f"aura-{cid}")
            if not art:
                return ""   # la locale no tiene los 8 colores -- se salta el quiz
            colors[cid] = {"nombre": cid, "emoji": COLOR_EMOJI[cid],
                           "blurb": art["answer"], "url": f"{base}/aura-{cid}/"}
    else:
        questions, strings = QUIZ_QUESTIONS_EN, QUIZ_STRINGS["en"]
        for cid in color_ids:
            name, blurb = ENGLISH_COLOR_INFO[cid]
            colors[cid] = {"nombre": name, "emoji": COLOR_EMOJI[cid], "blurb": blurb, "url": ""}

    qs = [{"q": fix_voseo(q["q"], voseo), "opts": q["opts"]} for q in questions]
    cfg = {"questions": qs, "colors": colors, **strings}
    return ('  <div class="quiz" id="aura-quiz"></div>\n'
            f'  <script>window.AURA_QUIZ={json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))};</script>\n'
            f'  <script>{QUIZ_JS}</script>')


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
    # ar/br/us son los "dueños" del codigo de idioma pelado (es/pt/en) en
    # todo el sitio -- ver GENERIC en build.py. Un hispanohablante sin
    # region que matchee (uy, ve, ec, gt, cr, pr, hn, py, ...) cae en "es"
    # y por default.py eso siempre apunta a ar. Antes de este cambio esas
    # paginas no tenian ese tag y GSC mostraba el trafico de esos paises
    # repartido sin criterio entre las variantes.
    GENERIC = {"ar": "es", "br": "pt", "us": "en"}
    generic_fallback = {}   # slug -> {bare_lang: url}
    for loc, d in data.items():
        for art in d["L"]["articles"]:
            siblings.setdefault(art["slug"], []).append(
                (d["lang"], f"{d['base']}/{art['slug']}/"))
            if loc in GENERIC:
                generic_fallback.setdefault(art["slug"], {})[GENERIC[loc]] = (
                    f"{d['base']}/{art['slug']}/")

    # Paginas donde va el quiz interactivo en vez de (o ademas de) contenido
    # estatico -- ver build_quiz_widget(). "es" se queda con la version
    # estatica por ahora porque solo tiene 4 de los 8 colores.
    QUIZ_SLUGS = {"color-de-aura", "aura-test", "aura-color-test"}

    urls = []
    for loc, d in data.items():
        L, lang, home, base = d["L"], d["lang"], d["home"], d["base"]
        articles_by_slug = {a["slug"]: a for a in L["articles"]}

        for art in L["articles"]:
            canonical = f"{base}/{art['slug']}/"

            quiz_widget = (build_quiz_widget(loc, lang, base, articles_by_slug, loc == "ar")
                           if art["slug"] in QUIZ_SLUGS else "")

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
            fallbacks = generic_fallback.get(art["slug"], {})
            tags = [f'<link rel="alternate" hreflang="{hl}" href="{u}">' for hl, u in group]
            tags += [f'<link rel="alternate" hreflang="{bl}" href="{u}">'
                     for bl, u in fallbacks.items()]
            # x-default prefiere el dueño del idioma pelado (es/pt/en) si
            # esta presente en el grupo; si no, la primera version.
            default_url = fallbacks.get("es") or fallbacks.get("pt") or fallbacks.get("en") or group[0][1]
            tags.append(f'<link rel="alternate" hreflang="x-default" href="{default_url}">')
            hreflang_tags = "\n".join(tags)

            html = GUIDE_TPL.format(
                lang=lang, title=esc(art["title"]), desc=esc(art["desc"]),
                canonical=canonical, hreflang=hreflang_tags,
                oglocale=lang.replace("-", "_"), home=home,
                h1=esc(art["h1"]), answer=art["answer"],
                meta=esc(art.get("meta", "")),
                homeLabel=esc(home_label),
                tocLabel=esc(art.get("tocLabel", TOC_LABEL[loc])),
                quizWidget=quiz_widget,
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
