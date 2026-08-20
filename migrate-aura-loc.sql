-- Migracion unica: el modulo de arquetipos (candidatos/duelos) nacio
-- exclusivo de Argentina, sin columna "loc". Al sumar mas paises varios
-- ids se repiten para el mismo concepto ("tarde", "gol", "foto"...), asi
-- que "candidatos" necesita PK compuesta (loc, id) -- no alcanza con
-- agregar la columna, en SQLite hay que reconstruir la tabla. "duelos" si
-- alcanza con agregar la columna, porque su PK es un id autoincremental
-- sin relacion con los ids de los candidatos. "votantes" no se toca: el
-- rate-limit es por IP nada mas, sin distincion de locale, igual que en
-- el modulo de historia.
--
--   npx wrangler d1 execute aura --remote --file=./migrate-aura-loc.sql
--
-- Correr una sola vez, antes del proximo seed.sql. Los datos existentes
-- (todos de Argentina hasta ahora) quedan intactos con loc='ar'.

CREATE TABLE candidatos_nuevo (
  loc       TEXT NOT NULL DEFAULT 'ar',
  id        TEXT NOT NULL,
  aura      INTEGER NOT NULL DEFAULT 1000,
  ganados   INTEGER NOT NULL DEFAULT 0,
  perdidos  INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (loc, id)
);

INSERT INTO candidatos_nuevo (loc, id, aura, ganados, perdidos)
SELECT 'ar', id, aura, ganados, perdidos FROM candidatos;

DROP TABLE candidatos;
ALTER TABLE candidatos_nuevo RENAME TO candidatos;

ALTER TABLE duelos ADD COLUMN loc TEXT NOT NULL DEFAULT 'ar';
CREATE INDEX IF NOT EXISTS idx_duelos_loc_ts ON duelos (loc, ts DESC);
