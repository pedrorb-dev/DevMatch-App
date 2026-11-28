"""Reglas de match para las notificaciones push de vacantes nuevas.

La cobertura de stack, la experiencia y el inglés se evalúan con el mismo
vocabulario canónico que usa el pipeline de enriquecimiento, de modo que un
alias como ``springboot`` cuente como ``Spring Boot``.
"""

import re
import unicodedata

from job_scraper import stack_catalog


ENGLISH_RANK = {"No especificado": 0, "B1": 1, "B2": 2, "C1": 3}

# El perfil de la app permite A1/A2/C2 aunque el scraper solo detecte los
# niveles de ENGLISH_RANK; se ordenan para no descartar perfiles C2.
_EXTRA_ENGLISH_RANK = {"A1": 0, "A2": 0, "C2": 4}

def _normalize_key(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if unicodedata.combining(char) == 0)
    return re.sub(r"\s+", " ", text).lower().strip()


_NORMALIZED_RANKS = {
    _normalize_key(level): rank
    for level, rank in {
        **ENGLISH_RANK,
        **_EXTRA_ENGLISH_RANK,
    }.items()
}


def canonical_tech(token):
    """Devuelve el nombre canónico de una tecnología, resolviendo alias."""
    return stack_catalog.canonical_tech(token)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def stack_match_percent(user_stack, job_stack):
    """Porcentaje de tecnologías del usuario cubiertas por la vacante."""
    user_techs = {canonical_tech(tech) for tech in _as_list(user_stack)}
    user_techs.discard("")
    if not user_techs:
        return 0

    job_techs = {canonical_tech(tech) for tech in _as_list(job_stack)}
    return 100 * len(user_techs & job_techs) / len(user_techs)


def english_rank(level):
    """Rango ordinal de un nivel de inglés; niveles desconocidos valen 0."""
    return _NORMALIZED_RANKS.get(_normalize_key(level), 0)


def _as_int(value):
    try:
        return max(int(value or 0), 0)
    except (TypeError, ValueError):
        return 0


def is_full_match(user, job):
    """True solo si la vacante cubre stack, experiencia e inglés del perfil."""
    if stack_match_percent(user.get("stack"), job.get("stack_detectado")) != 100:
        return False

    user_experience = _as_int(user.get("experiencia_anos"))
    job_experience = _as_int(job.get("experiencia_minima"))
    if user_experience == 0:
        if job_experience != 0:
            return False
    elif job_experience > user_experience:
        return False

    return english_rank(job.get("nivel_ingles")) <= english_rank(user.get("nivel_ingles"))
