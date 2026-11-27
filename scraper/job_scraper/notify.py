"""Envío de notificaciones push para vacantes nuevas con match completo."""

import logging

import requests
from supabase import create_client

from job_scraper.matching import is_full_match


logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
BATCH_SIZE = 100

JOB_COLUMNS = "id,titulo,empresa,stack_detectado,experiencia_minima,nivel_ingles"
PROFILE_COLUMNS = "id,stack,experiencia_anos,nivel_ingles,expo_push_token"


def _send_batch(messages):
    """Envía hasta 100 mensajes a Expo Push API y loguea los tickets."""
    response = requests.post(
        EXPO_PUSH_URL,
        json=messages,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json() or {}
    tickets = payload.get("data") or []

    for message, ticket in zip(messages, tickets):
        logger.info(
            "Push ticket para %s: %s",
            message["to"],
            ticket,
        )

    for error in payload.get("errors") or []:
        logger.error("Error de Expo Push API: %s", error)


def notify_full_matches(supabase_url, supabase_key, run_started_at):
    """Notifica las vacantes creadas desde ``run_started_at`` que encajan al 100 %.

    Devuelve el número de mensajes enviados. No hace nada si faltan credenciales
    o si ningún perfil tiene token push.
    """
    supabase_url = (supabase_url or "").strip()
    supabase_key = (supabase_key or "").strip()
    if not supabase_url or not supabase_key:
        logger.warning("Push notifications disabled: missing Supabase credentials.")
        return 0

    started_at = (
        run_started_at.isoformat()
        if hasattr(run_started_at, "isoformat")
        else str(run_started_at)
    )

    client = create_client(supabase_url, supabase_key)
    jobs_response = (
        client.table("vacantes")
        .select(JOB_COLUMNS)
        .gte("created_at", started_at)
        .execute()
    )
    profiles_response = (
        client.table("user_profiles")
        .select(PROFILE_COLUMNS)
        .not_.is_("expo_push_token", "null")
        .execute()
    )

    jobs = getattr(jobs_response, "data", None) or []
    profiles = getattr(profiles_response, "data", None) or []
    tokens = [
        profile.get("expo_push_token")
        for profile in profiles
        if isinstance(profile, dict) and profile.get("expo_push_token")
    ]
    if not jobs or not tokens:
        logger.info("No hay vacantes nuevas o perfiles con token para notificar.")
        return 0

    messages = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        for profile in profiles:
            if not isinstance(profile, dict) or not profile.get("expo_push_token"):
                continue
            if not is_full_match(profile, job):
                continue
            messages.append(
                {
                    "to": profile["expo_push_token"],
                    "title": "100% match con tu stack",
                    "body": f"{job.get('empresa') or ''} · {job.get('titulo') or ''}",
                    "data": {"url": f"/work/{job.get('id')}"},
                    "sound": "default",
                    "priority": "high",
                }
            )

    if not messages:
        logger.info("Ninguna vacante nueva hace match completo.")
        return 0

    for offset in range(0, len(messages), BATCH_SIZE):
        batch = messages[offset : offset + BATCH_SIZE]
        try:
            _send_batch(batch)
        except Exception as exc:
            logger.error("No se pudo enviar el lote de push notifications: %s", exc)

    logger.info("Push notifications enviadas: %d", len(messages))
    return len(messages)
