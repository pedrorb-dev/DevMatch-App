import pytest

from job_scraper.utils.sectionizer import classify_heading, split_sections


COCOON = """Cocoon connects property intelligence, homeowner engagement and service fulfillment to help homeowners better maintain and protect their homes while enabling insurance carriers and other partners to move from identifying property risk to addressing and verifying risk mitigation. To take the next step in growing our business, we are seeking an exceptional Principal Engineer who will inherit our fully functional platform. We are looking for someone who wants to become a long-term member of Cocoon's core team, participate meaningfully in the company's success. You will understand that system deeply, determine what should be preserved, identify what should be improved and lead the evolution of the platform's technical foundation in line with product and business strategy. Serving as Cocoon's primary internal technical authority and source of technical truth, you will own technical architecture and engineering decisions in alignment with the company's product and business priorities. Este empleo es original de Get on Board. Core Responsibilities Technical Architecture & Leadership Serve as Cocoon's primary internal authority on backend architecture, data architecture, system design and engineering quality. Own technical architecture and engineering decisions. Spearhead Cocoon's efforts to integrate AI-driven capabilities into its products, platform and engineering workflows. Hands-On Backend Engineering Remain deeply hands-on in Cocoon's codebase and personally develop production software. Enter an established codebase, understand it quickly and determine what should be retained, refactored or replaced. Help shape product ideas and requirements alongside Cocoon team members before specifications are finalized. Data Architecture Lead evolution of Cocoon's existing data architecture into a sophisticated relational domain model. Define schemas, relationships, data-access patterns and integrity standards. Develop safe migration strategies for evolving an active production database. Account for both structured and unstructured information as Cocoon's AI capabilities expand. Build a data foundation capable of supporting substantially greater intelligence, automation and scale over time. AI-Native Engineering Be AI-native in how you work, actively using AI development tools to improve engineering speed and quality. Infrastructure & DevOps Oversight Ensure infrastructure decisions remain aligned with Cocoon's application architecture. Maintain appropriate visibility into security, reliability, deployment architecture, performance & cost. Provide technical direction and oversight to Cocoon's outsourced AWS/DevOps engineer. Enterprise & Partner Technical Leadership As required, represent Cocoon in technical discussions with insurance carriers, technology partners and other external stakeholders. What We Are Looking For Exceptional Backend Engineering & Architectural Judgment — 8+ years of professional backend engineering experience at a Senior/Staff/Principal/Architect level, with exceptional hands-on development capability and significant production Java experience. Experience with Spring Boot, Spring Security and Hibernate/JPA strongly preferred. Deep Relational Data Architecture Expertise — Proven ownership of complex production relational data models at real scale. Strong System Design & API Architecture Capability — Demonstrated ability to design sophisticated production systems and REST APIs, understand distributed-system tradeoffs, with real experience improving an already-established codebase, not only building greenfield. Strong PostgreSQL experience (Cocoon currently uses Aurora PostgreSQL). AI-Native Engineering Capability — Demonstrated ability to use modern AI-assisted development tools to materially improve engineering productivity and quality, while applying the technical judgment needed to critically evaluate AI-generated work. Production Engineering Discipline — Strong understanding of application security, automated testing, observability, reliability, performance and maintainability. Builds systems designed to operate reliably in production, not simply function in development. Technical Leadership & Independent Judgment — Experience directing senior engineers and serving as a trusted technical authority. Comfortable making consequential decisions with incomplete information, surfacing risks early, challenging assumptions, and recommending a clear path forward. Production Applied-AI Experience (Highly Preferred) — Meaningful hands-on experience implementing and operating production AI, LLM, agentic, multimodal, or computer-vision capabilities, including architecture, evaluation, retrieval, reliability, and production operations Strong Cloud & Production Infrastructure Fluency — Experience with AWS-hosted production systems (EC2, S3, RDS/Aurora, IAM, VPC networking), containers, CI/CD and modern cloud deployment architecture. How You Work Owner's Mindset, Professional Maturity & Communication Operates like an owner, not a ticket-taker. Takes responsibility for outcomes, moves quickly without sacrificing quality, disagrees productively, communicates clearly, and credibly represents Cocoon with technical and nontechnical stakeholders. Genuine Engineering Craft Still loves building software and is comfortable operating without a large engineering organization around them. Thrives in a Startup Environment Acts independently while collaborating effectively within a small team. Knows how to get things done and works quickly without requiring a high degree of oversight. Why Join Cocoon Meaningful equity options and participation in the company's long-term success Direct working relationship with Cocoon's Founder & CEO Genuine ownership of Cocoon's technical architecture and engineering direction Opportunity to remain deeply hands-on while operating at the highest technical level in the company Small, senior team with substantial individual autonomy and impact Fully remote working environment Opportunity to shape how AI is embedded into both Cocoon's products and engineering organization Compensation: Competitive compensation + equity options GETONBRD Job ID: 63780 Se ofrece equity en la empresa Este cargo incluye participación accionaria (stock options o similar) como parte de la compensación. Ausencia por enfermedad pagada Se ofrece cobertura por días no trabajados a causa de enfermedad (pueden aplicar límites). Vestimenta informal Cocoon no exige ningún código de vestimenta. Vacaciones extra Cocoon otorga vacaciones pagadas adicionales al mínimo legal. Política de trabajo remoto Remoto sólo localmente El trabajo es 100% remoto, pero los candidatos deben residir en Sudamérica y Centroamérica para postular."""

