/**
 * API de duelos, portada de functions/api/[[ruta]].js (convencion de Cloudflare
 * Pages Functions) a un Worker normal, porque este proyecto se despliega con
 * `wrangler deploy` (Workers + static assets), no con `wrangler pages deploy`.
 * Bajo ese modelo las peticiones que no matchean un archivo en dist/ caen aca.
 *
 *   GET  /api/aura/estado
 *   POST /api/aura/voto
 *   GET  /api/aura/duelos
 *   GET  /api/historia/estado?loc=ar|mx|es|br
 *   POST /api/historia/voto
 *   GET  /api/historia/duelos?loc=ar|mx|es|br
 */

const MODULOS = {
  aura: {
    candidatos: "candidatos",
    duelos: "duelos",
    votantes: "votantes",
    locales: ["ar", "mx", "es", "br", "cl", "pe", "co", "us"],
    limite: 60,
    poda: 5000
  },
  historia: {
    candidatos: "h_candidatos",
    duelos: "h_duelos",
    votantes: "h_votantes",
    locales: ["ar", "mx", "es", "br", "cl", "pe", "co", "us"],
    limite: 40,
    poda: 8000
  }
};

const K = 32;
const MIN_MS = 400;
const MAX_POR_HORA = 400;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith("/api/")) {
      return new Response("Not Found", { status: 404 });
    }

    const ruta = url.pathname.slice("/api/".length).split("/").filter(Boolean);
    const modulo = MODULOS[ruta[0]];
    const accion = ruta[1];

    if (!modulo || !accion) return json({ error: "ruta_desconocida" }, 404);
    if (!env.AURA_DB) return json({ error: "sin_base" }, 503);

    try {
      if (accion === "estado" && request.method === "GET") {
        return await estado(request, env, modulo);
      }
      if (accion === "duelos" && request.method === "GET") {
        return await ultimos(request, env, modulo);
      }
      if (accion === "voto" && request.method === "POST") {
        return await voto(request, env, modulo);
      }
    } catch {
      return json({ error: "fallo" }, 500);
    }
    return json({ error: "metodo_no_permitido" }, 405);
  }
};

/* ------------------------------------------------------------------ */

function locDe(request, modulo, cuerpo) {
  if (!modulo.locales) return { ok: true, loc: null };
  const loc = cuerpo
    ? String(cuerpo.loc || "")
    : new URL(request.url).searchParams.get("loc") || "ar";
  return modulo.locales.includes(loc) ? { ok: true, loc } : { ok: false };
}

async function estado(request, env, modulo) {
  const l = locDe(request, modulo, null);
  if (!l.ok) return json({ error: "loc_invalida" }, 400);

  const sql =
    "SELECT id, aura, ganados, perdidos FROM " + modulo.candidatos +
    (l.loc ? " WHERE loc = ?" : "") + " ORDER BY aura DESC";
  const q = env.AURA_DB.prepare(sql);
  const { results } = await (l.loc ? q.bind(l.loc) : q).all();
  const filas = results || [];

  // las dos claves apuntan al mismo array: duelos.js lee "candidatos",
  // historia.js lee "figuras"
  return json({ loc: l.loc, candidatos: filas, figuras: filas }, 200, "public, max-age=10");
}

async function ultimos(request, env, modulo) {
  const l = locDe(request, modulo, null);
  if (!l.ok) return json({ error: "loc_invalida" }, 400);

  const sql =
    "SELECT ganador, perdedor, puntos, ts FROM " + modulo.duelos +
    (l.loc ? " WHERE loc = ?" : "") + " ORDER BY id DESC LIMIT " + modulo.limite;
  const q = env.AURA_DB.prepare(sql);
  const { results } = await (l.loc ? q.bind(l.loc) : q).all();
  return json({ loc: l.loc, duelos: results || [] }, 200, "public, max-age=10");
}

