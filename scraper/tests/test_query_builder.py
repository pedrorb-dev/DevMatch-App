import pytest

from job_scraper.utils.query_builder import SearchQueryBuilder, should_follow_job


def make_builder(rows):
    return SearchQueryBuilder(rows=rows)


# --- generación de URLs ----------------------------------------------------


def test_build_urls_hireline_perfil_cero_anos():
    builder = make_builder([{"stack": ["Java", "Python"], "experiencia_anos": 0}])

    assert builder.build_urls("hireline") == [
        "https://hireline.io/mx/empleos-de-trainee",
        "https://hireline.io/mx/empleos-de-becario-ti",
        "https://hireline.io/mx/empleos?k=Java",
        "https://hireline.io/mx/empleos?k=Python",
    ]


def test_build_urls_occ_perfil_cero_anos():
    builder = make_builder([{"stack": ["Java", "Python"], "experiencia_anos": 0}])

    assert builder.build_urls("occ") == [
        "https://www.occ.com.mx/empleos/de-practicante/",
        "https://www.occ.com.mx/empleos/de-java/",
        "https://www.occ.com.mx/empleos/de-python/",
    ]


def test_build_urls_hireline_perfil_dos_anos():
    builder = make_builder([{"stack": ["Java", "Python"], "experiencia_anos": 2}])

    assert builder.build_urls("hireline") == [
        "https://hireline.io/mx/empleos-de-desarrollador-junior",
        "https://hireline.io/mx/empleos?k=Java",
        "https://hireline.io/mx/empleos?k=Python",
    ]


def test_build_urls_occ_perfil_dos_anos():
    builder = make_builder([{"stack": ["Java", "Python"], "experiencia_anos": 2}])

    # Sin perfiles de 0 años no se busca la ruta de practicante.
    assert builder.build_urls("occ") == [
        "https://www.occ.com.mx/empleos/de-java/",
        "https://www.occ.com.mx/empleos/de-python/",
    ]


def test_build_urls_hireline_perfil_cinco_anos():
    builder = make_builder([{"stack": ["Java", "Python"], "experiencia_anos": 5}])

    assert builder.build_urls("hireline") == [
        "https://hireline.io/mx/empleos-de-senior",
        "https://hireline.io/mx/empleos?k=Java",
        "https://hireline.io/mx/empleos?k=Python",
    ]


def test_build_urls_occ_perfil_cinco_anos():
    builder = make_builder([{"stack": ["Java", "Python"], "experiencia_anos": 5}])

    assert builder.build_urls("occ") == [
        "https://www.occ.com.mx/empleos/de-java/",
        "https://www.occ.com.mx/empleos/de-python/",
    ]


def test_build_urls_combina_todos_los_perfiles():
    builder = make_builder(
        [
            {"stack": ["Java"], "experiencia_anos": 0},
            {"stack": ["Python"], "experiencia_anos": 2},
            {"stack": ["Java", "SQL"], "experiencia_anos": 5},
        ]
    )

    hireline_urls = builder.build_urls("hireline")
    assert "https://hireline.io/mx/empleos-de-trainee" in hireline_urls
    assert "https://hireline.io/mx/empleos-de-becario-ti" in hireline_urls
    assert "https://hireline.io/mx/empleos-de-desarrollador-junior" in hireline_urls
    assert "https://hireline.io/mx/empleos-de-senior" in hireline_urls
    assert "https://hireline.io/mx/empleos?k=Java" in hireline_urls
    assert "https://hireline.io/mx/empleos?k=Python" in hireline_urls
    assert "https://hireline.io/mx/empleos?k=SQL" in hireline_urls
    # stack único, sin repetir la tecnología compartida
    assert hireline_urls.count("https://hireline.io/mx/empleos?k=Java") == 1

    occ_urls = builder.build_urls("occ")
    assert "https://www.occ.com.mx/empleos/de-practicante/" in occ_urls
    assert occ_urls.count("https://www.occ.com.mx/empleos/de-java/") == 1


def test_build_urls_sin_perfiles_usa_rutas_de_entrada():
    builder = make_builder([])

    assert builder.build_urls("hireline") == [
        "https://hireline.io/mx/empleos-de-trainee",
        "https://hireline.io/mx/empleos-de-becario-ti",
    ]
    assert builder.build_urls("occ") == [
        "https://www.occ.com.mx/empleos/de-practicante/",
    ]


