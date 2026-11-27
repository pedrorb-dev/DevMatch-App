import pytest
from scrapy.exceptions import DropItem

from job_scraper import geocode
from job_scraper.items import JobOfferItem
from job_scraper.pipelines import DataCleaningPipeline, JobEnrichmentPipeline, SupabaseUpsertPipeline


@pytest.fixture(autouse=True)
def geocode_sin_red(monkeypatch):
    """Los tests de pipelines no deben llamar a Nominatim."""
    monkeypatch.setattr(geocode, "geocode", lambda text, cache: None)


class DummySpider:
    name = "hireline"
    logger = None


def run_cleaning(item):
    pipeline = DataCleaningPipeline()
    return pipeline.process_item(item, DummySpider())


def run_enrichment(item):
    pipeline = JobEnrichmentPipeline()
    return pipeline.process_item(item, DummySpider())


def test_vacante_en_espanol_normalizacion():
    item = JobOfferItem(
        titulo="Desarrollador Java Junior (Practicante)",
        empresa="ACME México",
        modalidad_raw="",
        ubicacion_texto="Jalisco - Híbrido",
        descripcion=(
            "<p>Buscamos practicante sin experiencia para desarrollar APIs con Java, "
            "Spring Boot, SQL y Docker. Inglés intermedio.</p>"
        ),
        tags_tecnologias=["Java", "springboot"],
        url_oferta="https://hireline.io/mx/empleos/123?ref=test",
    )

    cleaned = run_cleaning(item)
    enriched = run_enrichment(cleaned)

    assert enriched["titulo"] == "Desarrollador Java Junior (Practicante)"
    assert enriched["url_oferta"].startswith("https://hireline.io/mx/empleos/123")
    assert enriched["modalidad"] == "Híbrido"
    assert enriched["experiencia_minima"] == 0  # "practicante" + "sin experiencia"
    assert enriched["nivel_ingles"] == "B1"
    assert "Java" in enriched["stack_detectado"]
    assert "Spring Boot" in enriched["stack_detectado"]
    assert "SQL" in enriched["stack_detectado"]
    assert "Docker" in enriched["stack_detectado"]
    assert enriched["requirements"] == []
    assert enriched["benefits"] == []


def test_vacante_en_ingles_no_se_descarta_y_se_normaliza():
    item = JobOfferItem(
        titulo="Junior Software Engineer (Remote)",
        empresa="Global Tech",
        modalidad_raw="Remote",
        ubicacion_texto="Remote: Mexico",
        descripcion=(
            "We are looking for an entry level engineer to join our team. "
            "You will work with Python, Docker, SQL and AWS services. "
            "This is a great opportunity to grow your software development skills."
        ),
        tags_tecnologias=["python", "aws"],
        url_oferta="https://hireline.io/remoto/empleos/456",
    )

    cleaned = run_cleaning(item)  # must not raise DropItem
    enriched = run_enrichment(cleaned)

    assert enriched["empresa"] == "Global Tech"
    assert enriched["modalidad"] == "Remoto"
    assert enriched["experiencia_minima"] == 1  # sin indicador de entrada ni años
    assert enriched["nivel_ingles"] in {"B1", "B2", "C1"}  # English description => at least B1
    assert "Python" in enriched["stack_detectado"]
    assert "Docker" in enriched["stack_detectado"]
    assert "SQL" in enriched["stack_detectado"]
    assert "AWS" in enriched["stack_detectado"]


def test_cleaning_descarta_items_sin_titulo_o_url():
    pipeline = DataCleaningPipeline()
    with pytest.raises(DropItem):
        pipeline.process_item(JobOfferItem(titulo="", empresa="X", url_oferta="https://x"), DummySpider())
    with pytest.raises(DropItem):
        pipeline.process_item(JobOfferItem(titulo="Dev", empresa="X", url_oferta=""), DummySpider())


def test_vacante_espanol_separa_conocimientos_deseables_y_ofrecemos():
    item = JobOfferItem(
        titulo="Software Developer",
        empresa="THE BLUE PEOPLE",
        modalidad_raw="Remote",
        ubicacion_texto="Remoto: México",
        descripcion=(
            "Requisitos:\n"
            "- Experiencia programando en cualquier lenguaje\n"
            "- Conocimiento sobre base de datos\n"
            "- Avanzado nivel de inglés indispensable\n\n"
            "Actividades:\n"
            "- Desarrollo de programas que ayuden a automatizar procesos\n"
            "- Cumplir con las mejores prácticas de programación\n\n"
            "Ofrecemos:\n"
            "- Home office\n"
            "- Horario flexible\n"
            "- Capacitaciones constantes\n"
        ),
        tags_tecnologias=["SQL"],
        url_oferta="https://hireline.io/mx/empleos/software-developer/114704",
    )

    cleaned = run_cleaning(item)
    enriched = run_enrichment(cleaned)

    assert any("Experiencia programando" in r for r in enriched["requirements"])
    assert any("base de datos" in r.lower() for r in enriched["requirements"])
    assert any("Home office" in b for b in enriched["benefits"])
    assert any("Horario flexible" in b for b in enriched["benefits"])
    assert "Ofrecemos" not in enriched["descripcion"]
    assert "Requisitos" not in enriched["descripcion"]
    assert "Actividades" in enriched["descripcion"] or "automatizar" in enriched["descripcion"]
    assert enriched["modalidad"] == "Remoto"
    assert enriched["nivel_ingles"] == "B2"


