from scrapy.http import HtmlResponse, Request

from job_scraper.pipelines import DataCleaningPipeline, JobEnrichmentPipeline
from job_scraper.spiders.getonbrd_spider import GetOnBrdSpider
from job_scraper.utils.query_builder import SearchQueryBuilder


DETAIL_URL = (
    "https://www.getonbrd.com/empleos/desarrollo-de-software/desarrollador-python"
)
LISTING_URL = "https://www.getonbrd.com/jobs-python"


class DummySpider:
    name = "getonbrd"
    logger = None


def make_response(html, url=DETAIL_URL, meta=None):
    request = Request(url, meta=meta or {})
    return HtmlResponse(url=url, body=html.encode("utf-8"), encoding="utf-8", request=request)


def make_spider(stack=None, experiencia_anos=2):
    rows = [
        {
            "stack": stack if stack is not None else ["Python"],
            "experiencia_anos": experiencia_anos,
        }
    ]
    spider = GetOnBrdSpider()
    spider.query_builder = SearchQueryBuilder(rows=rows)
    return spider


def make_detail_html(
    title="Desarrollador Python",
    company="ACME",
    description="Buscamos desarrollador Python con experiencia en APIs.",
    location_type=None,
    applicant_countries=(),
    locations=None,
    locality=None,
    address_country=None,
    location_text="",
    qualifications="",
    skills=(),
):
    """Ficha con microdata schema.org como la que publica Get on Board."""
    if locations is None:
        locations = (
            [(locality, address_country)] if (locality or address_country) else []
        )

    parts = [
        '<html><body><div id="right-col" itemscope '
        'itemtype="http://schema.org/JobPosting">',
        '<h1 class="gb-landing-cover__title">'
        f'<span itemprop="title">{title}</span></h1>',
    ]

    if company is not None:
        parts.append(
            '<div itemprop="hiringOrganization" itemscope '
            'itemtype="http://schema.org/Organization">'
            f'<strong itemprop="name">{company}</strong></div>'
        )

    if location_type:
        parts.append(f'<meta itemprop="jobLocationType" content="{location_type}">')

    for country in applicant_countries:
        parts.append(
            '<span itemprop="applicantLocationRequirements" itemscope '
            'itemtype="http://schema.org/Country">'
            f'<meta itemprop="name" content="{country}"></span>'
        )

    if locations:
        for location_locality, location_country in locations:
            address = (
                '<span itemprop="jobLocation" itemscope '
                'itemtype="http://schema.org/Place">'
                '<span itemprop="address" itemscope '
                'itemtype="http://schema.org/PostalAddress">'
            )
            if location_locality:
                address += (
                    f'<meta itemprop="addressLocality" content="{location_locality}">'
                )
            if location_country:
                address += (
                    f'<meta itemprop="addressCountry" content="{location_country}">'
                )
            address += "</span></span>"
            parts.append(address)

    if location_text:
        parts.append(f'<span class="location">{location_text}</span>')

    if skills:
        tags = "".join(
            f'<a class="gb-tags__item" href="/jobs-tag/{tag.lower()}">{tag}</a>'
            for tag in skills
        )
        parts.append(f'<div itemprop="skills">{tags}</div>')

    if qualifications:
        parts.append(f'<span itemprop="qualifications">{qualifications}</span>')

    parts.append(
        f'<div id="job-body" itemprop="description"><p>{description}</p></div>'
    )
    parts.append("</div></body></html>")
    return "".join(parts)


def make_css_only_html(
    title="Desarrollador Backend",
    company="ACME",
    location_text="Remote",
    description="Vacante remota con Python y SQL.",
):
    """Ficha sin microdata: el spider debe caer al fallback CSS/XPath."""
    return (
        "<html><body>"
        f'<h1 class="gb-landing-cover__title">{title}</h1>'
        f'<a href="/companies/{company.lower()}"><strong>{company}</strong></a>'
        f'<span class="location">{location_text}</span>'
        f'<div id="job-body"><p>{description}</p></div>'
        "</body></html>"
    )


# --- filtro de elegibilidad México/Remoto ----------------------------------


def test_remoto_mexico_se_conserva():
    spider = make_spider()
    response = make_response(
        make_detail_html(location_type="TELECOMMUTE", applicant_countries=["Mexico"])
    )

    item = list(spider.parse_detail(response))[0]

    assert item["titulo"] == "Desarrollador Python"
    assert item["modalidad_raw"] == "Remoto"
    assert item["url_oferta"] == DETAIL_URL


def test_remoto_chile_se_descarta():
    spider = make_spider()
    response = make_response(
        make_detail_html(location_type="TELECOMMUTE", applicant_countries=["Chile"])
    )

    assert list(spider.parse_detail(response)) == []


def test_remoto_estados_unidos_se_descarta():
    spider = make_spider()
    response = make_response(
        make_detail_html(
            location_type="TELECOMMUTE", applicant_countries=["United States"]
        )
    )

    assert list(spider.parse_detail(response)) == []


