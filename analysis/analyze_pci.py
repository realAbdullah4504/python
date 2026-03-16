from ast import Dict
import json
import unicodedata
import re
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent)) 
from config.keywords_pci_dss_americas import SCORING_CONFIG, PCI_COMPLIANCE_SIGNALS
from datetime import datetime

import json

with open("config/portals.json") as f:
    config = json.load(f)

URL = config["portals"][0]["listing_urls"][0]

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
        score += len(matched_primary) * SCORING_CONFIG["pci"]["primary_pci"]
    if matched_secondary:
        score += len(matched_secondary) * SCORING_CONFIG["pci"]["version_4"]
    
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
# File Utilities
# ------------------------------
def load_enriched_tenders(filename: str) -> list[Dict]:
    """Load enriched NDJSON (skip metadata line)."""
    tenders = []

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            if line.strip():
                tenders.append(json.loads(line))
    # Sort tenders by created_at (latest first)
    tenders.sort(
        key=lambda x: datetime.fromisoformat(x["created_at"]),
        reverse=True
    )
    return tenders


def save_scored_tenders(tenders: list, filename: str):
    """Save enriched scored tenders to NDJSON."""
    with open(filename, "w", encoding="utf-8") as f:
        for tender in tenders:
            json.dump(tender, f, ensure_ascii=False)
            f.write("\n")

def load_processed_tenders_from_ndjson(filename: str = "outputs/pci_tenders.ndjson") -> set[str]:
    """Load processed tenders from NDJSON file"""
    existing_numbers = set()
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # Process tender records
            for line in lines:
                if line.strip():
                    data = json.loads(line)
                    existing_numbers.add(data.get('number'))
        
    except FileNotFoundError:
        print(f"File {filename} not found. Starting with empty set.")
    
    print(f"Loaded {len(existing_numbers)} processed tenders from {filename}")
    return existing_numbers

# ------------------------------
# Main Workflow
# ------------------------------
def main():
    enriched_tenders_file = "outputs/enriched_tenders.ndjson"
    scored_tenders_file = "outputs/scored_tenders.ndjson"

    tenders = load_enriched_tenders(enriched_tenders_file)
    processed_tenders = load_processed_tenders_from_ndjson()
    

    scored_tenders = []
    for tender in tenders:
        if tender["number"] in processed_tenders:
            continue
        full_text = tender.get("full_text", "")
        enrichment = score_tender(full_text)
        tender.update(enrichment)
        scored_tenders.append(tender)

    save_scored_tenders(scored_tenders, scored_tenders_file)

    # Sample output
    for t in scored_tenders:
        print(
            f"{t['number']}: "
            f"PCI Score={t.get('pci_score', 0)}, "
            f"PCI Keywords={t.get('matched_pci_keywords', [])}"
        )


if __name__ == "__main__":
    main()