def test_vacante_ingles_separa_requirements_y_benefits():
    item = JobOfferItem(
        titulo="Senior .NET Developer",
        empresa="Acme",
        modalidad_raw="Remote",
        ubicacion_texto="Remote: Mexico",
        descripcion=(
            "Build scalable solutions and make an impact.\n\n"
            "What We're Looking For:\n"
            "- 5+ years of experience in software development using C#\n"
            "- Experience with .NET Core and RESTful APIs\n"
            "- Strong SQL Server skills\n\n"
            "Responsibilities:\n"
            "- Design, develop, test, and maintain applications\n\n"
            "What We Offer:\n"
            "- Remote work\n"
            "- Professional development opportunities\n"
        ),
        tags_tecnologias=[".NET", "C#"],
        url_oferta="https://hireline.io/mx/empleos/senior-net-developer/1",
    )

    cleaned = run_cleaning(item)
    enriched = run_enrichment(cleaned)

    assert any("5+ years" in r for r in enriched["requirements"])
    assert any("RESTful APIs" in r for r in enriched["requirements"])
    assert any("Remote work" in b for b in enriched["benefits"])
    assert "What We Offer" not in enriched["descripcion"]
    assert "What We're Looking For" not in enriched["descripcion"]
    assert "Responsibilities" in enriched["descripcion"] or "maintain applications" in enriched["descripcion"]
    assert enriched["nivel_ingles"] in {"B1", "B2", "C1"}
    assert enriched["experiencia_minima"] == 5  # "5+ years"


# --- experiencia_minima (bilingüe) -----------------------------------------


def detect_experiencia(titulo, descripcion=""):
    item = JobOfferItem(
        titulo=titulo,
        empresa="ACME",
        modalidad_raw="",
        ubicacion_texto="",
        descripcion=descripcion,
        tags_tecnologias=[],
        url_oferta="https://example.com/empleo/1",
    )
    return run_enrichment(run_cleaning(item))["experiencia_minima"]


@pytest.mark.parametrize(
    ("titulo", "descripcion", "expected"),
    [
        # 1. Años explícitos (ES/EN), incluidos rangos (se toma el mínimo)
        ("Desarrollador Java", "Requisitos: 3 años de experiencia con Java", 3),
        ("Backend Engineer", "You need 2+ years of experience with Python", 2),
        ("Desarrollador Backend", "1 a 3 años de experiencia en desarrollo", 1),
        ("Data Engineer", "2-4 years of experience in data pipelines", 2),
        # La regla de años explícitos gana a los indicadores de entrada/senior
        ("Becario de desarrollo", "Buscamos becario con 2 años de experiencia", 2),
        # 2. Indicadores de entrada
        ("Becario de TI", "", 0),
        ("Practicante de desarrollo", "", 0),
        ("Desarrollador sin experiencia", "", 0),
        ("Software Engineer Intern", "", 0),
        ("Trainee Developer", "", 0),
        ("Estadías en desarrollo", "", 0),
        ("Developer", "No experience required, we will train you", 0),
        # 3. Indicador senior sin número
        ("Senior Java Developer", "", 4),
        ("Sr. Backend Developer", "", 4),
        ("Lead Software Engineer", "", 4),
        # 4. Sin mención
        ("Desarrollador Java", "", 1),
        ("Frontend Developer", "React and TypeScript para productos internos", 1),
    ],
)
def test_experiencia_minima_bilingue(titulo, descripcion, expected):
    assert detect_experiencia(titulo, descripcion) == expected


def test_telecommute_se_normaliza_a_remoto():
    item = JobOfferItem(
        titulo="Desarrollador Python",
        empresa="ACME",
        modalidad_raw="TELECOMMUTE",
        ubicacion_texto="",
        descripcion="",
        tags_tecnologias=[],
        url_oferta="https://www.occ.com.mx/empleo/oferta/1",
    )

    enriched = run_enrichment(run_cleaning(item))
    assert enriched["modalidad"] == "Remoto"


