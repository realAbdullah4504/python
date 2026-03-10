# analyze_tender_enrichment.py
import json
import unicodedata
import re
from keywords_pci_dss_americas import (
    SCORING_CONFIG,
    PCI_COMPLIANCE_SIGNALS
)

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
        score += len(matched_secondary) * SCORING_CONFIG["pci"]["payment_card_terms"]
    
    # Check for version 4 references
    version_keywords = ["4.0", "4.0.1", "v4.0", "v4.0.1"]
    for version in version_keywords:
        if version.lower() in text.lower():
            score += SCORING_CONFIG["pci"]["version_4"]
            break
    
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
def load_enriched_tenders(filename: str) -> tuple:
    """Load enriched NDJSON (skip metadata line)."""
    tenders = []
    source_url = None
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if lines:
            metadata = json.loads(lines[0].strip())
            source_url = metadata.get("source_url")
        for line in lines[1:]:
            if line.strip():
                tenders.append(json.loads(line))
    return tenders, source_url


def save_scored_tenders(tenders: list, source_url: str, filename: str):
    """Save enriched scored tenders to NDJSON."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"source_url": source_url}, f, ensure_ascii=False)
        f.write("\n")
        for tender in tenders:
            json.dump(tender, f, ensure_ascii=False)
            f.write("\n")


# ------------------------------
# Main Workflow
# ------------------------------
def main():
    enriched_tenders_file = "outputs/enriched_tenders.ndjson"
    scored_tenders_file = "outputs/scored_tenders.ndjson"

    tenders, source_url = load_enriched_tenders(enriched_tenders_file)

    scored_tenders = []
    for tender in tenders:
        full_text = tender.get("full_text", "")
        enrichment = score_tender(full_text)
        tender.update(enrichment)
        scored_tenders.append(tender)

    save_scored_tenders(scored_tenders, source_url, scored_tenders_file)

    # Sample output
    for t in scored_tenders:
        print(
            f"{t['number']}: "
            f"PCI Score={t.get('pci_score', 0)}, "
            f"PCI Keywords={t.get('matched_pci_keywords', [])}"
        )


if __name__ == "__main__":
    main()