HIRELINE_ISITA = """Requerido:- 5+ años de experiencia en desarrollo de soluciones escalables con .NET.- 3+ años de experiencia en desarrollo frontend con React.Experiencia en Sistemas Financieros- Diseño, creación e implementación de APIs empresariales con .NET.- Desarrollo desde cero de componentes y formularios complejos con React.- Aplicación de Clean Architecture, principios SOLID y manejo de arquitecturas orientadas a eventos.- Creación de consultas, índices y funciones en PostgreSQL.- Implementación de pipelines de CI/CD en Azure DevOps.- Participación en decisiones técnicas de diseño y arquitectura.Conocimientos de:- Backend: .NET (6 o mayor), ASP.NET Core Web API, EF Core o Dapper, JWT/OAuth2.- Frontend: React (16 o mayor), Typescript (avanzado).- PWA: Service workers, caché, funcionamiento offline y notificaciones push.- Base de datos: PostgreSQL (1+ años).- DevOps: Azure DevOps (3+ años).Habilidades:- Comunicación efectiva con equipos técnicos y de negocio.- Manejo de metodologías ágiles (Scrum/Kanban), refinamientos y ceremonias.- Inglés intermedio.Deseable:- Liderazgo técnico y mentoring de otros desarrolladores.- Experiencia en Next.js, SQL Server y Docker/Docker Compose.RequerimientosEducación mínima: Educación superior - Licenciatura4 años de experienciaIdiomas: InglésConocimientos: .net, Azure devops, React, Typescript AWS NodeJs Apis Rest .NetCore"""

WE_BUILT_IT = """We Built It is supporting digital business growth across Latin America with a tech-first foundation and delivery across multiple solution pillars. In this role, we’re looking for a Data Layer Developer to help our teams implement and maintain scalable, event-driven data layer solutions that enable reliable digital analytics and tracking. You will work closely with analytics and development stakeholders to ensure our tracking implementations are consistent, well-structured, and maintainable—especially in SPA environments—so that data accuracy and observability remain strong across a wide variety of digital projects and initiatives. Oferta exclusiva de getonbrd.com. Responsibilities Develop and maintain event-driven data layers Implement custom JavaScript events and tracking Build structured JSON payloads for analytics Collaborate with analytics and development teams Debug and validate tracking implementations Maintain documentation and tracking standards Support SPA tracking implementations Required Skills We are looking for a Data Layer Developer with strong, practical JavaScript skills and hands-on experience implementing event-driven analytics tracking. Strong JavaScript (ES6+) knowledge HTML5 and DOM manipulation JSON and nested object handling Understanding of event-driven architecture Ability to implement custom events and event listeners Comfort using browser developer tools to debug and validate behavior Experience with Adobe Client Data Layer (ACDL) Experience with data mapping and payload validation We also value clear communication, attention to detail, and ownership of quality. You should be able to validate tracking against expectations, keep implementations aligned with documentation and standards, and collaborate effectively with analytics and engineering teammates. Preferred Skills Experience with analytics implementations SPA frameworks like React.js or Angular Knowledge of Adobe Analytics or tag management systems Benefits 100% remote work environment Collaborative and supportive international team culture Fun and engaging team environment with strong camaraderie Exposure to a wide variety of digital projects and initiatives Birthday day off Opportunity to work within a highly dynamic retail digital ecosystem Continuous collaboration with experienced Scrum Masters and multidisciplinary teams GETONBRD Job ID: 63213 Trabajo 100% remoto El cargo puede ser desempeñado desde cualquier lugar del mundo. Horario flexible Entrada y salida flexibles, libertad para realizar trámites personales o familiares. Vacaciones extra We Built It otorga vacaciones pagadas adicionales al mínimo legal. Política de trabajo remoto Totalmente remoto El trabajo es 100% remoto desde cualquier país."""