@pytest.mark.parametrize("modalidad_raw", ["Desde casa", "Teletrabajo", "DESDE CASA", "teletrabajo"])
def test_modalidad_computrabajo_se_normaliza_a_remoto(modalidad_raw):
    item = JobOfferItem(
        titulo="Desarrollador Python",
        empresa="ACME",
        modalidad_raw=modalidad_raw,
        ubicacion_texto="",
        descripcion="",
        tags_tecnologias=[],
        url_oferta="https://mx.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-1",
    )

    enriched = run_enrichment(run_cleaning(item))
    assert enriched["modalidad"] == "Remoto"


def test_modalidad_desde_casa_en_ubicacion_es_remoto():
    item = JobOfferItem(
        titulo="Desarrollador Python",
        empresa="ACME",
        modalidad_raw="",
        ubicacion_texto="Ciudad de México - Desde casa",
        descripcion="",
        tags_tecnologias=[],
        url_oferta="https://mx.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-2",
    )

    enriched = run_enrichment(run_cleaning(item))
    assert enriched["modalidad"] == "Remoto"


# --- nivel_ingles -----------------------------------------------------------


def detect_ingles(titulo, descripcion=""):
    item = JobOfferItem(
        titulo=titulo,
        empresa="ACME",
        modalidad_raw="",
        ubicacion_texto="",
        descripcion=descripcion,
        tags_tecnologias=[],
        url_oferta="https://example.com/empleo/1",
    )
    return run_enrichment(run_cleaning(item))["nivel_ingles"]


@pytest.mark.parametrize(
    ("titulo", "descripcion"),
    [
        ("Desarrollador Java", "English required para integrarse al equipo."),
        ("Desarrollador Java", "Inglés requerido."),
        ("Backend Developer", "Requisitos:\n- Inglés requerido\n- Java"),
        ("Backend Developer", "Requirements:\n- English required\n- Java"),
    ],
)
def test_nivel_ingles_english_required_es_b1(titulo, descripcion):
    assert detect_ingles(titulo, descripcion) == "B1"


@pytest.mark.parametrize(
    ("descripcion", "expected"),
    [
        # Las menciones explícitas de nivel mantienen su precedencia.
        ("English required. Advanced English level.", "B2"),
        ("Inglés requerido. Nivel avanzado de inglés.", "B2"),
        ("English required. Bilingual candidate.", "C1"),
        ("Inglés requerido. Nativo.", "C1"),
        ("English required. Intermediate level.", "B1"),
    ],
)
def test_nivel_ingles_english_required_no_rompe_precedencias(descripcion, expected):
    assert detect_ingles("Desarrollador Java", descripcion) == expected


# --- url_oferta canónica (sin fragmento ni query params) -------------------


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://mx.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-1",
            "https://mx.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-1",
        ),
        (
            "https://mx.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-1#fragmento",
            "https://mx.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-1",
        ),
        (
            "https://mx.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-1?ref=test",
            "https://mx.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-1",
        ),
        (
            "https://mx.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-1?ref=test#fragmento",
            "https://mx.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-1",
        ),
        (
            "https://mx.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-1#fragmento?ref=test",
            "https://mx.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-1",
        ),
    ],
)
def test_cleaning_url_oferta_sin_fragmento_ni_query(url, expected):
    item = JobOfferItem(
        titulo="Desarrollador Python",
        empresa="ACME",
        modalidad_raw="",
        ubicacion_texto="",
        descripcion="",
        tags_tecnologias=[],
        url_oferta=url,
    )

    cleaned = run_cleaning(item)
    assert cleaned["url_oferta"] == expected


def test_pipeline_no_emite_es_practicante():
    item = JobOfferItem(
        titulo="Desarrollador Java",
        empresa="ACME",
        modalidad_raw="Remote",
        ubicacion_texto="Remote: Mexico",
        descripcion="",
        tags_tecnologias=[],
        url_oferta="https://example.com/empleo/2",
    )

    enriched = run_enrichment(run_cleaning(item))
    assert "experiencia_minima" in enriched
    assert "es_practicante" not in enriched


# --- splitter delegado a sectionizer (SPEC 08) ---------------------------


def test_pipeline_no_contiene_splitter_duplicado():
    assert not hasattr(JobEnrichmentPipeline, "_classify_heading")
    assert not hasattr(JobEnrichmentPipeline, "_split_sections_from_text")


