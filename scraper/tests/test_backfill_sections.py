import pytest

import backfill_sections
from job_scraper.utils.sectionizer import split_sections


ROW = {
    "id": "11111111-1111-4111-8111-111111111111",
    "titulo": "Backend Developer",
    "empresa": "ACME",
    "descripcion": (
        "Buscamos backend developer.\n"
        "Requisitos:\n"
        "- 5 años de experiencia con Python\n"
        "GETONBRD Job ID: 12345 Seguro de gastos médicos."
    ),
    "requirements": [],
    "benefits": [],
}


class FakeResult:
    def __init__(self, data=None):
        self.data = data if data is not None else []


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.selected = None
        self.neq_filter = None
        self.eq_filters = []
        self.limit_value = None

    def select(self, fields):
        self.selected = fields
        return self

    def neq(self, column, value):
        self.neq_filter = (column, value)
        return self

    def eq(self, column, value):
        self.eq_filters.append((column, value))
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def execute(self):
        rows = self.rows[: self.limit_value] if self.limit_value else list(self.rows)
        return FakeResult(rows)


class FakeUpdate:
    def __init__(self, table, payload):
        self.table = table
        self.payload = payload
        self.eq_filters = []

    def eq(self, column, value):
        self.eq_filters.append((column, value))
        return self

    def execute(self):
        self.table.updates.append((self.payload, self.eq_filters))
        return FakeResult()


class FakeTable:
    def __init__(self, name, rows, updates):
        self.name = name
        self.rows = rows
        self.updates = updates
        self.queries = []

    def select(self, fields):
        query = FakeQuery(self.rows).select(fields)
        self.queries.append(query)
        return query

    def update(self, payload):
        return FakeUpdate(self, payload)


class FakeClient:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.updates = []
        self.tables = []
        self.fail_on_update = False

    def table(self, name):
        table = FakeTable(name, self.rows, self.updates)
        self.tables.append(table)
        return table


def test_split_row_reutiliza_sectionizer():
    payload = backfill_sections.split_row(ROW)
    expected = split_sections(ROW["descripcion"])

    assert payload == {
        "id": ROW["id"],
        "descripcion": expected["descripcion"],
        "requirements": expected["requirements"],
        "benefits": expected["benefits"],
    }


def test_fetch_candidates_aplica_filtros_y_limite():
    client = FakeClient([ROW, dict(ROW, id="otro")])

    rows = backfill_sections.fetch_candidates(client, limit=1, row_id=ROW["id"])

    query = client.tables[0].queries[0]
    assert client.tables[0].name == "vacantes"
    assert "id" in query.selected and "descripcion" in query.selected
    assert query.neq_filter == ("descripcion", "")
    assert query.eq_filters[:2] == [("requirements", "{}"), ("benefits", "{}")]
    assert query.eq_filters[2] == ("id", ROW["id"])
    assert query.limit_value == 1
    assert len(rows) == 1


@pytest.mark.parametrize(
    ("row", "payload", "expected"),
    [
        (ROW, backfill_sections.split_row(ROW), True),
        (
            dict(
                ROW,
                descripcion="Buscamos backend developer.",
                requirements=["5 años de experiencia con Python"],
                benefits=["Seguro de gastos médicos."],
            ),
            backfill_sections.split_row(ROW),
            False,
        ),
        (
            dict(ROW, descripcion="", requirements=[], benefits=[]),
            {"id": ROW["id"], "descripcion": "", "requirements": [], "benefits": []},
            False,
        ),
    ],
)
def test_has_changes(row, payload, expected):
    assert backfill_sections.has_changes(row, payload) is expected


def test_dry_run_no_escribe():
    client = FakeClient([ROW])

    counts = backfill_sections.run(client, [ROW], dry_run=True)

    assert counts == {"seleccionadas": 1, "actualizadas": 1, "sin_cambios": 0, "errores": 0}
    assert client.updates == []


def test_run_actualiza_por_id_y_es_idempotente():
    client = FakeClient([ROW])

    first = backfill_sections.run(client, [ROW])
    assert first["actualizadas"] == 1
    assert len(client.updates) == 1
    payload, filters = client.updates[0]
    assert filters == [("id", ROW["id"])]
    assert set(payload) == {"descripcion", "requirements", "benefits"}
    assert payload["requirements"][0] == "5 años de experiencia con Python"
    assert any("Seguro de gastos médicos" in b for b in payload["benefits"])

    updated = dict(ROW, **payload)
    second = backfill_sections.run(client, [updated])
    assert second["actualizadas"] == 0
    assert second["sin_cambios"] == 1
    assert len(client.updates) == 1


def test_main_sin_env_termina_sin_cliente(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "")

    def fail(*args, **kwargs):
        raise AssertionError("no se debe crear cliente sin credenciales")

    monkeypatch.setattr(backfill_sections, "build_client", fail)
    monkeypatch.setattr(backfill_sections, "load_environment", lambda: None)

    assert backfill_sections.main([]) == 2
