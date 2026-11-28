"""Consistencia transversal del catálogo de stacks (SPEC 12).

Comprueba que catálogo, detección, matching y selector de perfil comparten
el mismo vocabulario canónico, sin listas paralelas.
"""

from pathlib import Path

import pytest

from job_scraper import geocode, stack_catalog
from job_scraper.items import JobOfferItem
from job_scraper.matching import stack_match_percent
from job_scraper.pipelines import JobEnrichmentPipeline

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def geocode_sin_red(monkeypatch):
    """La detección de stack no debe llamar a Nominatim."""
    monkeypatch.setattr(geocode, "geocode", lambda text, cache: None)


class DummySpider:
    name = "consistencia"
    logger = None


def detect_stack(titulo="", descripcion="", tags=None):
    item = JobOfferItem(
        titulo=titulo,
        empresa="ACME",
        modalidad_raw="",
        ubicacion_texto="",
        descripcion=descripcion,
        tags_tecnologias=tags or [],
        url_oferta="https://example.com/empleo/consistencia",
    )
    return JobEnrichmentPipeline().process_item(item, DummySpider())["stack_detectado"]


def test_todos_los_nombres_canonicos_tienen_alias_y_slug():
    catalog = stack_catalog.load_catalog()
    names = {stack["name"] for stack in catalog}

    assert len(names) == len(catalog), "hay nombres canónicos duplicados"
    for stack in catalog:
        name = stack["name"]
        key = stack_catalog._normalize_key(name)
        assert stack_catalog.STACK_KEYWORDS[key] == name
        assert stack["aliases"]
        assert stack["patterns"]
        for portal in stack_catalog.PORTALS:
            assert stack_catalog.stack_slug(name, portal) == stack["slugs"][portal]


def test_opciones_del_perfil_son_subconjunto_selectable_del_catalogo():
    adapter = (ROOT / "src/core/config/stacks.ts").read_text(encoding="utf-8")
    form = (ROOT / "src/features/profile/presentation/components/ProfileForm.tsx").read_text(
        encoding="utf-8"
    )

    # El adaptador es la única derivación: filtra el catálogo, no lista nombres.
    assert "STACK_CATALOG.filter(" in adapter
    assert "stack.selectable" in adapter
    assert "stack.name" in adapter

    # El formulario consume esa derivación: sin lista local ni alias obsoleto.
    assert "import { TECH_OPTIONS } from '@/core/config/stacks';" in form
    assert "const TECH_OPTIONS" not in form
    assert "FastApi" not in form

    catalog = stack_catalog.load_catalog()
    selectable = {stack["name"] for stack in catalog if stack["selectable"]}
    assert selectable <= {stack["name"] for stack in catalog}
    assert {"React Native", "FastAPI"} <= selectable
    assert not {"Git", "Linux", "REST", "GraphQL", "Kafka"} & selectable


def test_react_native_no_es_capturado_por_react_en_deteccion_y_match():
    detected = detect_stack(
        titulo="React Native Developer",
        descripcion="Trabajarás con react-native para iOS y Android.",
    )

    assert "React Native" in detected
    assert "React" not in detected
    assert stack_match_percent(["React Native"], detected) == 100
    assert stack_match_percent(["react-native"], detected) == 100


@pytest.mark.parametrize(
    ("tag", "canonical"),
    [
        ("C#", "C#"),
        ("csharp", "C#"),
        (".NET", ".NET"),
        ("dotnet", ".NET"),
        ("Go", "Go"),
        ("golang", "Go"),
    ],
)
def test_tokens_especiales_canonicalizan_igual_en_deteccion_y_match(tag, canonical):
    assert stack_catalog.canonical_tech(tag) == canonical

    detected = detect_stack(tags=[tag])
    assert canonical in detected
    assert stack_match_percent([tag], detected) == 100
