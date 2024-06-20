CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE IF NOT EXISTS public.poligonos
(
    codigo_postal CITEXT PRIMARY KEY,
    glosa CITEXT NOT NULL,
    geometria GEOMETRY(MultiPolygon, 4326)
);

ALTER TABLE public.poligonos
    OWNER TO postgres;
