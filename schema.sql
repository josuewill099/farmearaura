-- Esquema de la base de duelos (Cloudflare D1)
CREATE TABLE IF NOT EXISTS candidatos (
  id        TEXT PRIMARY KEY,
  aura      INTEGER NOT NULL DEFAULT 1000,
  ganados   INTEGER NOT NULL DEFAULT 0,
  perdidos  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS duelos (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  ganador   TEXT NOT NULL,
  perdedor  TEXT NOT NULL,
  puntos    INTEGER NOT NULL,
  ts        INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_duelos_ts ON duelos (ts DESC);

CREATE TABLE IF NOT EXISTS votantes (
  ip      TEXT PRIMARY KEY,
  ultimo  INTEGER NOT NULL,
  hora    INTEGER NOT NULL,
  cuenta  INTEGER NOT NULL DEFAULT 0
);
