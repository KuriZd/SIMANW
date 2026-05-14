import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class SIMANWSpider(CrawlSpider):
    name = "simanw_noticias"
    allowed_domains = ["portal-noticias.com"]
    start_urls = ["https://portal-noticias.com/noticias/"]

    rules = (
        Rule(LinkExtractor(allow=r"/noticias/"), callback="parse_noticia", follow=True),
    )

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 4,
        "FEED_FORMAT": "json",
        "FEED_URI": "noticias_%(time)s.json",
    }

    def parse_noticia(self, response):
        for articulo in response.css("article.noticia"):
            yield {
                "titulo": articulo.css("h2::text").get(),
                "cuerpo": " ".join(articulo.css("p.cuerpo::text").getall()).strip(),
                "fecha": articulo.css("span.fecha::text").get(),
                "autor": articulo.css("span.autor::text").get(),
                "categoria_original": articulo.attrib.get("data-categoria", "sin_categoria"),
                "url": response.urljoin(articulo.css("a.leer-mas::attr(href)").get()),
                "fuente": response.url,
            }