def test_build_urls_sin_stack_no_genera_busquedas_de_tecnologia():
    builder = make_builder([{"stack": [], "experiencia_anos": 2}])

    assert builder.build_urls("hireline") == [
        "https://hireline.io/mx/empleos-de-trainee",
        "https://hireline.io/mx/empleos-de-becario-ti",
        "https://hireline.io/mx/empleos-de-desarrollador-junior",
    ]
    assert builder.build_urls("occ") == [
        "https://www.occ.com.mx/empleos/de-practicante/",
    ]


def test_build_urls_acepta_stack_como_string():
    builder = make_builder([{"stack": "Spring Boot", "experiencia_anos": 2}])

    assert builder.build_urls("hireline") == [
        "https://hireline.io/mx/empleos-de-desarrollador-junior",
        "https://hireline.io/mx/empleos?k=Spring+Boot",
    ]
    assert builder.build_urls("occ") == [
        "https://www.occ.com.mx/empleos/de-spring-boot/",
    ]


@pytest.mark.parametrize(
    ("stack", "occ_url"),
    [
        ("C#", "https://www.occ.com.mx/empleos/de-c-sharp/"),
        (".NET", "https://www.occ.com.mx/empleos/de-dotnet/"),
        ("Node.js", "https://www.occ.com.mx/empleos/de-node-js/"),
        ("React", "https://www.occ.com.mx/empleos/de-react/"),
        ("Rust", "https://www.occ.com.mx/empleos/de-rust/"),
        ("Ruby on Rails", "https://www.occ.com.mx/empleos/de-ruby-on-rails/"),
    ],
)
def test_build_urls_occ_slugs(stack, occ_url):
    builder = make_builder([{"stack": [stack], "experiencia_anos": 2}])

    assert occ_url in builder.build_urls("occ")


def test_build_urls_rechaza_plataforma_desconocida():
    builder = make_builder([{"stack": ["Java"], "experiencia_anos": 2}])

    with pytest.raises(ValueError):
        builder.build_urls("linkedin")


def test_perfil_se_cachea_entre_llamadas():
    rows = [{"stack": ["Java"], "experiencia_anos": 2}]
    builder = make_builder(rows)

    first = builder.build_urls("hireline")
    rows.append({"stack": ["Python"], "experiencia_anos": 2})

    assert builder.build_urls("hireline") == first


# --- should_follow_job -----------------------------------------------------


@pytest.mark.parametrize(
    "title",
    [
        "Becario de TI",
        "Becaria de desarrollo",
        "Practicante de desarrollo",
        "Estadías en TI",
        "Estadias en TI",
        "Software Engineer Intern",
        "Trainee Developer",
        "Desarrollador sin experiencia",
        "Developer (no experience required)",
    ],
)
def test_should_follow_job_descarta_entrada_sin_perfiles_de_cero(title):
    assert should_follow_job(title, [2]) is False
    assert should_follow_job(title, [5]) is False


@pytest.mark.parametrize(
    "title",
    [
        "Senior Java Developer",
        "Sr. Backend Developer",
        "Lead Software Engineer",
        "Software Architect",
        "Engineering Manager",
    ],
)
def test_should_follow_job_descarta_senior_sin_perfiles_senior(title):
    assert should_follow_job(title, [0]) is False
    assert should_follow_job(title, [2]) is False


@pytest.mark.parametrize(
    "title",
    ["Desarrollador Java", "Analista de datos", "Frontend Developer"],
)
def test_should_follow_job_acepta_titulos_neutros(title):
    assert should_follow_job(title, [0]) is True
    assert should_follow_job(title, [2]) is True
    assert should_follow_job(title, [5]) is True


def test_should_follow_job_acepta_entrada_y_senior_cuando_hay_perfiles():
    assert should_follow_job("Becario de TI", [0, 2]) is True
    assert should_follow_job("Senior Java Developer", [2, 5]) is True
    assert should_follow_job("Practicante de desarrollo", [0]) is True
    assert should_follow_job("Software Architect", [5]) is True


def test_should_follow_job_sin_perfiles_no_descarta_nada():
    assert should_follow_job("Becario de TI", []) is True
    assert should_follow_job("Senior Java Developer", []) is True
    assert should_follow_job("Trainee Developer", None) is True


def test_should_follow_job_titulo_vacio_no_descarta():
    assert should_follow_job("", [2]) is True
    assert should_follow_job(None, [2]) is True


def test_query_builder_delega_should_follow_job():
    builder = make_builder([{"stack": ["Java"], "experiencia_anos": 2}])

    assert builder.should_follow_job("Desarrollador Java") is True
    assert builder.should_follow_job("Becario de TI") is False
    assert builder.should_follow_job("Senior Java Developer") is False
