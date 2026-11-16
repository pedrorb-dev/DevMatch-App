import scrapy


class JobOfferItem(scrapy.Item):
    # extraídos del sitio
    titulo = scrapy.Field()  # str
    empresa = scrapy.Field()  # str
    modalidad_raw = scrapy.Field()  # str (intermedio: Remoto/Remote/Híbrido/Hybrid/Presencial/On-site)
    ubicacion_texto = scrapy.Field()  # str (ej. "Jalisco - Híbrido", "Remoto: México")
    descripcion = scrapy.Field()  # str (descripción/resumen sin listas de requisitos/beneficios cuando se pueden separar)
    tags_tecnologias = scrapy.Field()  # list[str] (intermedio, tags de Hireline)
    url_oferta = scrapy.Field()  # str (canonical)

    # normalizados por el pipeline
    modalidad = scrapy.Field()  # 'Remoto' | 'Híbrido' | 'Presencial'
    stack_detectado = scrapy.Field()  # list[str]
    es_practicante = scrapy.Field()  # bool
    nivel_ingles = scrapy.Field()  # 'No especificado' | 'B1' | 'B2' | 'C1'
    requirements = scrapy.Field()  # list[str] (extraídos/normalizados; pueden quedar vacíos si no hay sección)
    benefits = scrapy.Field()  # list[str] (extraídos/normalizados; pueden quedar vacíos si no hay sección)
