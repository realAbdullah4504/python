from ast import Dict
import json
import unicodedata
import re
from config.keywords_pci_dss_americas import SCORING_CONFIG, PCI_COMPLIANCE_SIGNALS
from datetime import datetime
from utils.file_utils import load_tenders_from_ndjson, update_tender_with_details, ensure_output_directory

# ------------------------------
# Text Utilities
# ------------------------------
def normalize_text(text: str) -> str:
    """Lowercase and remove accents for consistent matching."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def match_keywords(text: str, keywords_dict: dict) -> list:
    """Return a list of matched keywords/phrases."""
    norm_text = normalize_text(text)
    matched = set()
    for lang, keywords in keywords_dict.items():
        for keyword in keywords:
            norm_keyword = normalize_text(keyword)
            pattern = r'(?<!\w)' + re.escape(norm_keyword) + r'(?!\w)'
            if re.search(pattern, norm_text):
                matched.add(keyword)  # keep original keyword
    return list(matched)


# ------------------------------
# Scoring Functions
# ------------------------------
def score_pci_compliance(text: str) -> (int, list):
    """Score PCI compliance signals."""
    matched_primary = match_keywords(text, {"primary": PCI_COMPLIANCE_SIGNALS["primary"]})
    matched_secondary = match_keywords(text, {"secondary": PCI_COMPLIANCE_SIGNALS["secondary"]})
    
    score = 0
    if matched_primary:
        score += SCORING_CONFIG["pci"]["primary_pci"]  # Score only 1 point if any primary keyword matches
    if matched_secondary:
        score += len(matched_secondary) * SCORING_CONFIG["pci"]["version_4"]
    
    print(matched_primary,matched_secondary)
    all_matched = matched_primary + matched_secondary
    return score, all_matched


def score_tender(text: str) -> dict:
    """Full enrichment pipeline for one tender."""
    # PCI compliance scoring
    pci_score, matched_pci = score_pci_compliance(text)
    
    return {
        "pci_score": pci_score,
        "matched_pci_keywords": matched_pci,
    }


# ------------------------------
# Main Workflow
# ------------------------------
def main():
    tenders_file = "outputs/tenders.ndjson"
    
    # Ensure output directory exists
    ensure_output_directory(tenders_file)
    
    # Load all tenders from the file
    tenders = load_tenders_from_ndjson(tenders_file)
    
    # Track which tenders we've already scored
    scored_count = 0
    skipped_count = 0
    
    for tender in tenders:
        # Skip if already scored (has pci_score field)
        if 'pci_score' in tender:
            skipped_count += 1
            continue
            
        # Get text for scoring (combine both full_text and description for comprehensive search)
        text_to_score = "{} {}".format(
            tender.get("full_text", ""), 
            tender.get("description", "")
        ).strip()

        # Score the tender
        enrichment = score_tender(text_to_score)
        tender.update(enrichment)
        tender["scored_at"] = datetime.now().isoformat()
        
        # Update the tender in the file
        if update_tender_with_details(tender, tenders_file):
            scored_count += 1
            print(
                "Scored {}: "
                "PCI Score={}, "
                "PCI Keywords={}".format(
                    tender['number'],
                    tender.get('pci_score', 0),
                    tender.get('matched_pci_keywords', [])
                )
            )
        else:
            print("Failed to update tender {}".format(tender['number']))
    
    print("\nSummary:")
    print("- Total tenders processed: {}".format(len(tenders)))
    print("- Newly scored: {}".format(scored_count))
    print("- Already scored (skipped): {}".format(skipped_count))
    print("- File updated: {}".format(tenders_file))


if __name__ == "__main__":
    main()