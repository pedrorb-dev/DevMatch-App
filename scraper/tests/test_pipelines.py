import pytest
from scrapy.exceptions import DropItem

from job_scraper.items import JobOfferItem
from job_scraper.pipelines import DataCleaningPipeline, JobEnrichmentPipeline


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
    assert enriched["es_practicante"] is True
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
    assert enriched["es_practicante"] is True  # entry level / junior
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
