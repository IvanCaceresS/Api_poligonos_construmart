CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE TABLE IF NOT EXISTS public.poligonos
(
    nombre CITEXT PRIMARY KEY,
    geometria GEOMETRY(MultiPolygon, 4326)
);

ALTER TABLE public.poligonos
    OWNER TO postgres;