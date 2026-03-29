"""
PCI Analysis engine for processing tender PCI compliance scoring.
"""

from typing import Dict, List, Optional
from datetime import datetime
from analysis.analyze_pci import score_tender
from utils.file_utils import load_tenders_from_ndjson, update_tender_with_details, ensure_output_directory


class PCIAnalysisEngine:
    """Main orchestrator for PCI compliance analysis workflow."""

    def __init__(self, tenders_file: str = "outputs/tenders.ndjson"):
        """Initialize PCI analysis engine with file paths."""
        self.tenders_file = tenders_file

    def _needs_pci_analysis(self, tender: Dict) -> bool:
        """
        Check if a tender needs PCI analysis.
        
        Args:
            tender: Tender dictionary to check
            
        Returns:
            True if tender has full_text but no pci_score
        """
        has_full_text = bool(tender.get('full_text', '').strip())
        has_pci_score = 'pci_score' in tender
        return has_full_text and not has_pci_score

    def _process_single_tender(self, tender: Dict) -> bool:
        """
        Process PCI analysis for a single tender.
        
        Args:
            tender: Tender dictionary to process
            
        Returns:
            True if processing was successful
        """
        try:
            # Get text for scoring (combine both full_text and description for comprehensive search)
            text_to_score = "{} {}".format(
                tender.get("full_text", ""), 
                tender.get("description", "")
            ).strip()

            # Skip if no meaningful text to analyze
            if len(text_to_score.strip()) < 50:
                print(f"Skipping tender {tender.get('number', 'unknown')}: insufficient text for analysis")
                return False

            # Score the tender using existing analysis logic
            enrichment = score_tender(text_to_score)
            tender.update(enrichment)
            tender["scored_at"] = datetime.now().isoformat()
            
            # Update the tender in the file
            if update_tender_with_details(tender, self.tenders_file):
                print(
                    "Scored {}: "
                    "PCI Score={}, "
                    "PCI Keywords={}".format(
                        tender['number'],
                        tender.get('pci_score', 0),
                        tender.get('matched_pci_keywords', [])
                    )
                )
                return True
            else:
                print(f"Failed to update tender {tender['number']}")
                return False
                
        except Exception as e:
            print(f"Error processing tender {tender.get('number', 'unknown')}: {e}")
            return False

    def run(self, max_tenders: int = None) -> Dict[str, int]:
        """
        Run PCI analysis for all eligible tenders.
        
        Args:
            max_tenders: Maximum number of tenders to process (None for all)
            
        Returns:
            Summary statistics of processing results
        """
        # Ensure output directory exists
        ensure_output_directory(self.tenders_file)
        
        # Load all tenders from the file
        tenders = load_tenders_from_ndjson(self.tenders_file)
        
        if not tenders:
            print("No tenders found for PCI analysis")
            return {"total_tenders": 0, "eligible": 0, "processed": 0, "skipped": 0}
        
        if max_tenders:
            tenders = tenders[:max_tenders]
        
        # Filter tenders that need PCI analysis
        eligible_tenders = [t for t in tenders if self._needs_pci_analysis(t)]
        skipped_count = len(tenders) - len(eligible_tenders)
        
        if not eligible_tenders:
            print(f"No eligible tenders found for PCI analysis. Skipped {skipped_count} tenders.")
            return {"total_tenders": len(tenders), "eligible": 0, "processed": 0, "skipped": skipped_count}
        
        summary = {
            "total_tenders": len(tenders),
            "eligible": len(eligible_tenders),
            "processed": 0,
            "skipped": skipped_count
        }

        print(f"Starting PCI analysis for {len(eligible_tenders)} eligible tenders...")
        
        # Process each eligible tender
        for tender in eligible_tenders:
            if self._process_single_tender(tender):
                summary["processed"] += 1
        
        print(f"\nPCI Analysis Summary:")
        print(f"- Total tenders: {summary['total_tenders']}")
        print(f"- Eligible for analysis: {summary['eligible']}")
        print(f"- Successfully processed: {summary['processed']}")
        print(f"- Skipped (already scored or no full_text): {summary['skipped']}")
        
        return summary
