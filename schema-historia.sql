-- Duelos historicos (Cloudflare D1). Independiente del modulo de arquetipos.
CREATE TABLE IF NOT EXISTS h_candidatos (
  loc       TEXT NOT NULL,
  id        TEXT NOT NULL,
  aura      INTEGER NOT NULL DEFAULT 1000,
  ganados   INTEGER NOT NULL DEFAULT 0,
  perdidos  INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (loc, id)
);
CREATE INDEX IF NOT EXISTS idx_h_candidatos_loc_aura ON h_candidatos (loc, aura DESC);

CREATE TABLE IF NOT EXISTS h_duelos (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  loc       TEXT NOT NULL,
  ganador   TEXT NOT NULL,
  perdedor  TEXT NOT NULL,
  puntos    INTEGER NOT NULL,
  ts        INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_h_duelos ON h_duelos (loc, id DESC);

CREATE TABLE IF NOT EXISTS h_votantes (
  ip      TEXT PRIMARY KEY,
  ultimo  INTEGER NOT NULL,
  hora    INTEGER NOT NULL,
  cuenta  INTEGER NOT NULL DEFAULT 0
);
