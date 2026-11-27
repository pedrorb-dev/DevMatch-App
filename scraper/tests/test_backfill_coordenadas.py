import pytest

import backfill_coordenadas


ROW = {
    "id": "11111111-1111-4111-8111-111111111111",
    "titulo": "Backend Developer",
    "empresa": "ACME",
    "ubicacion_texto": "Monterrey, México",
    "lat": None,
    "lng": None,
}


class FakeResult:
    def __init__(self, data=None):
        self.data = data if data is not None else []


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.selected = None
        self.neq_filter = None
        self.is_filter = None
        self.eq_filters = []
        self.limit_value = None

    def select(self, fields):
        self.selected = fields
        return self

    def neq(self, column, value):
        self.neq_filter = (column, value)
        return self

    def is_(self, column, value):
        self.is_filter = (column, value)
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


@pytest.fixture(autouse=True)
def geocode_sin_red(monkeypatch):
    monkeypatch.setattr(
        backfill_coordenadas, "geocode", lambda text, cache: (25.6866, -100.3161)
    )
    monkeypatch.setattr(backfill_coordenadas, "load_cache", lambda: {})


def test_fetch_candidates_aplica_filtros_y_limite():
    client = FakeClient([ROW, dict(ROW, id="otro")])

    rows = backfill_coordenadas.fetch_candidates(client, limit=1, row_id=ROW["id"])

    query = client.tables[0].queries[0]
    assert client.tables[0].name == "vacantes"
    assert "ubicacion_texto" in query.selected and "lat" in query.selected
    assert query.neq_filter == ("ubicacion_texto", "")
    assert query.is_filter == ("lat", "null")
    assert query.eq_filters == [("id", ROW["id"])]
    assert query.limit_value == 1
    assert len(rows) == 1


def test_run_actualiza_lat_lng_por_id():
    client = FakeClient([ROW])

    counts = backfill_coordenadas.run(client, [ROW])

    assert counts == {
        "seleccionadas": 1,
        "actualizadas": 1,
        "sin_coordenadas": 0,
        "errores": 0,
    }
    payload, filters = client.updates[0]
    assert payload == {"lat": 25.6866, "lng": -100.3161}
    assert filters == [("id", ROW["id"])]


def test_dry_run_no_escribe(monkeypatch):
    client = FakeClient([ROW])

    counts = backfill_coordenadas.run(client, [ROW], dry_run=True)

    assert counts["actualizadas"] == 1
    assert client.updates == []


def test_sin_coordenadas_no_escribe(monkeypatch):
    monkeypatch.setattr(backfill_coordenadas, "geocode", lambda text, cache: None)
    client = FakeClient([ROW])

    counts = backfill_coordenadas.run(client, [ROW])

    assert counts["sin_coordenadas"] == 1
    assert counts["actualizadas"] == 0
    assert client.updates == []


def test_main_sin_env_termina_sin_cliente(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "")

    def fail(*args, **kwargs):
        raise AssertionError("no se debe crear cliente sin credenciales")

    monkeypatch.setattr(backfill_coordenadas, "build_client", fail)
    monkeypatch.setattr(backfill_coordenadas, "load_environment", lambda: None)

    assert backfill_coordenadas.main([]) == 2
