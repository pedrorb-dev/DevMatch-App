import json

from scrapy.http import HtmlResponse, Request

from job_scraper.pipelines import DataCleaningPipeline, JobEnrichmentPipeline
from job_scraper.spiders.computrabajo_spider import ComputrabajoSpider
from job_scraper.utils.query_builder import SearchQueryBuilder


DETAIL_URL = (
    "https://mx.computrabajo.com/ofertas-de-trabajo/"
    "oferta-de-trabajo-de-desarrollador-python-1111111111111111"
)


class DummySpider:
    name = "computrabajo"
    logger = None


def make_response(html, url=DETAIL_URL, meta=None):
    request = Request(url, meta=meta or {})
    return HtmlResponse(url=url, body=html.encode("utf-8"), encoding="utf-8", request=request)


def make_spider(stack=None, experiencia_anos=2):
    rows = [{"stack": stack if stack is not None else ["Python"], "experiencia_anos": experiencia_anos}]
    spider = ComputrabajoSpider()
    spider.query_builder = SearchQueryBuilder(rows=rows)
    return spider


def make_json_ld_html(payload, extra=""):
    # Computrabajo publica un array JSON-LD con el `JobPosting` entre otros nodos.
    script = json.dumps(payload, ensure_ascii=False)
    return (
        "<html><head>"
        f'<script type="application/ld+json">{script}</script>'
        "</head><body>"
        f"{extra}"
        "</body></html>"
    )


JOB_POSTING = {
    "@context": "https://schema.org/",
    "@type": "JobPosting",
    "title": "Desarrollador Python",
    "description": (
        "Buscamos desarrollador Python con 2 años de experiencia."
        "<br/><br/>Requerimientos<br/>Python<br/>SQL"
    ),
    "employmentType": "FULL_TIME",
    "url": DETAIL_URL,
    "jobLocation": {
        "@type": "Place",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Ciudad de México DF",
            "addressRegion": "Benito Juárez",
            "addressCountry": "México",
        },
    },
    "hiringOrganization": {"@type": "Organization", "name": "KODE IT"},
}


def test_parse_detail_extrae_desde_json_ld():
    spider = make_spider()
    response = make_response(
        make_json_ld_html([JOB_POSTING]),
        url=f"{DETAIL_URL}?utm_source=test#lc=ListOffers-Score4-0",
        meta={"modalidad_raw": "Desde casa"},
    )

    items = list(spider.parse_detail(response))

    assert len(items) == 1
    item = items[0]
    assert item["titulo"] == "Desarrollador Python"
    assert item["empresa"] == "KODE IT"
    assert "2 años de experiencia" in item["descripcion"]
    assert "Requerimientos" in item["descripcion"]
    assert item["ubicacion_texto"] == "Benito Juárez, Ciudad de México DF, México"
    assert item["modalidad_raw"] == "Desde casa"
    assert item["url_oferta"] == DETAIL_URL


def test_parse_detail_usa_fallback_css_sin_json_ld():
    spider = make_spider()
    html = (
        "<html><body>"
        '<h1 class="fwB fs24 mb5 box_detail w100_m">Desarrollador Java</h1>'
        '<p class="fs16">ACME SA de CV - Guadalajara, Jalisco</p>'
        '<div class="mb40 pb40 bb1" div-link="oferta">'
        '<p class="mbB">Requisitos: 3 años de experiencia con Java.</p>'
        "</div>"
        '<span class="dIB mr10"><span class="icon i_home_office"></span>Híbrido</span>'
        "</body></html>"
    )

    item = list(spider.parse_detail(make_response(html)))[0]

    assert item["titulo"] == "Desarrollador Java"
    assert item["empresa"] == "ACME SA de CV"
    assert item["ubicacion_texto"] == "Guadalajara, Jalisco"
    assert "3 años de experiencia" in item["descripcion"]
    assert item["modalidad_raw"] == "Híbrido"


def test_parse_detail_empresa_confidencial_sin_datos():
    spider = make_spider()
    html = "<html><body><h1>Vacante Genérica</h1></body></html>"

    item = list(spider.parse_detail(make_response(html)))[0]

    assert item["titulo"] == "Vacante Genérica"
    assert item["empresa"] == "Empresa confidencial"


def test_parse_detail_normaliza_importante_empresa_del_sector():
    spider = make_spider()
    payload = dict(JOB_POSTING)
    payload["hiringOrganization"] = {
        "@type": "Organization",
        "name": "Importante empresa del sector",
    }

    item = list(spider.parse_detail(make_response(make_json_ld_html([payload]))))[0]

    assert item["empresa"] == "Empresa confidencial"


