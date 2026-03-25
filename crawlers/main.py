from typing import List, Dict, Set

from models.tender import TenderModel
from crawlers.strategies import CrawlerFactory
from crawlers.core import CrawlerEngine

def main() -> None:
    """Main entry point (delegates orchestration to CrawlerEngine)."""
    engine = CrawlerEngine()
    all_tenders = engine.run()

    for t in all_tenders[:5]:
        print(t)


if __name__ == "__main__":
    main()
