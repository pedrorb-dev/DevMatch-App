import pytest

import backfill_stacks
from job_scraper.pipelines import JobEnrichmentPipeline

ROW = {
    "id": "11111111-1111-4111-8111-111111111111",
    "titulo": "React Native Developer",
    "empresa": "ACME",
    "descripcion": "Buscamos desarrollador con Python y React Native.",
    "stack_detectado": ["React"],
}


class FakeResult:
    def __init__(self, data=None):
        self.data = data if data is not None else []


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.selected = None
        self.eq_filters = []
        self.limit_value = None

    def select(self, fields):
        self.selected = fields
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

    def table(self, name):
        table = FakeTable(name, self.rows, self.updates)
        self.tables.append(table)
        return table


@pytest.fixture
def pipeline():
    return JobEnrichmentPipeline()


def test_fetch_candidates_aplica_filtros_y_limite():
    client = FakeClient([ROW, dict(ROW, id="otro")])

    rows = backfill_stacks.fetch_candidates(client, limit=1, row_id=ROW["id"])

    query = client.tables[0].queries[0]
    assert client.tables[0].name == "vacantes"
    assert "id" in query.selected and "descripcion" in query.selected
    assert "stack_detectado" in query.selected
    assert query.eq_filters == [("id", ROW["id"])]
    assert query.limit_value == 1
    assert len(rows) == 1


def test_compute_stack_reutiliza_la_deteccion_del_pipeline(pipeline):
    detected = backfill_stacks.compute_stack(ROW, pipeline)

    assert "React Native" in detected
    assert "React" not in detected
    assert "Python" in detected
    assert detected == pipeline._detect_stack(
        {
            "titulo": ROW["titulo"],
            "descripcion": ROW["descripcion"],
            "tags_tecnologias": [],
        }
    )


def test_has_changes_ignora_el_orden_y_detecta_valores_obsoletos():
    detected = ["React Native", "Python"]

    assert backfill_stacks.has_changes(ROW, detected) is True
    assert backfill_stacks.has_changes(dict(ROW, stack_detectado=detected), detected) is False
    assert (
        backfill_stacks.has_changes(
            dict(ROW, stack_detectado=list(reversed(detected))), detected
        )
        is False
    )


def test_dry_run_no_escribe():
    client = FakeClient([ROW])
    pipeline = JobEnrichmentPipeline()

    counts = backfill_stacks.run(client, [ROW], dry_run=True, pipeline=pipeline)

    assert counts == {"seleccionadas": 1, "actualizadas": 1, "sin_cambios": 0, "errores": 0}
    assert client.updates == []


def test_run_actualiza_solo_stack_y_es_idempotente():
    client = FakeClient([ROW])
    pipeline = JobEnrichmentPipeline()

    first = backfill_stacks.run(client, [ROW], pipeline=pipeline)
    assert first["actualizadas"] == 1
    assert len(client.updates) == 1
    payload, filters = client.updates[0]
    assert filters == [("id", ROW["id"])]
    assert set(payload) == {"stack_detectado"}
    assert "React Native" in payload["stack_detectado"]
    assert "React" not in payload["stack_detectado"]

    updated = dict(ROW, stack_detectado=payload["stack_detectado"])
    second = backfill_stacks.run(client, [updated], pipeline=pipeline)
    assert second["actualizadas"] == 0
    assert second["sin_cambios"] == 1
    assert len(client.updates) == 1


def test_main_sin_env_termina_sin_cliente(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "")

    def fail(*args, **kwargs):
        raise AssertionError("no se debe crear cliente sin credenciales")

    monkeypatch.setattr(backfill_stacks, "build_client", fail)
    monkeypatch.setattr(backfill_stacks, "load_environment", lambda: None)

    assert backfill_stacks.main([]) == 2
