"""
Datos del menu de navegacion, compartidos por build.py, build_duelos.py y
build_historia.py, para que los links entre calculadora / duelos / duelos
historicos nunca queden desincronizados entre los tres builders.

Cada locale ve solo lo suyo: "duelos" (arquetipos cotidianos) es exclusivo de
ar, asi que solo ar tiene ese item en el menu. Los otros tres locales (mx, es,
br) solo ven calculadora + su propio duelo historico.

nav_html(loc, current) arma el <nav> completo. "current" indica en que pagina
esta el visitante, para marcar aria-current en el item (y sub-item) correcto:

    "home", "duelos", "duelos_ranking", "duelos_historial",
    "historia", "historia_ranking"
"""

NAV_LABELS = {
    "ar": {"calculadora": "Calculadora", "duelos": "Duelos", "historia": "Duelos Históricos",
           "ranking": "Ranking", "historial": "Historial"},
    "mx": {"calculadora": "Calculadora", "historia": "Duelos Históricos", "ranking": "Ranking"},
    "es": {"calculadora": "Calculadora", "historia": "Duelos Históricos", "ranking": "Ranking"},
    "br": {"calculadora": "Calculadora", "historia": "Batalhas", "ranking": "Ranking"},
}

NAV_URLS = {
    "ar": {
        "home": "https://farmearaura.com/",
        "duelos": "https://farmearaura.com/duelos/",
        "duelos_ranking": "https://farmearaura.com/duelos/ranking/",
        "duelos_historial": "https://farmearaura.com/duelos/historial/",
        "historia": "https://farmearaura.com/duelos/historia/",
        "historia_ranking": "https://farmearaura.com/duelos/historia/ranking/",
    },
    "mx": {
        "home": "https://farmearaura.com/mx/",
        "historia": "https://farmearaura.com/mx/duelos/historia/",
        "historia_ranking": "https://farmearaura.com/mx/duelos/historia/ranking/",
    },
    "es": {
        "home": "https://farmearaura.com/es/",
        "historia": "https://farmearaura.com/es/duelos-de-aura/",
        "historia_ranking": "https://farmearaura.com/es/duelos-de-aura/ranking/",
    },
    "br": {
        "home": "https://farmearaura.com/br/",
        "historia": "https://farmearaura.com/br/batalha-de-aura/",
        "historia_ranking": "https://farmearaura.com/br/batalha-de-aura/ranking/",
    },
}


def _esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def nav_html(loc, current):
    L, U = NAV_LABELS[loc], NAV_URLS[loc]

    def cur(key):
        return ' aria-current="page"' if key == current else ""

    parts = ['<a href="%s"%s>%s</a>' % (U["home"], cur("home"), _esc(L["calculadora"]))]

    if loc == "ar":
        parts.append(
            '<div class="item">'
            '<a href="%s"%s>%s</a>'
            '<div class="sub">'
            '<a href="%s"%s>%s</a>'
            '<a href="%s"%s>%s</a>'
            '</div></div>' % (
                U["duelos"], cur("duelos"), _esc(L["duelos"]),
                U["duelos_ranking"], cur("duelos_ranking"), _esc(L["ranking"]),
                U["duelos_historial"], cur("duelos_historial"), _esc(L["historial"]),
            )
        )

    parts.append(
        '<div class="item">'
        '<a href="%s"%s>%s</a>'
        '<div class="sub">'
        '<a href="%s"%s>%s</a>'
        '</div></div>' % (
            U["historia"], cur("historia"), _esc(L["historia"]),
            U["historia_ranking"], cur("historia_ranking"), _esc(L["ranking"]),
        )
    )
    return "".join(parts)
