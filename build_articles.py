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
from datetime import date
from pathlib import Path

import nav_data

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
TODAY = date.today().isoformat()   # sitemap <lastmod> for this build
DOMAIN = "https://farmearaura.com"

GUIDE_TPL = (SRC / "guide.tpl.html").read_text(encoding="utf-8")

# Mismo tag que build.py/build_duelos.py/build_historia.py/build_famosos.py.
GA4_ID = "G-XHZ0MM619V"   # dejalo en "" para no cargar analytics en estas paginas
ANALYTICS = (
    '<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>\n'
    "<script>window.dataLayer=window.dataLayer||[];"
    "function gtag(){dataLayer.push(arguments);}"
    'gtag("js",new Date());gtag("config","%s");</script>'
)
ANALYTICS_TAG = (ANALYTICS % (GA4_ID, GA4_ID)) if GA4_ID else ""

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
    "pt": "locales/articles-pt.json",
    "ec": "locales/articles-ec.json",
}

# Defaults por locale para los textos de chrome (breadcrumb "home", label del
# TOC, encabezado de fuentes) -- cada articulo puede pisarlos con su propia
# clave si hace falta, pero la mayoria no necesita repetirlos.
HOME_LABEL = {"br": "Início", "us": "Home", "ar": "Inicio", "mx": "Inicio", "es": "Inicio",
              "cl": "Inicio", "pe": "Inicio", "co": "Inicio", "esus": "Inicio", "uy": "Inicio",
              "pt": "Início", "ec": "Inicio"}
TOC_LABEL = {"br": "NESTA PÁGINA", "us": "ON THIS PAGE", "ar": "EN ESTA PÁGINA",
             "mx": "EN ESTA PÁGINA", "es": "EN ESTA PÁGINA", "cl": "EN ESTA PÁGINA",
             "pe": "EN ESTA PÁGINA", "co": "EN ESTA PÁGINA", "esus": "EN ESTA PÁGINA",
             "uy": "EN ESTA PÁGINA", "pt": "NESTA PÁGINA", "ec": "EN ESTA PÁGINA"}
SOURCES_H = {"br": "Fontes", "us": "Sources", "ar": "Fuentes", "mx": "Fuentes", "es": "Fuentes",
             "cl": "Fuentes", "pe": "Fuentes", "co": "Fuentes", "esus": "Fuentes", "uy": "Fuentes",
             "pt": "Fontes", "ec": "Fuentes"}
FAQ_HEADING = {"br": "Perguntas frequentes", "us": "FAQ", "ar": "Preguntas frecuentes",
               "mx": "Preguntas frecuentes", "es": "Preguntas frecuentes",
               "cl": "Preguntas frecuentes", "pe": "Preguntas frecuentes",
               "co": "Preguntas frecuentes", "esus": "Preguntas frecuentes",
               "uy": "Preguntas frecuentes", "pt": "Perguntas frequentes", "ec": "Preguntas frecuentes"}


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
                ("hacés/haces", "hacés", "haces"),
                ("decís/dices", "decís", "dices"),
                ("agradecés/agradeces", "agradecés", "agradeces"),
                ("mencionás/mencionas", "mencionás", "mencionas"),
                ("vos solo/tú solo", "vos solo", "tú solo")]


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


def build_quiz_widget(loc, lang, base, articles_by_slug, voseo, quiz_id):
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
    cfg = {"questions": qs, "colors": colors, "quizId": quiz_id, "loc": loc, **strings}
    return ('  <div class="quiz" id="aura-quiz"></div>\n'
            f'  <script>window.AURA_QUIZ={json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))};</script>\n'
            f'  <script>{QUIZ_JS}</script>')


# ------------------------------------------------------------ student quiz
# "aura de estudiante" -- seasonal content para el Dia del Estudiante (AR,
# 21 de septiembre). Mismo motor cliente que el quiz de colores
# (aura-quiz.js no le importa si las categorias son colores o arquetipos de
# estudiante), asi que el costo de un evento estacional nuevo es un set de
# preguntas + un articulo, no un modulo nuevo. URL evergreen (sin anio):
# se actualiza la copia y las fechas cada temporada en vez de crear
# "aura-de-estudiante-2026", "...-2027", etc.
QUIZ_QUESTIONS_ESTUDIANTE_AR = [
    {"q": "Es la noche antes del examen. ¿Qué hacés?", "opts": [
        {"t": "Repaso todo de nuevo aunque ya me lo sé", "c": "prep"},
        {"t": "Armo un resumen de último momento y confío en mi instinto", "c": "impro"},
        {"t": "Le mando un mensaje a alguien que sí estudió", "c": "copia"},
        {"t": "Miro una serie. Ya vi esto mil veces, tranqui", "c": "veterano"},
    ]},
    {"q": "El profesor reparte el examen. ¿Cuál es tu primer movimiento?", "opts": [
        {"t": "Leo todo el examen antes de empezar a responder", "c": "prep"},
        {"t": "Empiezo por la primera pregunta que me suena", "c": "impro"},
        {"t": "Miro de reojo cómo va el de al lado", "c": "copia"},
        {"t": "Respiro hondo. Ya pasé por esto, no es para tanto", "c": "veterano"},
    ]},
    {"q": "Te preguntan algo en clase y no tenés ni idea.", "opts": [
        {"t": "No pasa nada, ya lo tenía anotado para repasar después", "c": "prep"},
        {"t": "Invento una respuesta con total seguridad", "c": "impro"},
        {"t": "Le hago upa con la mirada a un compañero", "c": "copia"},
        {"t": "Digo \"buena pregunta\" y gano tiempo con total calma", "c": "veterano"},
    ]},
    {"q": "¿Cómo es tu cartuchera el día del examen?", "opts": [
        {"t": "Todo ordenado, con birome de repuesto y todo marcado con fibra", "c": "prep"},
        {"t": "Una birome que encontré en el fondo de la mochila", "c": "impro"},
        {"t": "Un acordeón que nunca voy a usar pero por las dudas", "c": "copia"},
        {"t": "Lo mínimo. Ya sé lo que necesito", "c": "veterano"},
    ]},
    {"q": "Terminaste el examen. ¿Qué hacés?", "opts": [
        {"t": "Reviso todo dos veces antes de entregar", "c": "prep"},
        {"t": "Entrego y me voy, ya fue", "c": "impro"},
        {"t": "Comparo respuestas con todo el curso en la puerta", "c": "copia"},
        {"t": "Salgo tranqui, como si nada", "c": "veterano"},
    ]},
    {"q": "¿Qué se dice de vos en el grupo del curso?", "opts": [
        {"t": "El o la que manda el resumen tres días antes", "c": "prep"},
        {"t": "El o la que salva la fecha justo a tiempo", "c": "impro"},
        {"t": "El o la que siempre pregunta \"che, qué hay que estudiar\"", "c": "copia"},
        {"t": "El o la que ya rindió esta materia dos veces en la vida real", "c": "veterano"},
    ]},
]