def test_parse_detail_normaliza_empresa_confidencial_en_cabecera():
    spider = make_spider()
    html = (
        "<html><body>"
        '<h1 class="box_detail">Desarrollador Python</h1>'
        '<p class="fs16">Confidencial - Remoto</p>'
        "</body></html>"
    )

    item = list(spider.parse_detail(make_response(html)))[0]

    assert item["empresa"] == "Empresa confidencial"


CARD_TEMPLATE = """
<article class="box_offer" data-id="{offer_id}" data-offers-grid-offer-item-container>
    <h2 class="fs18 fwB prB">
        <a class="js-o-link fc_base"
           href="/ofertas-de-trabajo/oferta-de-trabajo-de-{slug}-{offer_id}#lc=ListOffers-Score4-0">
            {title}
        </a>
    </h2>
    <p class="dFlex vm_fx fs16 fc_base mt5">
        <a class="fc_base t_ellipsis"
           href="https://mx.computrabajo.com/empresas/ofertas-de-trabajo-de-acme"
           offer-grid-article-company-url>ACME</a>
    </p>
    <p class="fs16 fc_base mt5"><span class="mr10">Cuauhtémoc, Ciudad de México DF</span></p>
    <div class="fs13 mt15">
        <span class="dIB mr10"><span class="icon i_home_office"></span>{modalidad}</span>
    </div>
</article>
"""


def make_listing(*cards):
    body = "".join(CARD_TEMPLATE.format(**card) for card in cards)
    return f"<html><body>{body}</body></html>"


def test_parse_extrae_cards_aplica_filtro_y_pagina():
    spider = make_spider(experiencia_anos=2)
    html = make_listing(
        {
            "offer_id": "111",
            "slug": "desarrollador-python",
            "title": "Desarrollador Python",
            "modalidad": "Desde casa",
        },
        {
            "offer_id": "222",
            "slug": "senior-python",
            "title": "Ingeniero Senior Python",
            "modalidad": "Presencial",
        },
    )
    base_url = "https://mx.computrabajo.com/trabajo-de-python"
    response = make_response(html, url=base_url, meta={"page": 1, "base_url": base_url})

    requests = list(spider.parse(response))
    detail_requests = [r for r in requests if r.callback == spider.parse_detail]
    page_requests = [r for r in requests if "p=" in r.url]

    assert [r.url for r in detail_requests] == [
        "https://mx.computrabajo.com/ofertas-de-trabajo/"
        "oferta-de-trabajo-de-desarrollador-python-111"
    ]
    assert detail_requests[0].meta["modalidad_raw"] == "Desde casa"
    assert len(page_requests) == 1
    assert page_requests[0].url == "https://mx.computrabajo.com/trabajo-de-python?p=2"


def test_parse_respeta_max_pages():
    spider = make_spider()
    html = make_listing(
        {
            "offer_id": "333",
            "slug": "desarrollador-python",
            "title": "Desarrollador Python",
            "modalidad": "Híbrido",
        }
    )
    base_url = "https://mx.computrabajo.com/trabajo-de-python"
    response = make_response(
        html, url=base_url, meta={"page": spider.max_pages, "base_url": base_url}
    )

    requests = list(spider.parse(response))

    assert not [r for r in requests if "p=" in r.url]


def test_start_requests_delega_en_query_builder():
    spider = make_spider(stack=["Python"], experiencia_anos=2)

    requests = list(spider.start_requests())

    assert [r.url for r in requests] == [
        "https://mx.computrabajo.com/trabajo-de-python",
        "https://mx.computrabajo.com/trabajo-de-desarrollador-python",
    ]
    assert all(r.callback == spider.parse for r in requests)
    assert all(r.meta["page"] == 1 for r in requests)


def test_end_to_end_desde_casa_es_remoto_y_url_canonica():
    spider = make_spider()
    response = make_response(
        make_json_ld_html([JOB_POSTING]),
        url=f"{DETAIL_URL}?ref=test#lc=ListOffers-Score4-0",
        meta={"modalidad_raw": "Desde casa"},
    )

    item = list(spider.parse_detail(response))[0]
    cleaned = DataCleaningPipeline().process_item(item, DummySpider())
    enriched = JobEnrichmentPipeline().process_item(cleaned, DummySpider())

    assert enriched["modalidad"] == "Remoto"
    assert enriched["url_oferta"] == DETAIL_URL
    assert "#" not in enriched["url_oferta"]
    assert "?" not in enriched["url_oferta"]
