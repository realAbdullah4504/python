import json
import unicodedata
import re
from keywords_pci_dss_americas import STRONG_PROCUREMENT_TRIGGERS, SCORING_CONFIG

# Normalize text: remove accents, lowercase
def normalize_text(text):
    """Remove accents and normalize text for matching"""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text

def score_tender_text(text, keywords_dict, scoring_config):
    """
    Score the tender text with full keyword matching (no substring).
    - Normalize accents
    - Case-insensitive
    - Each keyword counts only once
    """
    norm_text = normalize_text(text)
    matched_keywords = set()
    
    for lang, keywords in keywords_dict.items():
        for keyword in keywords:
            norm_keyword = normalize_text(keyword)
            # Custom word boundary for Unicode + punctuation
            pattern = r'(?<!\w)' + re.escape(norm_keyword) + r'(?!\w)'
            if re.search(pattern, norm_text):
                matched_keywords.add(keyword)  # keep original for reporting
    
    score = len(matched_keywords) * scoring_config["procurement"]["strong_trigger"]
    return score, list(matched_keywords)

# Example usage with NDJSON enriched tenders
enriched_tenders_file = "outputs/enriched_tenders.ndjson"
scored_tenders = []

with open(enriched_tenders_file, "r", encoding="utf-8") as f:
    lines = f.readlines()[1:]  # skip metadata
    for line in lines:
        tender = json.loads(line)
        full_text = tender.get("full_text", "")
        score, matched = score_tender_text(full_text, STRONG_PROCUREMENT_TRIGGERS, SCORING_CONFIG)
        tender["procurement_score"] = score
        tender["matched_keywords"] = matched
        scored_tenders.append(tender)

# Print scored tenders with matched keywords
for t in scored_tenders[:5]:
    print(f"{t['number']}: Score = {t['procurement_score']}, Matched Keywords = {t['matched_keywords']}")