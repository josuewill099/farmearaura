-- Esquema de la base de duelos (Cloudflare D1)
-- PK compuesta (loc, id), igual que h_candidatos: varios locales reusan el
-- mismo id para el mismo concepto ("tarde", "gol", "foto"...), asi que un id
-- global habria chocado apenas se sumo el segundo pais.
CREATE TABLE IF NOT EXISTS candidatos (
  loc       TEXT NOT NULL DEFAULT 'ar',
  id        TEXT NOT NULL,
  aura      INTEGER NOT NULL DEFAULT 1000,
  ganados   INTEGER NOT NULL DEFAULT 0,
  perdidos  INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (loc, id)
);

CREATE TABLE IF NOT EXISTS duelos (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  loc       TEXT NOT NULL DEFAULT 'ar',
  ganador   TEXT NOT NULL,
  perdedor  TEXT NOT NULL,
  puntos    INTEGER NOT NULL,
  ts        INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_duelos_loc_ts ON duelos (loc, ts DESC);

CREATE TABLE IF NOT EXISTS votantes (
  ip      TEXT PRIMARY KEY,
  ultimo  INTEGER NOT NULL,
  hora    INTEGER NOT NULL,
  cuenta  INTEGER NOT NULL DEFAULT 0
);