ESTUDIANTE_INFO = {
    "prep": {"emoji": "📚", "nombre": "Full Prep",
             "blurb": "Llegás con todo estudiado y una birome de repuesto. Tu aura se nota antes de que abras la boca: estás listo para cualquier cosa que te pregunten."},
    "impro": {"emoji": "🎲", "nombre": "Improvisador",
              "blurb": "No estudiaste todo, pero lo que decís suena tan seguro que nadie lo duda. Tu aura se farmea en tiempo real, arriba del escenario."},
    "copia": {"emoji": "😏", "nombre": "Que Copia con Estilo",
              "blurb": "No tenés toda la info, pero sabés exactamente dónde conseguirla. La verdadera habilidad no es saber, es saber a quién preguntarle."},
    "veterano": {"emoji": "😌", "nombre": "Veterano",
                 "blurb": "Ya pasaste por esto tantas veces que nada te agarra desprevenido. Tu superpoder es la calma: nada es tan grave como parece la primera vez."},
}


def build_student_quiz_widget(loc, quiz_id):
    categories = {
        cid: {"nombre": info["nombre"], "emoji": info["emoji"], "blurb": info["blurb"], "url": ""}
        for cid, info in ESTUDIANTE_INFO.items()
    }
    strings = {"resultLabel": "Tu aura de estudiante es",
               "seeMore": "Ver el significado completo", "retry": "Volver a hacer el test"}
    cfg = {"questions": QUIZ_QUESTIONS_ESTUDIANTE_AR, "colors": categories,
           "quizId": quiz_id, "loc": loc, **strings}
    return ('  <div class="quiz" id="aura-quiz"></div>\n'
            f'  <script>window.AURA_QUIZ={json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))};</script>\n'
            f'  <script>{QUIZ_JS}</script>')


# ------------------------------------------------------------- gamer quiz
# "aura-gamer" -- Tier 4 del plan de contenido: quiz-mode standalone, share-
# first. Preguntas en voseo + fix_voseo() para servir las 9 locales
# hispanas desde un unico set (mismo patron que build_quiz_widget con los
# colores); br/pt y us tienen sus propios sets porque difieren en registro
# ("você" vs "tu") o idioma, no solo en un par de verbos.
GAMER_QUESTIONS_ES = [
    {"q": "Perdiste la ranked por un compañero que la cagó. ¿Qué hacés?", "opts": [
        {"t": "Reviso la repetición para ver qué mejorar la próxima", "c": "tryhard"},
        {"t": "Tiro un meme en el chat y me río de todo", "c": "trol"},
        {"t": "Cierro el juego sin decir una palabra", "c": "frio"},
        {"t": "Le dejo un mensaje bien picante antes de salir", "c": "picante"},
    ]},
    {"q": "Hacés una jugada clutch y ganás un 1vX. ¿Cómo reaccionás?", "opts": [
        {"t": "Sigo jugando como si nada, ya lo esperaba", "c": "tryhard"},
        {"t": "Hago un baile random con el personaje", "c": "trol"},
        {"t": "Ni un emoji. Silencio total", "c": "frio"},
        {"t": "Grito re fuerte, que se entere todo el server", "c": "picante"},
    ]},
    {"q": "Se te corta el internet en el peor momento posible. ¿Qué decís?", "opts": [
        {"t": "Nada, reconecto y sigo jugando", "c": "tryhard"},
        {"t": "\"Bueno, así no vale\" entre risas", "c": "trol"},
        {"t": "No digo nada, ni me inmuto", "c": "frio"},
        {"t": "\"SE ME LAGGEÓ\" en mayúsculas, obvio", "c": "picante"},
    ]},
    {"q": "Un desconocido te carrya toda la partida. ¿Cómo se lo agradecés?", "opts": [
        {"t": "Le dejo un GG bien seco y listo", "c": "tryhard"},
        {"t": "Le mando un montón de emojis de fuego", "c": "trol"},
        {"t": "No digo nada, sigo a la siguiente partida", "c": "frio"},
        {"t": "Le escribo un párrafo agradeciéndole re efusivo", "c": "picante"},
    ]},
    {"q": "Estás carryando vos solo a todo el equipo. ¿Lo mencionás?", "opts": [
        {"t": "Ni loco, que se den cuenta solos", "c": "tryhard"},
        {"t": "Sí, con memes de por medio", "c": "trol"},
        {"t": "Ni ahí. Sigo jugando", "c": "frio"},
        {"t": "Sí, se los recuerdo cada dos minutos", "c": "picante"},
    ]},
    {"q": "¿Qué te define mejor en el chat de voz?", "opts": [
        {"t": "Callado, enfocado, cero distracciones", "c": "tryhard"},
        {"t": "El que tira chistes todo el partido", "c": "trol"},
        {"t": "El que casi ni prende el micro", "c": "frio"},
        {"t": "El que se calienta rápido pero se le pasa rápido", "c": "picante"},
    ]},
]

