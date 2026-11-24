"""Backfill de secciones para vacantes existentes (SPEC 08).

Reutiliza ``job_scraper.utils.sectionizer.split_sections`` para dividir las
descripciones ya almacenadas. Solo toca filas con ``descripcion`` no vacía y
``requirements``/``benefits`` vacíos, por lo que es idempotente.

Uso:
    python backfill_sections.py --dry-run --limit 1   # corrida en seco
    python backfill_sections.py                        # backfill completo
    python backfill_sections.py --id <uuid> --dry-run  # una vacante concreta
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

from job_scraper.utils.sectionizer import split_sections

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
    """Selecciona vacantes con descripción y section arrays vacíos."""
    query = (
        client.table("vacantes")
        .select("id, titulo, empresa, descripcion, requirements, benefits")
        .neq("descripcion", "")
        .eq("requirements", "{}")
        .eq("benefits", "{}")
    )
    if row_id:
        query = query.eq("id", row_id)
    if limit:
        query = query.limit(limit)
    return getattr(query.execute(), "data", None) or []


def split_row(row):
    """Aplica el splitter y devuelve el payload de actualización por ``id``."""
    sections = split_sections(row.get("descripcion") or "")
    return {
        "id": row.get("id"),
        "descripcion": sections["descripcion"],
        "requirements": sections["requirements"],
        "benefits": sections["benefits"],
    }


def has_changes(row, payload):
    """Compara contra la fila original para evitar escrituras innecesarias.

    Una fila que ya tiene secciones se deja intacta: aunque vuelva a aparecer
    en la selección, nunca se deben sobrescribir sus arrays con listas vacías.
    """
    if row.get("requirements") or row.get("benefits"):
        return False
    return (
        (row.get("descripcion") or "") != payload["descripcion"]
        or list(row.get("requirements") or []) != payload["requirements"]
        or list(row.get("benefits") or []) != payload["benefits"]
    )


def _preview(items, max_items=6):
    rendered = [str(item) for item in items]
    if len(rendered) > max_items:
        rendered = rendered[:max_items] + [f"... (+{len(rendered) - max_items})"]
    return rendered


def log_preview(row, payload):
    label = f"{row.get('empresa') or '?'} / {row.get('titulo') or '?'}"
    logger.info("  %s [%s]", label, row.get("id"))
    logger.info("    descripcion: %s", _preview([payload["descripcion"]])[0][:240] or "(vacía)")
    logger.info("    requirements: %s", _preview(payload["requirements"]))
    logger.info("    benefits: %s", _preview(payload["benefits"]))


def run(client, rows, dry_run=False):
    """Procesa las filas y devuelve un dict con los conteos del backfill."""
    counts = {"seleccionadas": len(rows), "actualizadas": 0, "sin_cambios": 0, "errores": 0}
    mode = "SECO" if dry_run else "ESCRITURA"

    for row in rows:
        try:
            payload = split_row(row)
            if not has_changes(row, payload):
                counts["sin_cambios"] += 1
                continue
            if dry_run:
                log_preview(row, payload)
                counts["actualizadas"] += 1
                continue
            client.table("vacantes").update(
                {
                    "descripcion": payload["descripcion"],
                    "requirements": payload["requirements"],
                    "benefits": payload["benefits"],
                }
            ).eq("id", payload["id"]).execute()
            counts["actualizadas"] += 1
        except Exception as exc:  # noqa: BLE001 - una fila no detiene el backfill
            counts["errores"] += 1
            logger.error("Error al procesar %s: %s", row.get("id"), exc)

    logger.info(
        "Backfill (%s): %d seleccionadas, %d actualizadas, %d sin cambios, %d errores.",
        mode,
        counts["seleccionadas"],
        counts["actualizadas"],
        counts["sin_cambios"],
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
