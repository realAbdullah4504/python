from typing import List, Dict, Set
from crawlers.core import CrawlerEngine

def main() -> None:
    """Main entry point (delegates orchestration to CrawlerEngine)."""
    engine = CrawlerEngine()
    summary = engine.run()

    print(f"Crawling completed. Summary: {summary}")


if __name__ == "__main__":
    main()