GAMER_INFO_ES = {
    "tryhard": {"emoji": "🎯", "nombre": "Tryhard Silencioso",
                "blurb": "Juega en serio, casi no habla y resuelve todo sin aspavientos. El aura se nota en el resultado, no en el chat."},
    "trol": {"emoji": "😏", "nombre": "Troll con Estilo",
             "blurb": "Se toma todo con humor, hasta perder. Nadie se enoja con este perfil, ni cuando debería perder aura."},
    "frio": {"emoji": "🧊", "nombre": "Frío Total",
             "blurb": "Cara de piedra pase lo que pase. Gana o pierde con la misma expresión, que es la definición exacta de tener aura."},
    "picante": {"emoji": "🔥", "nombre": "Modo Picante",
                "blurb": "Se calienta fácil pero con estilo. Su aura sube y baja rápido, pero nunca aburre."},
}

GAMER_QUESTIONS_PT_BR = [
    {"q": "Você perde a ranqueada por erro de um parceiro de time. O que você faz?", "opts": [
        {"t": "Revejo a repetição pra ver o que melhorar da próxima vez", "c": "tryhard"},
        {"t": "Mando um meme no chat e levo na esportiva", "c": "trol"},
        {"t": "Fecho o jogo sem falar nada", "c": "frio"},
        {"t": "Deixo uma mensagem bem ácida antes de sair", "c": "picante"},
    ]},
    {"q": "Você faz uma jogada clutch e ganha um 1vX. Como reage?", "opts": [
        {"t": "Sigo jogando numa boa, já esperava isso", "c": "tryhard"},
        {"t": "Faço uma dancinha aleatória com o personagem", "c": "trol"},
        {"t": "Nem um emoji. Silêncio total", "c": "frio"},
        {"t": "Grito tão alto que o servidor inteiro escuta", "c": "picante"},
    ]},
    {"q": "Sua internet cai bem na pior hora possível. O que você diz?", "opts": [
        {"t": "Nada, só reconecto e continuo jogando", "c": "tryhard"},
        {"t": "\"Ah, então não vale\" rindo", "c": "trol"},
        {"t": "Nada. Nem me abalo", "c": "frio"},
        {"t": "\"DEU LAG\" em caixa alta, óbvio", "c": "picante"},
    ]},
    {"q": "Um desconhecido carrega o time inteiro na partida. Como você agradece?", "opts": [
        {"t": "Mando um \"gg\" seco e sigo", "c": "tryhard"},
        {"t": "Mando uma sequência enorme de emoji de fogo", "c": "trol"},
        {"t": "Não digo nada, já entro na próxima partida", "c": "frio"},
        {"t": "Escrevo um parágrafo inteiro de agradecimento", "c": "picante"},
    ]},
    {"q": "Você está carregando o time sozinho. Você comenta isso?", "opts": [
        {"t": "De jeito nenhum, que percebam sozinhos", "c": "tryhard"},
        {"t": "Sim, com memes no meio", "c": "trol"},
        {"t": "Nem pensar. Sigo jogando", "c": "frio"},
        {"t": "Sim, e lembro todo mundo a cada dois minutos", "c": "picante"},
    ]},
    {"q": "O que mais define você no chat de voz?", "opts": [
        {"t": "Quieto, focado, zero distração", "c": "tryhard"},
        {"t": "Aquele que solta piada o jogo inteiro", "c": "trol"},
        {"t": "Aquele que quase nem liga o microfone", "c": "frio"},
        {"t": "Esquenta rápido, mas também esfria rápido", "c": "picante"},
    ]},
]

GAMER_QUESTIONS_PT_PT = [
    {"q": "Perdes a ranqueada por erro de um colega de equipa. O que fazes?", "opts": [
        {"t": "Revejo a repetição para ver o que melhorar da próxima vez", "c": "tryhard"},
        {"t": "Mando um meme no chat e levo na brincadeira", "c": "trol"},
        {"t": "Fecho o jogo sem dizer nada", "c": "frio"},
        {"t": "Deixo uma mensagem bem ácida antes de sair", "c": "picante"},
    ]},
    {"q": "Fazes uma jogada clutch e ganhas um 1vX. Como reages?", "opts": [
        {"t": "Continuo a jogar na boa, já esperava isso", "c": "tryhard"},
        {"t": "Faço uma dancinha aleatória com a personagem", "c": "trol"},
        {"t": "Nem um emoji. Silêncio total", "c": "frio"},
        {"t": "Grito tão alto que o servidor inteiro ouve", "c": "picante"},
    ]},
    {"q": "A tua internet cai mesmo na pior altura possível. O que dizes?", "opts": [
        {"t": "Nada, reconecto e continuo a jogar", "c": "tryhard"},
        {"t": "\"Então isso não conta\" a rir", "c": "trol"},
        {"t": "Nada. Nem me abalo", "c": "frio"},
        {"t": "\"DEU LAG\" em maiúsculas, óbvio", "c": "picante"},
    ]},
    {"q": "Um desconhecido carrega a equipa toda na partida. Como agradeces?", "opts": [
        {"t": "Deixo um \"gg\" seco e sigo em frente", "c": "tryhard"},
        {"t": "Mando uma sequência enorme de emoji de fogo", "c": "trol"},
        {"t": "Não digo nada, entro logo na próxima partida", "c": "frio"},
        {"t": "Escrevo um parágrafo inteiro de agradecimento", "c": "picante"},
    ]},
    {"q": "Estás a carregar a equipa toda sozinho. Comentas isso?", "opts": [
        {"t": "De maneira nenhuma, que percebam sozinhos", "c": "tryhard"},
        {"t": "Sim, com memes pelo meio", "c": "trol"},
        {"t": "Nem pensar. Continuo a jogar", "c": "frio"},
        {"t": "Sim, e lembro toda a gente a cada dois minutos", "c": "picante"},
    ]},
    {"q": "O que te define melhor no chat de voz?", "opts": [
        {"t": "Calado, focado, zero distrações", "c": "tryhard"},
        {"t": "Aquele que conta piadas o jogo todo", "c": "trol"},
        {"t": "Aquele que quase nunca liga o microfone", "c": "frio"},
        {"t": "Aquece depressa, mas também arrefece depressa", "c": "picante"},
    ]},
]

