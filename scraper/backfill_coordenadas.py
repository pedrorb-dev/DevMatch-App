"""Backfill de coordenadas para vacantes existentes (SPEC 10).

Geocodifica ``ubicacion_texto`` con Nominatim y reutiliza la caché de ciudades.
Solo toca filas con ``ubicacion_texto`` no vacía y ``lat is null``, por lo que
es idempotente.

Uso:
    python backfill_coordenadas.py --dry-run --limit 1   # corrida en seco
    python backfill_coordenadas.py                        # backfill completo
    python backfill_coordenadas.py --id <uuid> --dry-run  # una vacante concreta
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

from job_scraper.geocode import geocode, load_cache

logger = logging.getLogger(__name__)

_ENV_PATHS = (
    Path(__file__).resolve().parents[1] / ".env",  # raíz del repositorio
    Path(__file__).resolve().parent / ".env",      # scraper/.env
)


def load_environment():
    """Carga las env de la raíz y de scraper/ con el mismo patrón que settings.py."""
    for path in _ENV_PATHS:
        load_dotenv(path)


def build_client(url, key):
    if not url or not key:
        return None
    return create_client(url, key)


def fetch_candidates(client, limit=None, row_id=None):
    """Selecciona vacantes con ubicación y sin coordenadas."""
    query = (
        client.table("vacantes")
        .select("id, titulo, empresa, ubicacion_texto, lat, lng")
        .neq("ubicacion_texto", "")
        .is_("lat", "null")
    )
    if row_id:
        query = query.eq("id", row_id)
    if limit:
        query = query.limit(limit)
    return getattr(query.execute(), "data", None) or []


def run(client, rows, dry_run=False):
    """Geocodifica las filas y devuelve un dict con los conteos del backfill."""
    counts = {"seleccionadas": len(rows), "actualizadas": 0, "sin_coordenadas": 0, "errores": 0}
    mode = "SECO" if dry_run else "ESCRITURA"
    cache = load_cache()

    for row in rows:
        try:
            coords = geocode(row.get("ubicacion_texto") or "", cache)
            if not coords:
                counts["sin_coordenadas"] += 1
                continue
            payload = {"lat": coords[0], "lng": coords[1]}
            if dry_run:
                label = f"{row.get('empresa') or '?'} / {row.get('titulo') or '?'}"
                logger.info("  %s -> %s", label, payload)
                counts["actualizadas"] += 1
                continue
            client.table("vacantes").update(payload).eq("id", row.get("id")).execute()
            counts["actualizadas"] += 1
        except Exception as exc:  # noqa: BLE001 - una fila no detiene el backfill
            counts["errores"] += 1
            logger.error("Error al procesar %s: %s", row.get("id"), exc)

    logger.info(
        "Backfill (%s): %d seleccionadas, %d actualizadas, %d sin coordenadas, %d errores.",
        mode,
        counts["seleccionadas"],
        counts["actualizadas"],
        counts["sin_coordenadas"],
        counts["errores"],
    )
    return counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="no escribe en Supabase")
    parser.add_argument("--limit", type=int, help="máximo de vacantes a procesar")
    parser.add_argument("--id", help="procesar solo una vacante por su id")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_environment()

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        logger.warning("Backfill desactivado: faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY.")
        return 2

    client = build_client(url, key)
    try:
        rows = fetch_candidates(client, limit=args.limit, row_id=args.id)
    except Exception as exc:  # noqa: BLE001 - fallo de red/consulta
        logger.error("No se pudieron leer las vacantes: %s", exc)
        return 1

    counts = run(client, rows, dry_run=args.dry_run)
    return 1 if counts["errores"] else 0


if __name__ == "__main__":
    sys.exit(main())
