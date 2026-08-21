"""
Datos del menu de navegacion, compartidos por build.py, build_duelos.py y
build_historia.py, para que los links entre calculadora / duelos / duelos
historicos nunca queden desincronizados entre los tres builders.

Las siete locales tienen ambos duelos: "duelos" (arquetipos cotidianos,
reinventados con modismos locales en cada pais) y "historia" (personajes
historicos). Antes "duelos" era exclusivo de ar; ya no.

nav_html(loc, current) arma el <nav> completo. "current" indica en que pagina
esta el visitante, para marcar aria-current en el item (y sub-item) correcto:

    "home", "duelos", "duelos_ranking", "duelos_historial",
    "historia", "historia_ranking"
"""

NAV_LABELS = {
    "ar": {"calculadora": "Calculadora", "duelos": "Duelos", "historia": "Duelos Históricos",
           "ranking": "Ranking", "historial": "Historial"},
    "mx": {"calculadora": "Calculadora", "duelos": "Duelos", "historia": "Duelos Históricos",
           "ranking": "Ranking", "historial": "Historial"},
    "es": {"calculadora": "Calculadora", "duelos": "Duelos", "historia": "Duelos Históricos",
           "ranking": "Ranking", "historial": "Historial"},
    "br": {"calculadora": "Calculadora", "duelos": "Duelos", "historia": "Batalhas",
           "ranking": "Ranking", "historial": "Histórico"},
    "cl": {"calculadora": "Calculadora", "duelos": "Duelos", "historia": "Duelos Históricos",
           "ranking": "Ranking", "historial": "Historial"},
    "pe": {"calculadora": "Calculadora", "duelos": "Duelos", "historia": "Duelos Históricos",
           "ranking": "Ranking", "historial": "Historial"},
    "co": {"calculadora": "Calculadora", "duelos": "Duelos", "historia": "Duelos Históricos",
           "ranking": "Ranking", "historial": "Historial"},
    "us": {"calculadora": "Calculator", "duelos": "Duels", "historia": "Historical Duels",
           "ranking": "Ranking", "historial": "Recent"},
    "esus": {"calculadora": "Calculadora", "duelos": "Duelos", "historia": "Duelos Históricos",
             "ranking": "Ranking", "historial": "Historial"},
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
        "duelos": "https://farmearaura.com/mx/duelos/",
        "duelos_ranking": "https://farmearaura.com/mx/duelos/ranking/",
        "duelos_historial": "https://farmearaura.com/mx/duelos/historial/",
        "historia": "https://farmearaura.com/mx/duelos/historia/",
        "historia_ranking": "https://farmearaura.com/mx/duelos/historia/ranking/",
    },
    "es": {
        "home": "https://farmearaura.com/es/",
        "duelos": "https://farmearaura.com/es/duelos/",
        "duelos_ranking": "https://farmearaura.com/es/duelos/ranking/",
        "duelos_historial": "https://farmearaura.com/es/duelos/historial/",
        "historia": "https://farmearaura.com/es/duelos-de-aura/",
        "historia_ranking": "https://farmearaura.com/es/duelos-de-aura/ranking/",
    },
    "br": {
        "home": "https://farmearaura.com/br/",
        "duelos": "https://farmearaura.com/br/duelos/",
        "duelos_ranking": "https://farmearaura.com/br/duelos/ranking/",
        "duelos_historial": "https://farmearaura.com/br/duelos/historial/",
        "historia": "https://farmearaura.com/br/batalha-de-aura/",
        "historia_ranking": "https://farmearaura.com/br/batalha-de-aura/ranking/",
    },
    "cl": {
        "home": "https://farmearaura.com/cl/",
        "duelos": "https://farmearaura.com/cl/duelos/",
        "duelos_ranking": "https://farmearaura.com/cl/duelos/ranking/",
        "duelos_historial": "https://farmearaura.com/cl/duelos/historial/",
        "historia": "https://farmearaura.com/cl/duelos/historia/",
        "historia_ranking": "https://farmearaura.com/cl/duelos/historia/ranking/",
    },
    "pe": {
        "home": "https://farmearaura.com/pe/",
        "duelos": "https://farmearaura.com/pe/duelos/",
        "duelos_ranking": "https://farmearaura.com/pe/duelos/ranking/",
        "duelos_historial": "https://farmearaura.com/pe/duelos/historial/",
        "historia": "https://farmearaura.com/pe/duelos/historia/",
        "historia_ranking": "https://farmearaura.com/pe/duelos/historia/ranking/",
    },
    "co": {
        "home": "https://farmearaura.com/co/",
        "duelos": "https://farmearaura.com/co/duelos/",
        "duelos_ranking": "https://farmearaura.com/co/duelos/ranking/",
        "duelos_historial": "https://farmearaura.com/co/duelos/historial/",
        "historia": "https://farmearaura.com/co/duelos/historia/",
        "historia_ranking": "https://farmearaura.com/co/duelos/historia/ranking/",
    },
    "us": {
        "home": "https://farmearaura.com/us/",
        "duelos": "https://farmearaura.com/us/duels/",
        "duelos_ranking": "https://farmearaura.com/us/duels/ranking/",
        "duelos_historial": "https://farmearaura.com/us/duels/historial/",
        "historia": "https://farmearaura.com/us/historical-duels/",
        "historia_ranking": "https://farmearaura.com/us/historical-duels/ranking/",
    },
    "esus": {
        "home": "https://farmearaura.com/es-us/",
        "duelos": "https://farmearaura.com/es-us/duelos/",
        "duelos_ranking": "https://farmearaura.com/es-us/duelos/ranking/",
        "duelos_historial": "https://farmearaura.com/es-us/duelos/historial/",
        "historia": "https://farmearaura.com/es-us/duelos/historia/",
        "historia_ranking": "https://farmearaura.com/es-us/duelos/historia/ranking/",
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