GAMER_INFO_PT_BR = {
    "tryhard": {"emoji": "🎯", "nombre": "Tryhard Silencioso",
                "blurb": "Joga a sério, quase não fala e resolve tudo sem alarde. A aura aparece no resultado, não no chat."},
    "trol": {"emoji": "😏", "nombre": "Troll com Estilo",
             "blurb": "Leva tudo na esportiva, até perder. Ninguém fica bravo com esse perfil, nem quando deveria estar perdendo aura."},
    "frio": {"emoji": "🧊", "nombre": "Frio Total",
             "blurb": "Cara de paisagem não importa o que aconteça. Ganha ou perde com a mesma expressão, que é a definição exata de ter aura."},
    "picante": {"emoji": "🔥", "nombre": "Modo Ácido",
                "blurb": "Esquenta fácil, mas com estilo. A aura sobe e desce rápido, mas nunca fica sem graça."},
}

GAMER_INFO_PT_PT = {
    "tryhard": {"emoji": "🎯", "nombre": "Tryhard Silencioso",
                "blurb": "Joga a sério, quase não fala e resolve tudo sem alarido. A aura aparece no resultado, não no chat."},
    "trol": {"emoji": "😏", "nombre": "Troll com Estilo",
             "blurb": "Leva tudo na brincadeira, até perder. Ninguém fica chateado com este perfil, nem quando devia estar a perder aura."},
    "frio": {"emoji": "🧊", "nombre": "Frio Total",
             "blurb": "Cara de pedra não importa o que aconteça. Ganha ou perde com a mesma expressão, que é a definição exata de ter aura."},
    "picante": {"emoji": "🔥", "nombre": "Modo Ácido",
                "blurb": "Aquece facilmente, mas com estilo. A aura sobe e desce depressa, mas nunca é maçador."},
}

GAMER_QUESTIONS_EN = [
    {"q": "You lose ranked because of a teammate's mistake. What do you do?", "opts": [
        {"t": "Review the replay to see what to improve next time", "c": "tryhard"},
        {"t": "Drop a meme in chat and laugh it off", "c": "trol"},
        {"t": "Close the game without saying a word", "c": "frio"},
        {"t": "Leave a spicy message in chat before you go", "c": "picante"},
    ]},
    {"q": "You pull off a clutch 1vX win. How do you react?", "opts": [
        {"t": "Keep playing like it's nothing, saw it coming", "c": "tryhard"},
        {"t": "Hit a random dance emote with the character", "c": "trol"},
        {"t": "Not a single emoji. Total silence", "c": "frio"},
        {"t": "Scream loud enough for the whole server to hear", "c": "picante"},
    ]},
    {"q": "Your internet cuts out at the worst possible moment. What do you say?", "opts": [
        {"t": "Nothing, just reconnect and keep playing", "c": "tryhard"},
        {"t": "\"Well, that doesn't count\" laughing", "c": "trol"},
        {"t": "Nothing. Don't even flinch", "c": "frio"},
        {"t": "\"MY GAME LAGGED\" in all caps, obviously", "c": "picante"},
    ]},
    {"q": "A stranger carries the entire match. How do you thank them?", "opts": [
        {"t": "Drop a dry \"GG\" and move on", "c": "tryhard"},
        {"t": "Send a wall of fire emojis", "c": "trol"},
        {"t": "Say nothing, queue for the next match", "c": "frio"},
        {"t": "Write them a whole paragraph of thanks", "c": "picante"},
    ]},
    {"q": "You're solo-carrying the entire team. Do you mention it?", "opts": [
        {"t": "No way, let them figure it out themselves", "c": "tryhard"},
        {"t": "Yeah, with memes attached", "c": "trol"},
        {"t": "Not a chance. Keep playing", "c": "frio"},
        {"t": "Yes, and I remind them every two minutes", "c": "picante"},
    ]},
    {"q": "What best describes you in voice chat?", "opts": [
        {"t": "Quiet, focused, zero distractions", "c": "tryhard"},
        {"t": "The one cracking jokes all match", "c": "trol"},
        {"t": "The one who barely turns the mic on", "c": "frio"},
        {"t": "Quick to get heated, quick to cool down", "c": "picante"},
    ]},
]

GAMER_INFO_EN = {
    "tryhard": {"emoji": "🎯", "nombre": "Silent Tryhard",
                "blurb": "Plays for real, barely talks, and clears everything without any fuss. The aura shows up in the result, not the chat."},
    "trol": {"emoji": "😏", "nombre": "Stylish Troll",
             "blurb": "Takes everything as a joke, even losing. Nobody gets mad at this one, not even when they should be losing aura."},
    # Nota: aura-quiz.js pasa el blurb por esc() al renderizarlo, asi que aca
    # va un guion largo literal, no la entidad HTML (&mdash; se mostraria tal cual).
    "frio": {"emoji": "🧊", "nombre": "Total Ice",
             "blurb": "Same poker face no matter what happens. Wins or loses with the exact same expression — the literal definition of having aura."},
    "picante": {"emoji": "🔥", "nombre": "Spicy Mode",
                "blurb": "Heats up fast, but with style. The aura swings up and down quickly, but it's never boring."},
}

