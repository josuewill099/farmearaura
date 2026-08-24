-- Duelos entre famosos (Cloudflare D1). Independiente de los modulos de arquetipos e historia.
CREATE TABLE IF NOT EXISTS f_candidatos (
  loc       TEXT NOT NULL,
  id        TEXT NOT NULL,
  aura      INTEGER NOT NULL DEFAULT 1000,
  ganados   INTEGER NOT NULL DEFAULT 0,
  perdidos  INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (loc, id)
);

CREATE TABLE IF NOT EXISTS f_duelos (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  loc       TEXT NOT NULL,
  ganador   TEXT NOT NULL,
  perdedor  TEXT NOT NULL,
  puntos    INTEGER NOT NULL,
  ts        INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_f_duelos ON f_duelos (loc, id DESC);

CREATE TABLE IF NOT EXISTS f_votantes (
  ip      TEXT PRIMARY KEY,
  ultimo  INTEGER NOT NULL,
  hora    INTEGER NOT NULL,
  cuenta  INTEGER NOT NULL DEFAULT 0
);