# --- casos reales ---------------------------------------------------------


def test_caso_real_cocoon():
    result = split_sections(COCOON)

    assert any("Exceptional Backend Engineering" in r for r in result["requirements"])
    assert any("8+ years" in r for r in result["requirements"])
    assert any("PostgreSQL" in r for r in result["requirements"])

    assert any("Meaningful equity options" in b for b in result["benefits"])
    assert any("Competitive compensation" in b for b in result["benefits"])
    assert any("Se ofrece equity" in b for b in result["benefits"])
    assert any("Ausencia por enfermedad" in b for b in result["benefits"])
    assert any("Vestimenta informal" in b for b in result["benefits"])
    assert any("Vacaciones extra" in b for b in result["benefits"])
    assert any("Política de trabajo remoto" in b for b in result["benefits"])

    assert "Core Responsibilities" in result["descripcion"]
    assert "How You Work" in result["descripcion"]
    assert "Technical Architecture & Leadership" in result["descripcion"]
    assert "requirements alongside" in result["descripcion"]
    assert "GETONBRD Job ID" not in result["descripcion"]
    assert "Este empleo es original de Get on Board" not in result["descripcion"]


def test_caso_real_hireline_net():
    result = split_sections(HIRELINE_ISITA)

    assert any("5+ años de experiencia" in r for r in result["requirements"])
    assert any("ASP.NET Core Web API" in r for r in result["requirements"])
    assert any("Comunicación efectiva" in r for r in result["requirements"])
    assert any("Liderazgo técnico" in r for r in result["requirements"])

    assert "Experiencia en Sistemas Financieros" in result["descripcion"]
    assert "Diseño, creación e implementación de APIs" in result["descripcion"]


def test_caso_real_we_built_it():
    result = split_sections(WE_BUILT_IT)

    assert any("Strong JavaScript" in r for r in result["requirements"])
    assert any("Adobe Client Data Layer" in r for r in result["requirements"])
    assert any("Experience with analytics implementations" in r for r in result["requirements"])

    assert any("100% remote work environment" in b for b in result["benefits"])
    assert any("Birthday day off" in b for b in result["benefits"])
    assert any("Trabajo 100% remoto" in b for b in result["benefits"])
    assert any("Horario flexible" in b for b in result["benefits"])

    assert "We Built It is supporting" in result["descripcion"]
    assert "Develop and maintain event-driven data layers" in result["descripcion"]
    assert "GETONBRD Job ID" not in result["descripcion"]
    assert "Oferta exclusiva" not in result["descripcion"]


# --- casos ES / EN --------------------------------------------------------


def test_espanol_requisitos_y_ofrecemos():
    text = (
        "Buscamos un desarrollador para el equipo.\n\n"
        "Requisitos:\n"
        "- 3 años de experiencia con Python\n"
        "- Inglés intermedio\n\n"
        "Actividades:\n"
        "- Diseñar APIs\n\n"
        "Ofrecemos:\n"
        "- Seguro de gastos médicos\n"
        "- Horario flexible\n"
    )
    result = split_sections(text)

    assert result["requirements"] == ["3 años de experiencia con Python", "Inglés intermedio"]
    assert result["benefits"] == ["Seguro de gastos médicos", "Horario flexible"]
    assert "Buscamos un desarrollador" in result["descripcion"]
    assert "Diseñar APIs" in result["descripcion"]
    assert "Requisitos" not in result["descripcion"]
    assert "Ofrecemos" not in result["descripcion"]