GAMER_STRINGS = {
    "es": {"resultLabel": "Tu aura gamer es", "seeMore": "Ver el significado completo", "retry": "Volver a hacer el test"},
    "pt": {"resultLabel": "Sua aura gamer é", "seeMore": "Ver o significado completo", "retry": "Refazer o teste"},
    "pt-pt": {"resultLabel": "A tua aura gamer é", "seeMore": "Ver o significado completo", "retry": "Refazer o teste"},
    "en": {"resultLabel": "Your gamer aura is", "seeMore": "See the full meaning", "retry": "Retake the quiz"},
}

def build_gamer_quiz_widget(loc, lang, voseo, quiz_id):
    if lang.startswith("pt"):
        questions = GAMER_QUESTIONS_PT_PT if loc == "pt" else GAMER_QUESTIONS_PT_BR
        info = GAMER_INFO_PT_PT if loc == "pt" else GAMER_INFO_PT_BR
        strings = GAMER_STRINGS["pt-pt"] if loc == "pt" else GAMER_STRINGS["pt"]
    elif lang.startswith("en"):
        questions, info, strings = GAMER_QUESTIONS_EN, GAMER_INFO_EN, GAMER_STRINGS["en"]
    else:
        questions = [{"q": fix_voseo(q["q"], voseo), "opts": q["opts"]} for q in GAMER_QUESTIONS_ES]
        info, strings = GAMER_INFO_ES, GAMER_STRINGS["es"]

    categories = {cid: {"nombre": c["nombre"], "emoji": c["emoji"], "blurb": c["blurb"], "url": ""}
                  for cid, c in info.items()}
    cfg = {"questions": questions, "colors": categories, "quizId": quiz_id, "loc": loc, **strings}
    return ('  <div class="quiz" id="aura-quiz"></div>\n'
            f'  <script>window.AURA_QUIZ={json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))};</script>\n'
            f'  <script>{QUIZ_JS}</script>')


# ------------------------------------------------------- static quiz helper
# Version simplificada de build_gamer_quiz_widget para quizzes de una sola
# locale (no necesitan ramificar por idioma ni voseo): aura-futbol (AR) y
# aura-anime (BR) se embeben en sus respectivos articulos editoriales ya
# existentes en vez de crear una pagina nueva que compita por las mismas
# queries -- ver notas del plan de contenido Tier 4.
def build_static_quiz_widget(loc, quiz_id, questions, info, strings):
    categories = {cid: {"nombre": c["nombre"], "emoji": c["emoji"], "blurb": c["blurb"], "url": ""}
                  for cid, c in info.items()}
    cfg = {"questions": questions, "colors": categories, "quizId": quiz_id, "loc": loc, **strings}
    return ('  <div class="quiz" id="aura-quiz"></div>\n'
            f'  <script>window.AURA_QUIZ={json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))};</script>\n'
            f'  <script>{QUIZ_JS}</script>')


FUTBOL_QUESTIONS_AR = [
    {"q": "Le hacés un caño a un rival en el picado. ¿Qué hacés después?", "opts": [
        {"t": "Sigo jugando como si nada", "c": "crack"},
        {"t": "Miro a ver si alguien lo vio", "c": "figura"},
        {"t": "Ni cambio la cara", "c": "roca"},
        {"t": "Grito y se lo señalo al que se la hice", "c": "nervioso"},
    ]},
    {"q": "Errás un gol cantado con el arco vacío. ¿Cómo reaccionás?", "opts": [
        {"t": "Sigo corriendo, ya fue", "c": "crack"},
        {"t": "Me río de mí mismo antes que los demás", "c": "figura"},
        {"t": "Cara de piedra, ni un gesto", "c": "roca"},
        {"t": "Pateo el aire y puteo un rato", "c": "nervioso"},
    ]},
    {"q": "El árbitro te cobra un offside que no fue. ¿Qué decís?", "opts": [
        {"t": "Nada, sigo jugando", "c": "crack"},
        {"t": "Un comentario picante pero con onda", "c": "figura"},
        {"t": "Ni lo miro", "c": "roca"},
        {"t": "Le reclamo un buen rato", "c": "nervioso"},
    ]},
    {"q": "Atajás un penal en la última jugada. ¿Cómo festejás?", "opts": [
        {"t": "Me paro y sigo, ni un grito", "c": "crack"},
        {"t": "Un festejo armado, coreografía y todo", "c": "figura"},
        {"t": "Ni un gesto, como si fuera de rutina", "c": "roca"},
        {"t": "Grito tan fuerte que se escucha en la otra cancha", "c": "nervioso"},
    ]},
    {"q": "Un compañero te putea por un pase mal dado. ¿Qué hacés?", "opts": [
        {"t": "Sigo jugando, no le doy bola", "c": "crack"},
        {"t": "Le respondo con un chiste", "c": "figura"},
        {"t": "Ni lo escucho", "c": "roca"},
        {"t": "Le devuelvo la puteada", "c": "nervioso"},
    ]},
    {"q": "¿Cómo te definen en el equipo?", "opts": [
        {"t": "El que resuelve sin hacer ruido", "c": "crack"},
        {"t": "El que siempre tiene una gambeta de más", "c": "figura"},
        {"t": "El que no cambia la cara ni ganando ni perdiendo", "c": "roca"},
        {"t": "El que se prende fácil en cualquier discusión", "c": "nervioso"},
    ]},
]

FUTBOL_INFO_AR = {
    "crack": {"emoji": "🐐", "nombre": "Crack Silencioso",
              "blurb": "Resuelve todo sin necesidad de mostrarlo. Su aura se nota en el resultado, no en el festejo."},
    "figura": {"emoji": "😏", "nombre": "Figura del Picado",
               "blurb": "Se luce con estilo, hasta cuando nadie se lo pidió. Nunca se toma nada del todo en serio."},
    "roca": {"emoji": "🧊", "nombre": "Roca de Área",
             "blurb": "Cara de piedra pase lo que pase. Ganar o perder le cambia la cara lo mismo: nada."},
    "nervioso": {"emoji": "🔥", "nombre": "Nueve Nervioso",
                 "blurb": "Se calienta rápido y lo demuestra. Su aura sube y baja en el mismo partido."},
}

