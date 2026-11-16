import json

from scrapy.http import HtmlResponse, Request

from job_scraper.spiders.occ_spider import OccSpider
from job_scraper.utils.query_builder import SearchQueryBuilder


def make_response(html, url="https://www.occ.com.mx/empleo/oferta/123456", meta=None):
    request = Request(url, meta=meta or {}) if meta else None
    return HtmlResponse(url=url, body=html.encode("utf-8"), encoding="utf-8", request=request)


def make_spider():
    indicator_rows = [{"stack": [], "experiencia_anos": 2}]
    spider = OccSpider()
    spider.query_builder = SearchQueryBuilder(rows=indicator_rows)
    return spider


def make_json_ld_html(payload, extra=""):
    # OCC publica el JSON-LD con claves capitalizadas y un `;` final.
    script = json.dumps(payload, ensure_ascii=False) + ";"
    return (
        "<html><head>"
        f'<script type="application/ld+json">{script}</script>'
        "</head><body>"
        f"{extra}"
        "</body></html>"
    )


JOB_POSTING = {
    "@context": "https://schema.org",
    "@type": "JobPosting",
    "Title": "Desarrollador Python",
    "Description": "<p>Buscamos desarrollador con 2 años de experiencia en Python.</p>"
    "<ul><li>Python</li><li>SQL</li></ul>",
    "HiringOrganization": {"Name": "ACME Tecnologías"},
    "JobLocationType": "TELECOMMUTE",
    "JobLocation": {
        "Address": {
            "AddressLocality": "Ciudad de México",
            "AddressRegion": "CDMX",
            "AddressCountry": "MX",
        }
    },
}


def test_parse_detail_extrae_desde_json_ld():
    spider = make_spider()
    response = make_response(
        make_json_ld_html(JOB_POSTING),
        url="https://www.occ.com.mx/empleo/oferta/123456?utm_source=test",
    )

    items = list(spider.parse_detail(response))

    assert len(items) == 1
    item = items[0]
    assert item["titulo"] == "Desarrollador Python"
    assert item["empresa"] == "ACME Tecnologías"
    assert "2 años de experiencia" in item["descripcion"]
    assert item["modalidad_raw"] == "TELECOMMUTE"
    assert "Ciudad de México" in item["ubicacion_texto"]
    assert item["url_oferta"] == "https://www.occ.com.mx/empleo/oferta/123456"


def test_parse_detail_usa_fallback_css_sin_json_ld():
    spider = make_spider()
    html = (
        "<html><head>"
        '<meta name="description" content="Ofertas de trabajo de Desarrollador Java. '
        'ACME SA de CV - Guadalajara, Jalisco. Descubre más ofertas." />'
        "</head><body>"
        "<h1>Desarrollador Java</h1>"
        '<div class="rich-text"><p>Requisitos: 3 años de experiencia con Java.</p></div>'
        "<p>Espacio de trabajo</p>"
        '<a href="/empleos/tipo-home-office-mixto/">Mixto</a>'
        "</body></html>"
    )

    items = list(spider.parse_detail(make_response(html)))
    item = items[0]

    assert item["titulo"] == "Desarrollador Java"
    assert item["empresa"] == "ACME SA de CV"
    assert "3 años de experiencia" in item["descripcion"]
    assert item["modalidad_raw"] == "Híbrido"
    assert item["ubicacion_texto"] == "Guadalajara, Jalisco"


def test_parse_detail_empresa_confidencial_sin_datos():
    spider = make_spider()
    html = "<html><body><h1>Vacante Genérica</h1></body></html>"

    item = list(spider.parse_detail(make_response(html)))[0]

    assert item["titulo"] == "Vacante Genérica"
    assert item["empresa"] == "Empresa confidencial"


def test_parse_extrae_cards_y_pagina():
    spider = make_spider()
    html = (
        "<html><body><ul>"
        '<li class="vacancy-card" data-id="98765">'
        '<h2 class="vacancy-title">Desarrollador Python</h2>'
        "</li>"
        '<li class="vacancy-card" data-id="98766">'
        '<h2 class="vacancy-title">Analista de datos</h2>'
        "</li>"
        "</ul></body></html>"
    )
    base_url = "https://www.occ.com.mx/empleos/de-python/"
    response = make_response(html, url=base_url, meta={"page": 1, "base_url": base_url})

    requests = list(spider.parse(response))
    detail_requests = [r for r in requests if "empleo/oferta" in r.url]
    page_requests = [r for r in requests if "page=" in r.url]

    assert [r.url for r in detail_requests] == [
        "https://www.occ.com.mx/empleo/oferta/98765",
        "https://www.occ.com.mx/empleo/oferta/98766",
    ]
    assert len(page_requests) == 1
    assert page_requests[0].url == "https://www.occ.com.mx/empleos/de-python/?page=2"


def test_parse_respeta_max_pages():
    spider = make_spider()
    html = (
        "<html><body>"
        '<li class="vacancy-card" data-id="1"><h2>Desarrollador Python</h2></li>'
        "</body></html>"
    )
    base_url = "https://www.occ.com.mx/empleos/de-python/"
    response = make_response(
        html, url=base_url, meta={"page": spider.max_pages, "base_url": base_url}
    )

    requests = list(spider.parse(response))

    assert not [r for r in requests if "page=" in r.url]
