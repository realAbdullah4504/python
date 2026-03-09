# analyze_tender_enrichment.py
import json
import unicodedata
import re
from keywords_pci_dss_americas import (
    STRONG_PROCUREMENT_TRIGGERS,
    STRUCTURAL_PROCUREMENT_MARKERS,
    SCORING_CONFIG
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
def score_strong_triggers(text: str) -> (int, list):
    """Score strong procurement triggers."""
    matched_keywords = match_keywords(text, STRONG_PROCUREMENT_TRIGGERS)
    if not matched_keywords:
        score = 0
    elif len(matched_keywords) == 1:
        score = SCORING_CONFIG["procurement"]["strong_trigger"]
    else:
        score = SCORING_CONFIG["procurement"]["strong_trigger"] + \
                SCORING_CONFIG["procurement"]["additional_procurement"]
    return score, matched_keywords


def score_structural_markers(text: str) -> (int, list):
    """Score structural markers (adds bonus points)."""
    matched_structural = match_keywords(text, STRUCTURAL_PROCUREMENT_MARKERS)
    score = SCORING_CONFIG["procurement"]["structural_marker"] if matched_structural else 0
    return score, matched_structural

def score_tender(text: str) -> dict:
    """Full enrichment pipeline for one tender."""
    strong_score, matched_keywords = score_strong_triggers(text)
    structural_score, matched_structural = score_structural_markers(text)
    
    total_score = strong_score + structural_score
    
    return {
        "procurement_score": total_score,
        "matched_keywords": matched_keywords,
        "matched_structural_markers": matched_structural,
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
    for t in scored_tenders[:5]:
        print(
            f"{t['number']}: Score={t['procurement_score']}, "
            f"Keywords={t['matched_keywords']}, "
            f"Structural={t['matched_structural_markers']}"
        )


if __name__ == "__main__":
    main()