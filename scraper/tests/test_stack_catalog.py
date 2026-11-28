import pytest

from job_scraper import stack_catalog


def test_load_catalog_devuelve_el_catalogo_canonical():
    catalog = stack_catalog.load_catalog()
    assert len(catalog) == 45

    required = {"name", "category", "selectable", "aliases", "patterns", "slugs"}
    for stack in catalog:
        assert required <= set(stack)
        assert stack["name"]
        assert stack["aliases"]
        assert stack["patterns"]
        assert set(stack["slugs"]) == set(stack_catalog.PORTALS)


def test_listas_derivadas_salen_del_catalogo():
    assert stack_catalog.STACK_KEYWORDS["reactnative"] == "React Native"
    assert stack_catalog.STACK_KEYWORDS["fastapi"] == "FastAPI"
    assert stack_catalog.STACK_KEYWORDS["golang"] == "Go"
    assert stack_catalog.STACK_KEYWORDS["ts"] == "TypeScript"
    assert ("spring boot", "Spring Boot") in stack_catalog.STACK_PATTERNS
    assert ("azure", "Azure") in stack_catalog.STACK_PATTERNS
    assert ("redis", "Redis") in stack_catalog.STACK_PATTERNS


def test_react_native_se_evalua_antes_que_react():
    canonicals = [canonical for _, canonical in stack_catalog.STACK_PATTERNS]
    assert canonicals.index("React Native") < canonicals.index("React")


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("FastApi", "FastAPI"),
        ("react-native", "React Native"),
        ("C#", "C#"),
        (".NET", ".NET"),
        ("dotnet", ".NET"),
        ("Go", "Go"),
        ("golang", "Go"),
        ("spring boot 3", "Spring Boot"),
        ("Desconocida", "Desconocida"),
        ("", ""),
    ],
)
def test_canonical_tech_resuelve_alias_del_catalogo(token, expected):
    assert stack_catalog.canonical_tech(token) == expected


def test_stack_slug_usa_los_slugs_explicitos_del_catalogo():
    assert stack_catalog.stack_slug("Node.js", "occ") == "node-js"
    assert stack_catalog.stack_slug("C#", "computrabajo") == "c-sharp"
    assert stack_catalog.stack_slug(".NET", "getonbrd") == "dotnet"
    assert stack_catalog.stack_slug("Elixir", "occ") is None
