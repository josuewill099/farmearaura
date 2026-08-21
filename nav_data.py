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

legal_links_html(loc, home) arma la linea "farmearaura.com · Privacidad ·
Cookies · ..." que build.py ya usaba en las paginas de guia/legal, pero que
las paginas de duelos/historia nunca tuvieron -- build_duelos.py y
build_historia.py son scripts aparte, sin acceso al LEGAL/LEGAL_OF de
build.py. Duplica esa tabla (es chica y cambia poco) en vez de importar
build.py entero solo para esto.
"""

import json
from pathlib import Path

_ROOT = Path(__file__).parent

LEGAL_OF = {"ar": "es", "mx": "es", "es": "es", "br": "pt",
            "cl": "es", "pe": "es", "co": "es", "us": "en", "esus": "es"}
_legal_cache = {}


def _legal(langkey):
    if langkey not in _legal_cache:
        _legal_cache[langkey] = json.loads(
            (_ROOT / "locales" / ("legal-%s.json" % langkey)).read_text(encoding="utf-8"))
    return _legal_cache[langkey]


def legal_links_html(loc, home):
    L = _legal(LEGAL_OF[loc])
    items = " &middot; ".join(
        '<a href="%s%s/">%s</a>' % (L["base"], pg["slug"], _esc(pg["h1"]))
        for pg in L["pages"].values()
    )
    return '<a href="%s">farmearaura.com</a> &middot; %s' % (home, items)


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


# Toca una vez por pagina, junto con el <nav> que genera. El hover-only de
# antes nunca andaba en mobile: los navegadores tactiles siguen el link en el
# primer toque (no hay "hover" que revelar), asi que el submenu jamas se veia
# a tiempo. Este script agrega un boton "caret" separado del link, que abre y
# cierra el submenu por tap sin navegar -- el link de al lado sigue navegando
# directo como siempre. El hover de mouse en desktop se maneja aparte en CSS.
NAV_SCRIPT = """<script>(function(){
  function closeAll(except){
    document.querySelectorAll('.nav .item.open').forEach(function(i){
      if (i !== except) { i.classList.remove('open'); i.querySelector('.caret').setAttribute('aria-expanded','false'); }
    });
  }
  document.querySelectorAll('.nav .caret').forEach(function(btn){
    btn.addEventListener('click', function(e){
      e.preventDefault();
      var item = btn.closest('.item');
      var willOpen = !item.classList.contains('open');
      closeAll(null);
      if (willOpen) { item.classList.add('open'); btn.setAttribute('aria-expanded','true'); }
    });
  });
  document.addEventListener('click', function(e){
    if (!e.target.closest('.nav .item')) closeAll(null);
  });
})();</script>"""


def nav_html(loc, current):
    L, U = NAV_LABELS[loc], NAV_URLS[loc]

    def cur(key):
        return ' aria-current="page"' if key == current else ""

    def dropdown(key, ranking_key, label, sub_id, extra_sub=""):
        return (
            '<div class="item">'
            '<a href="%s"%s>%s</a>'
            '<button type="button" class="caret" aria-expanded="false" aria-label="%s">▾</button>'
            '<div class="sub" id="%s">'
            '<a href="%s"%s>%s</a>%s'
            '</div></div>' % (
                U[key], cur(key), _esc(label),
                _esc(label), sub_id,
                U[ranking_key], cur(ranking_key), _esc(L["ranking"]), extra_sub,
            )
        )

    parts = ['<a href="%s"%s>%s</a>' % (U["home"], cur("home"), _esc(L["calculadora"]))]

    historial_link = '<a href="%s"%s>%s</a>' % (
        U["duelos_historial"], cur("duelos_historial"), _esc(L["historial"]))
    parts.append(dropdown("duelos", "duelos_ranking", L["duelos"], "nav-sub-duelos", historial_link))
    parts.append(dropdown("historia", "historia_ranking", L["historia"], "nav-sub-historia"))
    parts.append(NAV_SCRIPT)
    return "".join(parts)
