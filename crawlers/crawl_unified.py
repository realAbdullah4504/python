from typing import List, Dict, Set

from models.tender import TenderModel
from crawlers.strategies import CrawlerFactory
from crawlers.core import CrawlerEngine


def crawl_all_tenders(url: str, portal_config: Dict, seen_tender_numbers: Set[str]) -> List[TenderModel]:
    """
    Main function to crawl and parse all tenders from portal.
    Uses strategy pattern to select appropriate crawler.
    """
    try:
        # Create appropriate crawler strategy using factory
        crawler = CrawlerFactory.create_crawler(portal_config)
        
        # Execute crawling using the selected strategy
        tenders = crawler.crawl(url, portal_config, seen_tender_numbers)
        
        return tenders
        
    except ValueError as e:
        print(f"Error creating crawler: {e}")
        return []


def main() -> None:
    """Main entry point (delegates orchestration to CrawlerEngine)."""
    engine = CrawlerEngine()
    all_tenders = engine.run()

    for t in all_tenders[:5]:
        print(t)


if __name__ == "__main__":
    main()