def test_remoto_multipais_latam_se_conserva():
    spider = make_spider()
    response = make_response(
        make_detail_html(
            location_type="TELECOMMUTE",
            applicant_countries=["Chile", "Colombia", "Mexico"],
        )
    )

    items = list(spider.parse_detail(response))

    assert len(items) == 1
    assert items[0]["modalidad_raw"] == "Remoto"


def test_remoto_sin_restriccion_se_conserva():
    spider = make_spider()
    response = make_response(make_detail_html(location_type="TELECOMMUTE"))

    items = list(spider.parse_detail(response))

    assert len(items) == 1
    assert items[0]["modalidad_raw"] == "Remoto"


def test_presencial_chile_se_descarta():
    spider = make_spider()
    response = make_response(
        make_detail_html(
            locality="Santiago",
            address_country="CL",
            location_text="Santiago (On-site)",
        )
    )

    assert list(spider.parse_detail(response)) == []


def test_presencial_mexico_se_conserva():
    spider = make_spider()
    response = make_response(
        make_detail_html(
            locality="Ciudad de México",
            address_country="MX",
            location_text="Ciudad de México (On-site)",
        )
    )

    item = list(spider.parse_detail(response))[0]

    assert item["modalidad_raw"] == "Presencial"
    assert item["ubicacion_texto"] == "Ciudad de México, MX"


def test_hibrido_mexico_se_conserva():
    spider = make_spider()
    response = make_response(
        make_detail_html(
            locality="Ciudad de México",
            address_country="MX",
            location_text="Ciudad de México (Hybrid)",
        )
    )

    item = list(spider.parse_detail(response))[0]

    assert item["modalidad_raw"] == "Híbrido"


def test_presencial_sin_pais_se_conserva():
    spider = make_spider()
    response = make_response(
        make_detail_html(location_text="Guadalajara (On-site)")
    )

    items = list(spider.parse_detail(response))

    assert len(items) == 1
    assert items[0]["modalidad_raw"] == "Presencial"


def test_presencial_multipais_fuera_de_mexico_se_descarta():
    spider = make_spider()
    response = make_response(
        make_detail_html(
            locations=[
                ("Lima", "PE"),
                ("Puerto Montt", "CL"),
                ("Santiago", "CL"),
            ],
            location_text="Lima, Puerto Montt, Santiago (Hybrid)",
        )
    )

    assert list(spider.parse_detail(response)) == []


def test_presencial_multipais_con_mexico_se_conserva():
    spider = make_spider()
    response = make_response(
        make_detail_html(
            locations=[("Bogotá", "CO"), ("Ciudad de México", "MX")],
            location_text="Bogotá, Ciudad de México (On-site)",
        )
    )

    item = list(spider.parse_detail(response))[0]

    assert item["modalidad_raw"] == "Presencial"
    assert item["ubicacion_texto"] == "Bogotá, CO; Ciudad de México, MX"


# --- extracción ------------------------------------------------------------


def test_extrae_microdata_completa():
    spider = make_spider()
    response = make_response(
        make_detail_html(
            company="KODE IT",
            description="Requisitos: Python, SQL y Docker.",
            location_type="TELECOMMUTE",
            applicant_countries=["Mexico"],
            locality="Ciudad de México",
            address_country="MX",
            skills=["Python", "SQL", "Docker"],
            qualifications="Remote",
        )
    )

    item = list(spider.parse_detail(response))[0]

    assert item["titulo"] == "Desarrollador Python"
    assert item["empresa"] == "KODE IT"
    assert "Requisitos" in item["descripcion"]
    assert item["tags_tecnologias"] == ["Python", "SQL", "Docker"]
    assert item["requirements"] == []
    assert item["benefits"] == []


def test_fallback_css_sin_microdata():
    spider = make_spider()
    response = make_response(make_css_only_html())

    item = list(spider.parse_detail(response))[0]

    assert item["titulo"] == "Desarrollador Backend"
    assert item["empresa"] == "ACME"
    assert "Vacante remota" in item["descripcion"]
    assert item["modalidad_raw"] == "Remoto"


def test_empresa_confidencial_sin_datos():
    spider = make_spider()
    response = make_response(make_detail_html(company=None))

    item = list(spider.parse_detail(response))[0]

    assert item["empresa"] == "Empresa confidencial"


def test_url_oferta_sin_fragmento_ni_query():
    spider = make_spider()
    response = make_response(
        make_detail_html(location_type="TELECOMMUTE", applicant_countries=["Mexico"]),
        url=f"{DETAIL_URL}?utm_source=test#apply",
    )

    item = list(spider.parse_detail(response))[0]

    assert item["url_oferta"] == DETAIL_URL
    assert "#" not in item["url_oferta"]
    assert "?" not in item["url_oferta"]


