from datetime import datetime, timezone
from types import SimpleNamespace

from job_scraper import notify


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def select(self, columns):
        self.calls.append(("select", columns))
        return self

    def gte(self, column, value):
        self.calls.append(("gte", column, value))
        return self

    @property
    def not_(self):
        return self

    def is_(self, column, value):
        self.calls.append(("is", column, value, True))
        return self

    def execute(self):
        return SimpleNamespace(data=list(self.rows))


class FakeClient:
    def __init__(self, jobs, profiles):
        self.tables = {
            "vacantes": FakeQuery(jobs),
            "user_profiles": FakeQuery(profiles),
        }

    def table(self, name):
        return self.tables[name]


class FakeResponse:
    def __init__(self, count):
        self.count = count

    def raise_for_status(self):
        return None

    def json(self):
        return {"data": [{"status": "ok"} for _ in range(self.count)]}


RUN_STARTED_AT = datetime(2026, 11, 27, 8, 0, tzinfo=timezone.utc)


def make_job(job_id=1, stack=None, experiencia_minima=2, nivel_ingles="B1"):
    return {
        "id": job_id,
        "titulo": "Desarrollador Python",
        "empresa": "ACME",
        "stack_detectado": ["Python", "SQL"] if stack is None else stack,
        "experiencia_minima": experiencia_minima,
        "nivel_ingles": nivel_ingles,
    }


def make_profile(token="ExpoPushToken[abc]", experiencia_anos=3, nivel_ingles="B2", stack=None):
    return {
        "id": "user-1",
        "stack": ["Python", "SQL"] if stack is None else stack,
        "experiencia_anos": experiencia_anos,
        "nivel_ingles": nivel_ingles,
        "expo_push_token": token,
    }


def setup_client(monkeypatch, jobs, profiles):
    client = FakeClient(jobs, profiles)
    monkeypatch.setattr(notify, "create_client", lambda url, key: client)
    return client


def capture_posts(monkeypatch):
    posts = []

    def fake_post(url, **kwargs):
        messages = kwargs["json"]
        posts.append((url, kwargs))
        return FakeResponse(len(messages))

    monkeypatch.setattr(notify.requests, "post", fake_post)
    return posts


def test_notify_full_matches_envia_solo_match_completo_con_token(monkeypatch):
    client = setup_client(
        monkeypatch,
        jobs=[make_job(1), make_job(2, stack=["Java"])],
        profiles=[
            make_profile(),
            make_profile(token=None),
            make_profile(token="ExpoPushToken[otro]", experiencia_anos=0),
        ],
    )
    posts = capture_posts(monkeypatch)

    sent = notify.notify_full_matches("https://supabase.test", "key", RUN_STARTED_AT)

    assert sent == 1
    assert len(posts) == 1
    assert posts[0][0] == notify.EXPO_PUSH_URL
    message = posts[0][1]["json"][0]
    assert message["to"] == "ExpoPushToken[abc]"
    assert message["title"] == "100% match con tu stack"
    assert message["body"] == "ACME · Desarrollador Python"
    assert message["data"] == {"url": "/work/1"}
    assert ("gte", "created_at", RUN_STARTED_AT.isoformat()) in client.tables[
        "vacantes"
    ].calls
    assert ("is", "expo_push_token", "null", True) in client.tables[
        "user_profiles"
    ].calls


def test_notify_full_matches_sin_credenciales_no_consulta_ni_envia(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("No debería crear cliente sin credenciales")

    monkeypatch.setattr(notify, "create_client", fail)
    posts = capture_posts(monkeypatch)

    assert notify.notify_full_matches("", "", RUN_STARTED_AT) == 0
    assert posts == []


def test_notify_full_matches_sin_tokens_no_envia(monkeypatch):
    setup_client(monkeypatch, jobs=[make_job()], profiles=[make_profile(token=None)])
    posts = capture_posts(monkeypatch)

    assert notify.notify_full_matches("https://supabase.test", "key", RUN_STARTED_AT) == 0
    assert posts == []


def test_notify_full_matches_agrupa_en_lotes_de_100(monkeypatch):
    jobs = [make_job(job_id=i) for i in range(101)]
    setup_client(monkeypatch, jobs, [make_profile()])
    posts = capture_posts(monkeypatch)

    sent = notify.notify_full_matches("https://supabase.test", "key", RUN_STARTED_AT)

    assert sent == 101
    assert [len(post[1]["json"]) for post in posts] == [100, 1]


def test_notify_full_matches_no_falla_si_expo_rechaza_el_lote(monkeypatch):
    setup_client(monkeypatch, [make_job()], [make_profile()])

    def fail_post(url, **kwargs):
        raise RuntimeError("Expo caído")

    monkeypatch.setattr(notify.requests, "post", fail_post)

    assert notify.notify_full_matches("https://supabase.test", "key", RUN_STARTED_AT) == 1
