"""Run every spider of the project sequentially from a single process.

The daily GitHub Actions workflow invokes this module (``python run_spiders.py``)
so one run covers every source (Hireline, OCCMundial, Computrabajo and Get on
Board) instead of separate ``scrapy crawl`` invocations.

``CrawlerProcess`` is built to run crawlers in parallel, so the next spider is
only started from the previous crawl's deferred. That keeps the crawls
sequential while sharing settings, item pipelines and the reactor. A spider
that fails does not abort the run: the error is logged and the remaining
spiders still run, and ``main`` returns a non-zero exit code at the end.
"""

import logging
import sys

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.python.failure import Failure

from job_scraper.spiders.computrabajo_spider import ComputrabajoSpider
from job_scraper.spiders.getonbrd_spider import GetOnBrdSpider
from job_scraper.spiders.hireline_spider import HirelineSpider
from job_scraper.spiders.occ_spider import OccSpider


logger = logging.getLogger(__name__)

SPIDERS = (
    ("hireline", HirelineSpider),
    ("occ", OccSpider),
    ("computrabajo", ComputrabajoSpider),
    ("getonbrd", GetOnBrdSpider),
)


def main():
    process = CrawlerProcess(get_project_settings())
    failed = []

    def crawl_from(index):
        if index >= len(SPIDERS):
            return None

        name, spider_cls = SPIDERS[index]
        deferred = process.crawl(spider_cls)

        def on_finished(result):
            if isinstance(result, Failure):
                failed.append(name)
                logger.error("Spider %r failed: %s", name, result.getTraceback())
            return crawl_from(index + 1)

        deferred.addBoth(on_finished)
        return deferred

    crawl_from(0)
    # Starts the reactor and blocks until every chained crawl has finished.
    process.start()

    if failed:
        print(f"Failed spiders: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