def test_pipeline_delega_split_con_pie_de_fuente():
    item = JobOfferItem(
        titulo="Backend Developer",
        empresa="ACME",
        modalidad_raw="",
        ubicacion_texto="",
        descripcion=(
            "Buscamos backend developer.\n"
            "Requisitos:\n"
            "- 5 años de experiencia con Python\n"
            "GETONBRD Job ID: 12345 Seguro de gastos médicos. Vacaciones extra."
        ),
        tags_tecnologias=["Python"],
        url_oferta="https://www.getonbrd.com/jobs/backend/1",
    )

    enriched = run_enrichment(run_cleaning(item))

    assert any("5 años de experiencia" in r for r in enriched["requirements"])
    assert any("Seguro de gastos médicos" in b for b in enriched["benefits"])
    assert any("Vacaciones extra" in b for b in enriched["benefits"])
    assert "GETONBRD Job ID" not in enriched["descripcion"]


def test_pipeline_delega_split_de_vinietas_sin_encabezado():
    item = JobOfferItem(
        titulo="Backend Developer",
        empresa="ACME",
        modalidad_raw="",
        ubicacion_texto="",
        descripcion="Buscamos talento. - 5+ años de experiencia en Java - seguro de gastos médicos",
        tags_tecnologias=[],
        url_oferta="https://www.getonbrd.com/jobs/backend/2",
    )

    enriched = run_enrichment(run_cleaning(item))

    assert any("5+ años de experiencia" in r for r in enriched["requirements"])
    assert any("seguro de gastos médicos" in b for b in enriched["benefits"])
    assert "Buscamos talento" in enriched["descripcion"]


def test_pipeline_no_reemplaza_listas_ya_proporcionadas():
    item = JobOfferItem(
        titulo="Backend Developer",
        empresa="ACME",
        modalidad_raw="",
        ubicacion_texto="",
        descripcion="Requisitos:\n- Otro requisito",
        requirements=["Requisito previo"],
        benefits=["Beneficio previo"],
        tags_tecnologias=[],
        url_oferta="https://www.getonbrd.com/jobs/backend/3",
    )

    enriched = run_enrichment(run_cleaning(item))

    assert enriched["requirements"] == ["Requisito previo"]
    assert enriched["benefits"] == ["Beneficio previo"]


# --- geocodificación (SPEC 10) ---------------------------------------------


def test_enrichment_setea_lat_lng_desde_geocode(monkeypatch):
    monkeypatch.setattr(geocode, "geocode", lambda text, cache: (25.6866, -100.3161))
    item = JobOfferItem(
        titulo="Backend Developer",
        empresa="ACME",
        modalidad_raw="",
        ubicacion_texto="Monterrey, México",
        descripcion="",
        tags_tecnologias=[],
        url_oferta="https://example.com/empleo/geo-1",
    )

    enriched = run_enrichment(item)

    assert enriched["lat"] == 25.6866
    assert enriched["lng"] == -100.3161


def test_enrichment_deja_lat_lng_null_cuando_no_hay_coordenadas(monkeypatch):
    texts = []

    def fake_geocode(text, cache):
        texts.append(text)
        return None

    monkeypatch.setattr(geocode, "geocode", fake_geocode)
    item = JobOfferItem(
        titulo="Backend Developer",
        empresa="ACME",
        modalidad_raw="",
        ubicacion_texto="",
        descripcion="",
        tags_tecnologias=[],
        url_oferta="https://example.com/empleo/geo-2",
    )

    enriched = run_enrichment(item)

    assert texts == [""]
    assert enriched["lat"] is None
    assert enriched["lng"] is None


class FakeUpsertClient:
    def __init__(self):
        self.upserts = []

    def table(self, name):
        assert name == "vacantes"
        return self

    def upsert(self, payload, on_conflict):
        self.upserts.append((payload, on_conflict))
        return self

    def execute(self):
        return None


def test_upsert_incluye_lat_lng_en_payload():
    pipeline = SupabaseUpsertPipeline("https://supabase.test", "key")
    pipeline.client = FakeUpsertClient()
    item = JobOfferItem(
        titulo="Backend Developer",
        empresa="ACME",
        modalidad_raw="",
        ubicacion_texto="Monterrey, México",
        descripcion="",
        tags_tecnologias=[],
        url_oferta="https://example.com/empleo/geo-3",
        lat=25.6866,
        lng=-100.3161,
    )

    pipeline.process_item(item, DummySpider())

    payload, on_conflict = pipeline.client.upserts[0]
    assert on_conflict == "url_oferta"
    assert payload["lat"] == 25.6866
    assert payload["lng"] == -100.3161
    assert payload["ubicacion_texto"] == "Monterrey, México"


@pytest.mark.parametrize(
    ("value", "expected"),
    [("25.68", 25.68), (None, None), ("no es número", None)],
)
def test_upsert_coordena_invalida_se_vuelve_null(value, expected):
    assert SupabaseUpsertPipeline._coerce_coordenada(value) == expected