FUTBOL_STRINGS_ES = {"resultLabel": "Tu aura futbolera es", "seeMore": "Ver el significado completo",
                      "retry": "Volver a hacer el test"}

ANIME_QUESTIONS_BR = [
    {"q": "Você resolve um problema gigante em segundos. Como reage?", "opts": [
        {"t": "Fico calado e sigo andando", "c": "piccolo"},
        {"t": "Solto uma piada e sigo em frente", "c": "gojo"},
        {"t": "Dou de ombros, nem foi difícil", "c": "saitama"},
        {"t": "Nem comento, só sigo pro próximo problema", "c": "levi"},
    ]},
    {"q": "Alguém tenta te provocar no meio de uma treta grande. O que você faz?", "opts": [
        {"t": "Fico sério e não respondo", "c": "piccolo"},
        {"t": "Devolvo com outra provocação, sorrindo", "c": "gojo"},
        {"t": "Nem escuto, tô entediado", "c": "saitama"},
        {"t": "Encaro rápido e resolvo sem falar", "c": "levi"},
    ]},
    {"q": "Você vence uma disputa que parecia impossível. Como comemora?", "opts": [
        {"t": "Não comemoro, sigo minha rotina", "c": "piccolo"},
        {"t": "Faço pose e curto o momento", "c": "gojo"},
        {"t": "Nem foi empolgante, próximo", "c": "saitama"},
        {"t": "Só confirmo que terminou e sigo", "c": "levi"},
    ]},
    {"q": "Um adversário jura que vai te superar. Sua resposta?", "opts": [
        {"t": "Nada. O silêncio já responde", "c": "piccolo"},
        {"t": "Rio e aceito o desafio na hora", "c": "gojo"},
        {"t": "Espero que seja mais interessante que o último", "c": "saitama"},
        {"t": "Não perco tempo respondendo", "c": "levi"},
    ]},
    {"q": "No meio de uma crise, todo mundo entra em pânico. E você?", "opts": [
        {"t": "Fico parado, calculando o próximo passo", "c": "piccolo"},
        {"t": "Brinco com a situação pra aliviar o clima", "c": "gojo"},
        {"t": "Acho estranho tanto alarde por tão pouco", "c": "saitama"},
        {"t": "Dou ordens rápidas e direto ao ponto", "c": "levi"},
    ]},
    {"q": "O que mais te define numa batalha?", "opts": [
        {"t": "Paciência e silêncio", "c": "piccolo"},
        {"t": "Confiança e humor", "c": "gojo"},
        {"t": "Poder tão grande que virou tédio", "c": "saitama"},
        {"t": "Precisão fria, sem espaço pra erro", "c": "levi"},
    ]},
]

ANIME_INFO_BR = {
    "piccolo": {"emoji": "🗿", "nombre": "Estilo Piccolo",
                "blurb": "Calma extrema, quase não fala. Resolve tudo em silêncio e deixa o resultado falar por si."},
    "gojo": {"emoji": "😏", "nombre": "Estilo Gojo",
             "blurb": "Confiança displicente, sempre com uma piada solta. Encara qualquer desafio como se fosse fácil."},
    "saitama": {"emoji": "😐", "nombre": "Estilo Saitama",
                "blurb": "Tão poderoso que ficou entediado. A maior ironia da aura: parecer aborrecido com o próprio poder."},
    "levi": {"emoji": "🧊", "nombre": "Estilo Levi",
             "blurb": "Frieza cirúrgica e zero espaço pra erro. Resolve rápido e sem gastar uma palavra a mais."},
}

ANIME_STRINGS_PT = {"resultLabel": "Sua aura de anime é", "seeMore": "Ver o significado completo",
                     "retry": "Refazer o teste"}


# --------------------------------------------------------------- aura counter
# "contador de aura"/"contador de farmear aura": trafico real (GSC) sin
# volumen en Ahrefs todavia (el termino es demasiado nuevo), pero sin
# competencia dedicada -- distinto de la calculadora (7 preguntas, un
# resultado): esto es un boton que se puede tocar cuantas veces se quiera,
# suma o resta un monto random con su motivo, y persiste en localStorage.
# Arranco en AR y lo fui sumando al resto de las locales -- se activa solo
# con que exista alguno de los slugs de COUNTER_SLUGS en su propio
# articles-{loc}.json, sin gating explicito de locale aca.
COUNTER_JS = (SRC / "aura-counter.js").read_text(encoding="utf-8")

# Los eventos ya estaban escritos en preterito ("contestaste", "ganaste"),
# que en español es identico entre voseo y tuteo -- por eso una sola lista
# sirve para las 8 locales hispanas, salvo "posta?" (modismo AR/UY) que se
# cambia a "en serio?" para el resto.
COUNTER_EVENTS_ES_VOSEO = [
    {"pts": 250, "t": "Contestaste tarde y quedó mejor."},
    {"pts": 180, "t": "No mandaste el mensaje que habías escrito con bronca."},
    {"pts": 900, "t": "Te fuiste de la previa sin avisar y quedó como un mood."},
    {"pts": 120, "t": "Le bajaste el volumen a tu propia queja."},
    {"pts": 2000, "t": "Ganaste una discusión sin levantar la voz."},
    {"pts": 75, "t": "Caminaste como si supieras a dónde ibas, aunque no tenías idea."},
    {"pts": 300, "t": "No le diste bola a un comentario que buscaba pelea."},
    {"pts": 50, "t": "Te reíste último y en voz baja."},
    {"pts": 5000, "t": "Alguien te copió el look sin avisar."},
    {"pts": 150, "t": "Dijiste \"no pasa nada\" y de verdad no te importó."},
    {"pts": 400, "t": "Saliste del grupo sin dar explicaciones."},
    {"pts": 999, "t": "Bostezaste en un momento tenso y quedó como total indiferencia."},
    {"pts": -300, "t": "Explicaste un chiste que no funcionó."},
    {"pts": -150, "t": "Le pusiste \"visto\" a alguien y después contestaste igual."},
    {"pts": -1000, "t": "Te reíste de tu propio chiste antes que los demás."},
    {"pts": -50, "t": "Preguntaste \"posta?\" tres veces seguidas."},
    {"pts": -700, "t": "Pediste que te den bola en el grupo."},
    {"pts": -200, "t": "Se te cortó la voz pidiendo algo obvio."},
]
COUNTER_EVENTS_ES_TUTEO = [
    dict(e, t=e["t"].replace("posta?", "en serio?")) for e in COUNTER_EVENTS_ES_VOSEO
]

