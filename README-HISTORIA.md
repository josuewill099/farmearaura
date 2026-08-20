# Duelos históricos — las cuatro locales

Ocho páginas nuevas: votar + ranking por cada mercado.

| Locale | Votar | Ranking |
|---|---|---|
| AR | `/duelos/historia/` | `/duelos/historia/ranking/` |
| MX | `/mx/duelos/historia/` | `/mx/duelos/historia/ranking/` |
| ES | `/es/duelos-de-aura/` | `/es/duelos-de-aura/ranking/` |
| BR | `/br/batalha-de-aura/` | `/br/batalha-de-aura/ranking/` |

Las cuatro se declaran entre sí con hreflang (`es-AR` + `es` + `x-default` en AR,
`es-MX`, `es-ES`, `pt-BR`). ES y BR usan slug propio: en España "duelo de aura"
suena antes que "duelos", y en Brasil "batalha" es la palabra que se usa.

**Cada mercado tiene su propio ranking.** Los 20 nombres globales son los mismos
en todos lados, pero los 8 locales cambian, así que un ranking compartido no
tendría sentido. La tabla lleva columna `loc`.

---

## Archivos

```
build_historia.py               # corre al final
locales/historia-ar.json        # copia + 28 figuras
locales/historia-mx.json
locales/historia-es.json
locales/historia-br.json
src/historia.tpl.html
src/historia.css                # se concatena DESPUES de duelos.css
src/historia.js
functions/api/historia/estado.js
functions/api/historia/voto.js
functions/api/historia/duelos.js
schema-historia.sql
seed-historia.sql               # lo genera build_historia.py
```

`historia.css` **no reemplaza** a `duelos.css`: el builder lee los dos y los pega,
así que el módulo de arquetipos y este comparten layout y solo cambia la paleta
(oro en vez de magenta). Si tocás `duelos.css`, cambian los dos.

## Puesta en marcha

Misma base D1, mismo binding `AURA_DB`, tablas nuevas (`h_candidatos`, `h_duelos`,
`h_votantes`). No toca nada del módulo de arquetipos.

```bash
npx wrangler d1 execute aura --remote --file=./schema-historia.sql
python3 build_historia.py
npx wrangler d1 execute aura --remote --file=./seed-historia.sql
```

Build command final del proyecto:

```
python3 build.py && python3 build_duelos.py && python3 build_historia.py
```

Sin base, las ocho páginas caen a modo local con el cartel amarillo y el duelo
se juega igual. Sirve para previsualizar.

---

## El roster: 20 globales + 8 locales

Globales (iguales en las cuatro, traducidos): Cleopatra, Da Vinci, Einstein,
Tesla, Marie Curie, Frida Kahlo, Ada Lovelace, Juana de Arco, Napoleón, Alejandro
Magno, Beethoven, Mozart, Shakespeare, Amelia Earhart, Sócrates, Galileo, Van
Gogh, Bruce Lee, Tutankamón, Hipatia.

Locales: San Martín, Belgrano, Juana Azurduy, Borges, Gardel, Piazzolla,
Favaloro y Maradona en AR · Sor Juana, Juárez, Zapata, Villa, Nezahualcóyotl,
Rivera, Pedro Infante y Octavio Paz en MX · Cervantes, Goya, Velázquez, Lorca,
Ramón y Cajal, Dalí, Picasso y Camarón en ES · Machado de Assis, Santos Dumont,
Tarsila do Amaral, Carmen Miranda, Zumbi dos Palmares, Pelé, Senna y Clarice
Lispector en BR.

### Lo que dejé afuera a propósito

- **Vivos.** Todos están muertos. Poner a alguien vivo en una tabla pública
  ordenada de mejor a peor es otra cosa, con otro riesgo legal.
- **Dictadores y genocidas.** Nada de Hitler, Videla, Franco, Pinochet, Stalin.
  Un juego de "quién tiene más aura" convierte cualquier nombre que toca en un
  chiste compartible, y esos no.
- **Figuras religiosas.** Ni Jesús, ni Mahoma, ni santos. En un ranking con
  ganadores y perdedores no hay forma de que no ofenda a alguien.
- **Íconos de lucha civil y víctimas.** Mandela, Gandhi, Rosa Parks, Ana Frank.
  Se los recuerda por lo que sufrieron o pelearon, y el registro del juego no da.
- **Políticos que todavía dividen elecciones.** Por eso no está Evita, aunque en
  términos de aura sería top 3 en Argentina. Si el sitio se lee como que toma
  partido, perdés la mitad del público de un lado o del otro.

El criterio, si querés agregar gente: sirve alguien a quien se lo recuerda por
algo que hizo, y sobre quien un adolescente puede opinar sin que nadie se ofenda
de verdad. Científicos, artistas, exploradores, deportistas, escritores.

## Cambiar el roster

Editá `figuras` en el `locales/historia-<loc>.json` que corresponda, corré
`build_historia.py` y pasá el `seed-historia.sql` nuevo (es `INSERT OR IGNORE`,
no pisa lo que ya está acumulado). Para sacar a alguien alcanza con borrarlo del
JSON: el front filtra por lo que hay ahí y desaparece de las dos páginas sin
tocar la base.

Cada figura son cinco campos: `id`, `emoji`, `nombre`, `anios`, `oficio`. El
`oficio` es la línea chica bajo el nombre y es la que hace votable el duelo —
"Inventó el bypass" da más para decidir que "Médico".

## SEO

Cada página de votar lleva JSON-LD con `ItemList` de 28 `Person`, más `WebPage`
y `BreadcrumbList`. El texto de abajo explica la mecánica en prosa, así que la
página no es solo dos botones para el crawler. Las ocho se suman solas a
`dist/sitemap.xml` si el archivo existe cuando corre el build.

Nota: BR es tu mercado grande (44k/mes contra 1,7k de los tres en español), así
que si vas a empujar una, empujá `/br/batalha-de-aura/`.

## Analytics

Igual que el resto: constante `GA4_ID` arriba de `build_historia.py`. Cuando
resuelvas el banner de consentimiento hay que tocarlo acá también, o dejarlo en
`""`.