def test_url_oferta_quita_puerto_interno():
    spider = make_spider()
    response = make_response(
        make_detail_html(location_type="TELECOMMUTE"),
        url=(
            "https://www.getonbrd.com:2053/jobs/programming/"
            "desarrollador-fullstack?ref=test#apply"
        ),
    )

    item = list(spider.parse_detail(response))[0]

    assert item["url_oferta"] == (
        "https://www.getonbrd.com/jobs/programming/desarrollador-fullstack"
    )


def test_end_to_end_url_canonica_y_modalidad_remoto():
    spider = make_spider()
    response = make_response(
        make_detail_html(
            description="English required. Python and SQL.",
            location_type="TELECOMMUTE",
            applicant_countries=["Mexico"],
        ),
        url=f"{DETAIL_URL}?ref=test#lc=apply",
    )

    item = list(spider.parse_detail(response))[0]
    cleaned = DataCleaningPipeline().process_item(item, DummySpider())
    enriched = JobEnrichmentPipeline().process_item(cleaned, DummySpider())

    assert enriched["modalidad"] == "Remoto"
    assert enriched["nivel_ingles"] == "B1"
    assert enriched["url_oferta"] == DETAIL_URL
    assert "#" not in enriched["url_oferta"]
    assert "?" not in enriched["url_oferta"]


# --- listado y paginación ---------------------------------------------------


CARD_TEMPLATE = """
<a class="results-item" href="{href}">
    <h4 class="results-list-title"><strong>{title}</strong></h4>
</a>
"""


def make_listing(*cards):
    body = "".join(CARD_TEMPLATE.format(**card) for card in cards)
    return f"<html><body>{body}</body></html>"


def test_start_requests_delega_en_query_builder():
    spider = make_spider(stack=["Python"], experiencia_anos=2)

    requests = list(spider.start_requests())

    assert [r.url for r in requests] == [LISTING_URL]
    assert all(r.callback == spider.parse for r in requests)
    assert all(r.meta["page"] == 1 for r in requests)
    assert all(r.meta["base_url"] == LISTING_URL for r in requests)


def test_parse_extrae_cards_aplica_filtro_y_pagina():
    spider = make_spider(experiencia_anos=2)
    html = make_listing(
        {
            "href": "/empleos/desarrollo-de-software/desarrollador-python",
            "title": "Desarrollador Python",
        },
        {
            "href": "/empleos/desarrollo-de-software/desarrollador-python-senior",
            "title": "Desarrollador Senior Python",
        },
        {
            "href": "/empleos/desarrollo-de-software/practicante-python",
            "title": "Practicante Python",
        },
    )
    response = make_response(
        html, url=LISTING_URL, meta={"page": 1, "base_url": LISTING_URL}
    )

    requests = list(spider.parse(response))
    detail_requests = [r for r in requests if r.callback == spider.parse_detail]
    page_requests = [r for r in requests if "page=" in r.url]

    assert [r.url for r in detail_requests] == [DETAIL_URL]
    assert len(page_requests) == 1
    assert page_requests[0].url == f"{LISTING_URL}?page=2"


def test_parse_respeta_max_pages():
    spider = make_spider()
    html = make_listing(
        {
            "href": "/empleos/desarrollo-de-software/desarrollador-python",
            "title": "Desarrollador Python",
        }
    )
    response = make_response(
        html,
        url=LISTING_URL,
        meta={"page": spider.max_pages, "base_url": LISTING_URL},
    )

    requests = list(spider.parse(response))

    assert not [r for r in requests if "page=" in r.url]


def test_parse_normaliza_enlaces_con_puerto_interno():
    spider = make_spider()
    html = make_listing(
        {
            "href": (
                "https://www.getonbrd.com:2053/jobs/programming/"
                "desarrollador-fullstack"
            ),
            "title": "Desarrollador Fullstack",
        }
    )
    response = make_response(
        html, url=LISTING_URL, meta={"page": 1, "base_url": LISTING_URL}
    )

    requests = list(spider.parse(response))
    detail_requests = [r for r in requests if r.callback == spider.parse_detail]

    assert [r.url for r in detail_requests] == [
        "https://www.getonbrd.com/jobs/programming/desarrollador-fullstack"
    ]


def test_parse_deduplica_empleos_y_jobs_y_detiene_paginacion_sin_fichas_nuevas():
    spider = make_spider()
    html = make_listing(
        {
            "href": "/empleos/desarrollo-de-software/desarrollador-python",
            "title": "Desarrollador Python",
        },
        {
            "href": "/jobs/desarrollo-de-software/desarrollador-python",
            "title": "Desarrollador Python",
        },
    )
    first_page = make_response(
        html, url=LISTING_URL, meta={"page": 1, "base_url": LISTING_URL}
    )

    first_requests = list(spider.parse(first_page))
    detail_requests = [r for r in first_requests if r.callback == spider.parse_detail]
    assert [r.url for r in detail_requests] == [DETAIL_URL]

    second_page = make_response(
        html, url=f"{LISTING_URL}?page=2", meta={"page": 2, "base_url": LISTING_URL}
    )

    # La segunda página repite las mismas fichas: no hay peticiones nuevas.
    assert list(spider.parse(second_page)) == []