COUNTER_EVENTS_PT = [
    {"pts": 250, "t": "Respondeu atrasado e ficou melhor assim."},
    {"pts": 180, "t": "Não mandou aquela mensagem de raiva que tinha escrito."},
    {"pts": 900, "t": "Saiu da festa sem avisar e ficou parecendo estiloso."},
    {"pts": 120, "t": "Baixou o tom da própria reclamação."},
    {"pts": 2000, "t": "Ganhou uma discussão sem levantar a voz."},
    {"pts": 75, "t": "Andou como se soubesse pra onde estava indo, mesmo sem saber."},
    {"pts": 300, "t": "Ignorou um comentário que só queria brigar."},
    {"pts": 50, "t": "Riu por último e bem baixinho."},
    {"pts": 5000, "t": "Alguém copiou o seu visual sem avisar."},
    {"pts": 150, "t": "Disse \"não tem problema\" e realmente não ligou."},
    {"pts": 400, "t": "Saiu do grupo sem dar satisfação."},
    {"pts": 999, "t": "Bocejou num momento tenso e pareceu indiferença total."},
    {"pts": -300, "t": "Explicou uma piada que não funcionou."},
    {"pts": -150, "t": "Deixou no \"visto\" e depois respondeu do mesmo jeito."},
    {"pts": -1000, "t": "Riu da própria piada antes de todo mundo."},
    {"pts": -50, "t": "Perguntou \"sério?\" três vezes seguidas."},
    {"pts": -700, "t": "Pediu atenção no grupo."},
    {"pts": -200, "t": "A voz falhou pedindo algo óbvio."},
]

COUNTER_EVENTS_EN = [
    {"pts": 250, "t": "You replied late and it landed better."},
    {"pts": 180, "t": "You didn't send the message you typed out of anger."},
    {"pts": 900, "t": "You left the party without saying bye and it read as a whole mood."},
    {"pts": 120, "t": "You turned down the volume on your own complaint."},
    {"pts": 2000, "t": "You won an argument without raising your voice."},
    {"pts": 75, "t": "You walked like you knew where you were going, even though you had no idea."},
    {"pts": 300, "t": "You ignored a comment that was fishing for a fight."},
    {"pts": 50, "t": "You laughed last, and quietly."},
    {"pts": 5000, "t": "Someone copied your fit without telling you."},
    {"pts": 150, "t": "You said \"it's fine\" and actually meant it."},
    {"pts": 400, "t": "You left the group chat without an explanation."},
    {"pts": 999, "t": "You yawned in a tense moment and it read as total indifference."},
    {"pts": -300, "t": "You explained a joke that didn't land."},
    {"pts": -150, "t": "You left someone on read and then replied anyway."},
    {"pts": -1000, "t": "You laughed at your own joke before anyone else did."},
    {"pts": -50, "t": "You asked \"wait, really?\" three times in a row."},
    {"pts": -700, "t": "You asked to be noticed in the group chat."},
    {"pts": -200, "t": "Your voice cracked asking for something obvious."},
]

COUNTER_NUMFMT = {"ar": "es-AR", "mx": "es-MX", "es": "es-ES", "br": "pt-BR",
                   "cl": "es-CL", "pe": "es-PE", "co": "es-CO", "us": "en-US",
                   "esus": "es-US", "uy": "es-UY", "pt": "pt", "ec": "es-EC"}
COUNTER_VOSEO_LOCS = {"ar", "uy"}


def build_counter_widget(loc):
    if loc == "us":
        strings = {"label": "YOUR AURA", "intro": "Tap the button to add or lose aura on the spot.",
                   "cta": "FARM AURA", "reset": "Reset counter",
                   "presetNote": "you added that one yourself"}
        events = COUNTER_EVENTS_EN
    elif loc == "br":
        strings = {"label": "SUA AURA", "intro": "Toque no botão e some ou tire aura na hora.",
                   "cta": "FARMAR AURA", "reset": "Reiniciar contador",
                   "presetNote": "você somou na mão"}
        events = COUNTER_EVENTS_PT
    elif loc == "pt":
        strings = {"label": "A TUA AURA", "intro": "Toca no botão e soma ou tira aura na hora.",
                   "cta": "FARMAR AURA", "reset": "Reiniciar contador",
                   "presetNote": "foste tu que somaste isso"}
        events = COUNTER_EVENTS_PT
    else:
        voseo = loc in COUNTER_VOSEO_LOCS
        strings = {
            "label": "TU AURA",
            "intro": ("Tocá el botón y sumá o restá aura al toque." if voseo
                      else "Toca el botón y suma o resta aura al toque."),
            "cta": "FARMEAR AURA",
            "reset": "Reiniciar contador",
            "presetNote": "lo sumaste vos" if voseo else "lo sumaste tú",
        }
        events = COUNTER_EVENTS_ES_VOSEO if voseo else COUNTER_EVENTS_ES_TUTEO

    cfg = {
        "key": loc,
        "numfmt": COUNTER_NUMFMT[loc],
        "events": events,
        "presets": [50, 100, 200, 300, 500, 1000],
        **strings,
    }
    return ('  <div class="counter" id="aura-counter"></div>\n'
            f'  <script>window.AURA_COUNTER={json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))};</script>\n'
            f'  <script>{COUNTER_JS}</script>')


