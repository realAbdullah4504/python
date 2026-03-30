from typing import List, Dict, Set
from crawlers.core import CrawlerEngine
from crawlers.core.details_engine import DetailsEngine
from crawlers.core.pci_analysis_engine import PCIAnalysisEngine
from utils.logger import get_logger, log_phase_start, log_phase_end, log_error_with_context

def main() -> None:
    """Main entry point (delegates orchestration to CrawlerEngine, DetailsEngine, and PCIAnalysisEngine)."""
    logger = get_logger(__name__, "pipeline")
    
    try:
        # Step 1: Run the crawler to collect tender data
        log_phase_start(logger, "crawling")
        crawler_engine = CrawlerEngine()
        crawler_summary = crawler_engine.run()
        log_phase_end(logger, "crawling", crawler_summary)
        
        # Step 2: Run the details engine to enrich tender data
        log_phase_start(logger, "details_extraction")
        details_engine = DetailsEngine()
        details_summary = details_engine.run()
        log_phase_end(logger, "details_extraction", details_summary)
        
        # Step 3: Run the PCI analysis engine to score tenders
        log_phase_start(logger, "pci_analysis")
        pci_engine = PCIAnalysisEngine()
        pci_summary = pci_engine.run()
        log_phase_end(logger, "pci_analysis", pci_summary)
        
        # Overall summary
        logger.info("Pipeline completed successfully!")
        logger.info(f"Final summary - Details: {details_summary}, PCI Analysis: {pci_summary}")
        
    except Exception as e:
        log_error_with_context(logger, e, "pipeline execution")
        raise


if __name__ == "__main__":
    main()
