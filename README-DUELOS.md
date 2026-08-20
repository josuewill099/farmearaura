# Módulo de duelos — farmearaura.com (solo AR)

Tres páginas nuevas, agregadas sin tocar `build.py`:

| URL | Qué es |
|---|---|
| `/duelos/` | votar: dos personajes, elegís uno, el ganador le roba aura |
| `/duelos/ranking/` | tabla en vivo, ordenada por aura |
| `/duelos/historial/` | los últimos 60 votos, uno por uno |

Los votos son **globales**: todos los que entran ven los mismos números. Eso
necesita una base, y en Cloudflare Pages eso es D1 (gratis hasta 100.000
escrituras por día, que es mucho más de lo que KV te da).

---

## Archivos

```
build_duelos.py            # corre DESPUÉS de build.py
locales/duelos-ar.json     # toda la copia y los 24 personajes
src/duelos.tpl.html
src/duelos.css
src/duelos.js
functions/api/aura/estado.js   # GET  candidatos + aura
functions/api/aura/voto.js     # POST un voto
functions/api/aura/duelos.js   # GET  últimos duelos
schema.sql                 # tablas
seed.sql                   # lo genera build_duelos.py desde el JSON
```

`functions/` va en la **raíz del repo**, al lado de `build.py`, no adentro de `dist/`.

---

## 1. Crear la base (una sola vez)

En la terminal, con wrangler:

```bash
npx wrangler d1 create aura
npx wrangler d1 execute aura --remote --file=./schema.sql
python3 build_duelos.py                 # genera seed.sql
npx wrangler d1 execute aura --remote --file=./seed.sql
```

Si preferís no usar terminal: **Cloudflare Dashboard → Storage & Databases → D1
→ Create database** (nombre `aura`), abrí la consola de la base y pegá primero
el contenido de `schema.sql` y después el de `seed.sql`.

## 2. Conectarla al sitio

Dashboard → tu proyecto de Pages → **Settings → Bindings → Add → D1 database**

- Variable name: `AURA_DB`  ← tiene que ser exactamente así
- D1 database: `aura`

Agregala en **Production** y también en **Preview**. Redeploy después de guardar.

## 3. Build command

Cambiá el build command del proyecto a:

```
python3 build.py && python3 build_duelos.py
```

Si estás commiteando `dist/` a mano, corré los dos comandos local antes de pushear.

---

## Cómo funciona la aura

Cada uno arranca en 1.000. En cada duelo el ganador le roba puntos al perdedor:

```
esperado = 1 / (1 + 10^((auraPerdedor − auraGanador) / 400))
puntos   = round(32 × (1 − esperado))      // mínimo 1
```

Ganarle a uno que está arriba roba mucho; ganarle a uno hundido roba casi nada.
Es Elo, con la resta al perdedor. **Puede quedar en negativo** y está bien: aura
negativa es parte del chiste.

El cálculo está en el servidor (`voto.js`). El cliente lo replica solo para que
el número se mueva al instante; cuando vuelve la respuesta se corrige con el
valor real. Nadie puede inventar puntos desde la consola.

## Si la base todavía no está

Las páginas **no se rompen**: caen a modo local con los valores del JSON, muestran
el cartel amarillo "Modo local: los votos no se guardan todavía" y el duelo se
puede jugar igual. Sirve para previsualizar antes de crear la D1.

## Anti-abuso

Por IP (hasheada con el user-agent, no se guarda la IP en claro): mínimo 400 ms
entre votos y tope de 400 votos por hora. La tabla `duelos` se poda sola a las
5.000 filas más recientes.

---

## Cambiar los personajes

Editá `locales/duelos-ar.json` → `candidatos`, corré `build_duelos.py`, y pasá
el `seed.sql` nuevo por D1 (`INSERT OR IGNORE`, así que no pisa lo que ya está).
Para sacar a alguien, borralo del JSON: el front filtra por lo que hay en el
JSON, así que desaparece de las tres páginas sin tocar la base.

**El roster es fijo a propósito.** No hay campo para que nadie cargue nombres.
Con público de 11 a 17 años, un "quién tiene más aura" con nombres libres se
convierte en una máquina de bardear compañeros en una tarde, y encima te obliga
a moderar. Personajes tipo "el que corta el mate y no avisa" se comparten igual
y no le pegan a nadie.

## Pendiente que ya venías arrastrando

Estas tres páginas cargan GA4 igual que el resto del sitio (constante `GA4_ID`
arriba de `build_duelos.py`). Si terminás resolviendo lo del banner de consentimiento
o el cambio a Cloudflare Web Analytics, acordate de que acá también hay que tocarlo:
dejá `GA4_ID = ""` y listo.

## Para las otras locales

Cuando quieras MX / ES / BR: copiá `locales/duelos-ar.json`, traducí copia y
personajes, y en `build_duelos.py` pasá el prefijo de carpeta. La base puede ser
la misma con una columna `locale` en `candidatos`, o una tabla por mercado.
Brasil probablemente merezca su propio roster, no una traducción.