async function voto(request, env, modulo) {
  let cuerpo;
  try {
    cuerpo = await request.json();
  } catch {
    return json({ error: "json_invalido" }, 400);
  }

  const l = locDe(request, modulo, cuerpo);
  if (!l.ok) return json({ error: "loc_invalida" }, 400);

  const ganador = String(cuerpo.ganador || "").slice(0, 40);
  const perdedor = String(cuerpo.perdedor || "").slice(0, 40);
  if (!ganador || !perdedor || ganador === perdedor) {
    return json({ error: "par_invalido" }, 400);
  }

  const ahora = Date.now();
  const horaActual = Math.floor(ahora / 3600000);
  const ip = await hash(
    (request.headers.get("cf-connecting-ip") || "0.0.0.0") +
      (request.headers.get("user-agent") || "")
  );

  const v = await env.AURA_DB
    .prepare("SELECT ultimo, hora, cuenta FROM " + modulo.votantes + " WHERE ip = ?")
    .bind(ip)
    .first();

  if (v) {
    if (ahora - v.ultimo < MIN_MS) return json({ error: "muy_rapido" }, 429);
    if (v.hora === horaActual && v.cuenta >= MAX_POR_HORA) {
      return json({ error: "limite" }, 429);
    }
  }

  const sel =
    "SELECT id, aura FROM " + modulo.candidatos +
    " WHERE " + (l.loc ? "loc = ? AND " : "") + "id IN (?, ?)";
  const args = l.loc ? [l.loc, ganador, perdedor] : [ganador, perdedor];
  const { results } = await env.AURA_DB.prepare(sel).bind(...args).all();
  if (!results || results.length !== 2) return json({ error: "no_existe" }, 404);

  const auraG = results.find((r) => r.id === ganador).aura;
  const auraP = results.find((r) => r.id === perdedor).aura;
  const esperado = 1 / (1 + Math.pow(10, (auraP - auraG) / 400));
  const puntos = Math.max(1, Math.round(K * (1 - esperado)));
  const ts = Math.floor(ahora / 1000);
  const cuenta = v && v.hora === horaActual ? v.cuenta + 1 : 1;

  const cond = l.loc ? " WHERE loc = ? AND id = ?" : " WHERE id = ?";
  const arg = (id) => (l.loc ? [l.loc, id] : [id]);

  const sentencias = [
    env.AURA_DB
      .prepare("UPDATE " + modulo.candidatos +
               " SET aura = aura + ?, ganados = ganados + 1" + cond)
      .bind(puntos, ...arg(ganador)),
    env.AURA_DB
      .prepare("UPDATE " + modulo.candidatos +
               " SET aura = aura - ?, perdidos = perdidos + 1" + cond)
      .bind(puntos, ...arg(perdedor)),
    l.loc
      ? env.AURA_DB
          .prepare("INSERT INTO " + modulo.duelos +
                   " (loc, ganador, perdedor, puntos, ts) VALUES (?, ?, ?, ?, ?)")
          .bind(l.loc, ganador, perdedor, puntos, ts)
      : env.AURA_DB
          .prepare("INSERT INTO " + modulo.duelos +
                   " (ganador, perdedor, puntos, ts) VALUES (?, ?, ?, ?)")
          .bind(ganador, perdedor, puntos, ts),
    env.AURA_DB
      .prepare("INSERT INTO " + modulo.votantes +
               " (ip, ultimo, hora, cuenta) VALUES (?, ?, ?, ?) " +
               "ON CONFLICT(ip) DO UPDATE SET ultimo = excluded.ultimo, " +
               "hora = excluded.hora, cuenta = excluded.cuenta")
      .bind(ip, ahora, horaActual, cuenta)
  ];

  if (Math.random() < 0.01) {
    sentencias.push(
      env.AURA_DB.prepare(
        "DELETE FROM " + modulo.duelos +
        " WHERE id < (SELECT MAX(id) - " + modulo.poda + " FROM " + modulo.duelos + ")"
      )
    );
  }

  await env.AURA_DB.batch(sentencias);

  return json({
    ok: true,
    puntos,
    ganador: { id: ganador, aura: auraG + puntos },
    perdedor: { id: perdedor, aura: auraP - puntos }
  });
}

/* ------------------------------------------------------------------ */

async function hash(texto) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(texto));
  return [...new Uint8Array(buf)]
    .slice(0, 12)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function json(data, status = 200, cache = "no-store") {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": cache
    }
  });
}