def render_sections(sections):
    out = []
    for h, blocks in sections:
        inner = []
        for b in blocks:
            if isinstance(b, dict) and "ul" in b:
                inner.append('  <ul class="plain">\n' + "\n".join(
                    f"    <li>{x}</li>" for x in b["ul"]) + "\n  </ul>")
            elif isinstance(b, dict) and "dl" in b:
                # Mismo shape que el "Glosario" de build_guide() (dl.glo ya
                # tiene estilos en guide.tpl.html) -- reusado aca para la
                # pagina de lexico, que necesita listas de definicion, no
                # bullets sueltos.
                inner.append('  <dl class="glo">\n' + "\n".join(
                    f"    <dt>{esc(t)}</dt><dd>{d}</dd>" for t, d in b["dl"]) + "\n  </dl>")
            elif isinstance(b, dict) and "embed" in b:
                # Embed oficial (oEmbed de TikTok, etc.) pegado tal cual --
                # sin envolver en <p>, que rompe el blockquote de embed.js.
                inner.append(f'  <div class="embed-wrap">{b["embed"]}</div>')
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
    COUNTER_SLUGS = {"contador-de-aura", "contador-de-farmar-aura", "aura-counter"}
    STUDENT_QUIZ_SLUGS = {"aura-de-estudiante"}
    # Locales voseantes -- afecta la conjugacion de las preguntas del quiz
    # (ver fix_voseo). Antes solo estaba "ar" hardcodeado aca, lo que le
    # daba tuteo por error a uy cuando se sumo (uy tambien es voseante).
    VOSEO_LOCS = {"ar", "uy"}

    urls = []
    for loc, d in data.items():
        L, lang, home, base = d["L"], d["lang"], d["home"], d["base"]
        articles_by_slug = {a["slug"]: a for a in L["articles"]}

        for art in L["articles"]:
            canonical = f"{base}/{art['slug']}/"

            if art["slug"] in QUIZ_SLUGS:
                quiz_widget = build_quiz_widget(loc, lang, base, articles_by_slug, loc in VOSEO_LOCS, art["slug"])
            elif art["slug"] in COUNTER_SLUGS:
                quiz_widget = build_counter_widget(loc)
            elif art["slug"] in STUDENT_QUIZ_SLUGS:
                quiz_widget = build_student_quiz_widget(loc, art["slug"])
            elif art["slug"] == "aura-gamer":
                quiz_widget = build_gamer_quiz_widget(loc, lang, loc in VOSEO_LOCS, art["slug"])
            elif art["slug"] == "aura-futbol":
                quiz_widget = build_static_quiz_widget(loc, art["slug"], FUTBOL_QUESTIONS_AR, FUTBOL_INFO_AR, FUTBOL_STRINGS_ES)
            elif art["slug"] == "aura-anime":
                quiz_widget = build_static_quiz_widget(loc, art["slug"], ANIME_QUESTIONS_BR, ANIME_INFO_BR, ANIME_STRINGS_PT)
            else:
                quiz_widget = ""

            blocks = render_sections(art["sections"])
            glossary_terms = [
                (t, d) for _, section_blocks in art["sections"]
                for b in section_blocks if isinstance(b, dict) and "dl" in b
                for t, d in b["dl"]
            ]
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
            if glossary_terms:
                graph.append({"@type": "DefinedTermSet", "@id": canonical + "#lexico",
                              "name": art["h1"], "hasDefinedTerm": [
                                  {"@type": "DefinedTerm", "@id": f"{canonical}#term-{i}",
                                   "name": re.sub("<[^>]+>", "", t).split(" / ")[0],
                                   "description": re.sub("<[^>]+>", "", d),
                                   "inDefinedTermSet": canonical + "#lexico"}
                                  for i, (t, d) in enumerate(glossary_terms)]})
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
                ogimage=f"{DOMAIN}/og-{loc}.jpg",
                h1=esc(art["h1"]), answer=art["answer"],
                meta=art.get("meta", ""),
                homeLabel=esc(home_label),
                tocLabel=esc(art.get("tocLabel", TOC_LABEL[loc])),
                quizWidget=quiz_widget, analytics=ANALYTICS_TAG,
                toc=toc, sections=sections, related=related,
                sourcesH=esc(art.get("sourcesH", SOURCES_H[loc])),
                sources="\n".join(f"    <li>{x}</li>" for x in art.get("sources", [])),
                promoK=esc(art["promoK"]), promoP=esc(art["promoP"]), promoBtn=esc(art["promoBtn"]),
                promoUrl=art.get("promoUrl", home),
                ctaNav=esc(art["ctaNav"]), guideLink=esc(art.get("guideLink", art["h1"])),
                navblock=(f'<nav class="nav">{nav_data.nav_html(loc, "contador")}</nav>'
                          if art["slug"] in COUNTER_SLUGS
                          else f'<a class="cta" href="{home}">{esc(art["ctaNav"])}</a>'),
                footerNote=art["footerNote"], ld=ld,
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
                "<url><loc>%s</loc><lastmod>%s</lastmod>"
                "<changefreq>monthly</changefreq></url>\n" % (u, TODAY) for u in nuevas)
            xml = re.sub(r"</urlset>", bloque + "</urlset>", xml, count=1)
            sm.write_text(xml, encoding="utf-8")
            print("  -> sitemap.xml (+%d URLs)" % len(nuevas))


if __name__ == "__main__":
    print("Construyendo articulos standalone...")
    build()
    print("Listo.")