def test_ingles_requirements_y_benefits():
    text = (
        "Build scalable solutions.\n\n"
        "What We're Looking For:\n"
        "- 5+ years of experience with C#\n"
        "- Strong SQL Server skills\n\n"
        "Responsibilities:\n"
        "- Design and maintain applications\n\n"
        "What We Offer:\n"
        "- Remote work\n"
        "- Equity options\n"
    )
    result = split_sections(text)

    assert result["requirements"] == [
        "5+ years of experience with C#",
        "Strong SQL Server skills",
    ]
    assert result["benefits"] == ["Remote work", "Equity options"]
    assert "Build scalable solutions" in result["descripcion"]
    assert "Design and maintain applications" in result["descripcion"]


@pytest.mark.parametrize(
    ("heading", "expected"),
    [
        ("Requisitos", "requirements"),
        ("CONOCIMIENTOS DESEABLES:", "requirements"),
        ("Minimum Requirements", "requirements"),
        ("Must-Have", "requirements"),
        ("Ofrecemos", "benefits"),
        ("Compensation and Benefits", "benefits"),
        ("Why Join Us", "benefits"),
        ("What you'll get", "benefits"),
        ("Actividades", "description"),
        ("Sobre la empresa", "description"),
        ("Core Responsibilities", "description"),
        ("How You Work", "description"),
        ("Experiencia en Sistemas Financieros", "description"),
        ("Texto sin encabezado", "description"),
    ],
)
def test_classify_heading_bilingue(heading, expected):
    assert classify_heading(heading) == expected


def test_vinietas_sin_encabezado_por_senales():
    text = (
        "Buscamos talento.\n"
        "- 5+ años de experiencia en Python\n"
        "- seguro de gastos médicos\n"
        "- Trabajo en equipo\n"
    )
    result = split_sections(text)

    assert result["requirements"] == ["5+ años de experiencia en Python"]
    assert result["benefits"] == ["seguro de gastos médicos"]
    assert "Buscamos talento" in result["descripcion"]
    assert "Trabajo en equipo" in result["descripcion"]


def test_prosa_corrida_sin_marcadores_no_se_divide():
    text = "Somos una empresa que desarrolla software para clientes internacionales."
    result = split_sections(text)

    assert result == {"descripcion": text, "requirements": [], "benefits": []}


def test_items_conservan_mayusculas_y_acentos():
    result = split_sections("Requisitos:\n- Inglés Avanzado\n- CONOCIMIENTOS de SQL")

    assert result["requirements"] == ["Inglés Avanzado", "CONOCIMIENTOS de SQL"]


@pytest.mark.parametrize(
    "marker",
    ["GETONBRD Job ID: 63780", "OCC Job ID: 12", "Job ID: 7"],
)
def test_variantes_de_pie_de_fuente(marker):
    result = split_sections(f"Requisitos:\n- Java\n{marker} Seguro médico. Vacaciones extra.")

    assert result["requirements"] == ["Java"]
    assert any("Seguro médico" in b for b in result["benefits"])
    assert any("Vacaciones extra" in b for b in result["benefits"])
    assert marker not in result["descripcion"]


def test_subencabezado_no_parte_seccion():
    text = (
        "Core Responsibilities\n"
        "Technical Architecture & Leadership\n"
        "- Own the platform\n\n"
        "What We Are Looking For\n"
        "- 8+ years of experience\n"
    )
    result = split_sections(text)

    assert "Technical Architecture & Leadership" in result["descripcion"]
    assert result["requirements"] == ["8+ years of experience"]


def test_encabezados_concatenados_sin_separador():
    # Texto almacenado tras colapsar saltos de línea (caso ALPRO real).
    text = (
        "Sobre nosotrosALPRO es una plataforma SaaS B2B. "
        "ResponsabilidadesDesarrollar APIs y corregir bugs. "
        "Requisitos (must)3+ años con React. "
        "DeseableAWS y Drizzle. "
        "OfrecemosSueldo competitivo y trabajo remoto."
    )
    result = split_sections(text)

    assert "Sobre nosotrosALPRO" in result["descripcion"]
    assert "ResponsabilidadesDesarrollar" in result["descripcion"]
    assert any("3+ años con React" in r for r in result["requirements"])
    assert any("AWS y Drizzle" in r for r in result["requirements"])
    assert any("Sueldo competitivo" in b for b in result["benefits"])


def test_entrada_vacia():
    assert split_sections("") == {"descripcion": "", "requirements": [], "benefits": []}
    assert split_sections(None) == {"descripcion": "", "requirements": [], "benefits": []}
