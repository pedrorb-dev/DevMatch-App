"""Backfill de stacks para vacantes existentes (SPEC 12).

Recalcula ``stack_detectado`` con la misma detección del pipeline de
enriquecimiento. Las vacantes guardan texto y secciones, pero no los tags de
scraping, así que la detección se hace con los campos persistidos (título y
descripción). Solo escribe cuando el resultado cambia y no toca ningún otro
campo: es idempotente, manual y revisible con ``--dry-run``.

Uso:
    python backfill_stacks.py --dry-run --limit 1   # corrida en seco
    python backfill_stacks.py                        # backfill completo
    python backfill_stacks.py --id <uuid> --dry-run  # una vacante concreta
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

from job_scraper.pipelines import JobEnrichmentPipeline

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
    """Selecciona las vacantes existentes, con o sin stack detectado."""
    query = client.table("vacantes").select(
        "id, titulo, empresa, descripcion, stack_detectado"
    )
    if row_id:
        query = query.eq("id", row_id)
    if limit:
        query = query.limit(limit)
    return getattr(query.execute(), "data", None) or []


def compute_stack(row, pipeline):
    """Aplica la detección del pipeline a los campos persistidos de la vacante."""
    # Deliberadamente sin tags: ``vacantes`` no guarda ``tags_tecnologias``.
    # Usar el pipeline evita duplicar aquí patrones ni reglas de shadowing.
    return pipeline._detect_stack(
        {
            "titulo": row.get("titulo") or "",
            "descripcion": row.get("descripcion") or "",
            "tags_tecnologias": [],
        }
    )


def has_changes(row, detected):
    """Compara con el valor guardado para no reescribir filas ya actualizadas."""
    return sorted(row.get("stack_detectado") or []) != sorted(detected)


def log_preview(row, detected):
    label = f"{row.get('empresa') or '?'} / {row.get('titulo') or '?'}"
    logger.info(
        "  %s [%s]: %s -> %s",
        label,
        row.get("id"),
        row.get("stack_detectado") or [],
        detected,
    )


def run(client, rows, dry_run=False, pipeline=None):
    """Recalcula el stack de las filas y devuelve los conteos del backfill."""
    counts = {"seleccionadas": len(rows), "actualizadas": 0, "sin_cambios": 0, "errores": 0}
    mode = "SECO" if dry_run else "ESCRITURA"
    pipeline = pipeline or JobEnrichmentPipeline()

    for row in rows:
        try:
            detected = compute_stack(row, pipeline)
            if not has_changes(row, detected):
                counts["sin_cambios"] += 1
                continue
            if dry_run:
                log_preview(row, detected)
                counts["actualizadas"] += 1
                continue
            client.table("vacantes").update({"stack_detectado": detected}).eq(
                "id", row.get("id")
            ).execute()
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
