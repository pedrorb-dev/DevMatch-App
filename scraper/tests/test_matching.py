import pytest

from job_scraper import matching
from job_scraper.matching import (
    canonical_tech,
    english_rank,
    is_full_match,
    stack_match_percent,
)


def test_stack_match_percent_cobertura_total_parcial_y_nula():
    assert stack_match_percent(["Python", "SQL"], ["Python", "SQL"]) == 100
    assert stack_match_percent(["Python", "SQL"], ["Python", "Docker"]) == 50
    assert stack_match_percent(["Python", "SQL"], ["Docker"]) == 0


def test_stack_match_percent_stack_vacio_es_cero():
    assert stack_match_percent([], ["Python"]) == 0
    assert stack_match_percent(None, ["Python"]) == 0


def test_stack_match_percent_ignora_tecnologias_extra_de_la_vacante():
    assert stack_match_percent(["Python"], ["Python", "Kubernetes", "AWS"]) == 100


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("AngularJS", "Angular"),
        ("angular", "Angular"),
        ("springboot", "Spring Boot"),
        ("Spring Boot", "Spring Boot"),
        ("spring", "Spring Boot"),
        ("nodejs", "Node.js"),
        ("TypeScript", "TypeScript"),
    ],
)
def test_canonical_tech_resuelve_alias(token, expected):
    assert canonical_tech(token) == expected


@pytest.mark.parametrize(
    ("level", "expected"),
    [("No especificado", 0), ("B1", 1), ("B2", 2), ("C1", 3)],
)
def test_english_rank(level, expected):
    assert english_rank(level) == expected


def make_user(stack=None, experiencia_anos=2, nivel_ingles="B2"):
    return {
        "stack": ["Python", "SQL"] if stack is None else stack,
        "experiencia_anos": experiencia_anos,
        "nivel_ingles": nivel_ingles,
    }


def make_job(stack=None, experiencia_minima=1, nivel_ingles="B1"):
    return {
        "stack_detectado": ["Python", "SQL"] if stack is None else stack,
        "experiencia_minima": experiencia_minima,
        "nivel_ingles": nivel_ingles,
    }


def test_is_full_match_exige_stack_experiencia_e_ingles():
    assert is_full_match(make_user(), make_job()) is True


def test_is_full_match_rechaza_stack_parcial_pero_acepta_extras():
    assert is_full_match(make_user(), make_job(stack=["Python", "Docker"])) is False
    assert (
        is_full_match(
            make_user(), make_job(stack=["Python", "SQL", "Docker", "AWS"])
        )
        is True
    )


def test_is_full_match_practicante_solo_acepta_experiencia_cero():
    assert is_full_match(make_user(experiencia_anos=0), make_job(experiencia_minima=0))
    assert not is_full_match(
        make_user(experiencia_anos=0), make_job(experiencia_minima=1)
    )


def test_is_full_match_rechaza_experiencia_superior_al_perfil():
    assert not is_full_match(make_user(experiencia_anos=2), make_job(experiencia_minima=4))
    assert is_full_match(make_user(experiencia_anos=2), make_job(experiencia_minima=2))


@pytest.mark.parametrize("nivel_vacante", ["B2", "C1"])
def test_is_full_match_b1_no_recibe_vacantes_b2_ni_c1(nivel_vacante):
    assert not is_full_match(
        make_user(nivel_ingles="B1"), make_job(nivel_ingles=nivel_vacante)
    )


def test_is_full_match_inglés_menor_o_no_especificado_si_se_acepta():
    assert is_full_match(make_user(nivel_ingles="B1"), make_job(nivel_ingles="B1"))
    assert is_full_match(
        make_user(nivel_ingles="B1"), make_job(nivel_ingles="No especificado")
    )


def test_is_full_match_perfil_c2_cubre_vacante_b2():
    assert is_full_match(make_user(nivel_ingles="C2"), make_job(nivel_ingles="B2"))


# --- vocabulario canónico compartido (SPEC 12) -------------------------------


def test_no_queda_mapa_de_alias_duplicado_en_matching():
    assert not hasattr(matching, "_EXTRA_STACK_ALIASES")


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("FastApi", "FastAPI"),
        ("react-native", "React Native"),
        ("C#", "C#"),
        (".NET", ".NET"),
        ("golang", "Go"),
        ("spring boot 3", "Spring Boot"),
    ],
)
def test_canonical_tech_usa_el_catalogo(token, expected):
    assert canonical_tech(token) == expected


def test_stack_match_percent_compara_nombres_canonicos():
    assert stack_match_percent(["FastApi", "React Native", "C#"], ["FastAPI", "reactnative", "csharp"]) == 100
