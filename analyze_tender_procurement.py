import json
import unicodedata
from keywords_pci_dss_americas import STRONG_PROCUREMENT_TRIGGERS, SCORING_CONFIG

# Normalize text: remove accents, lowercase
def normalize_text(text):
    text = unicodedata.normalize('NFKD', text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower()

def score_tender_text(text, keywords_dict, scoring_config):
    """
    Score the tender text:
      - Normalize accents
      - Case-insensitive
      - Each keyword counts only once
    """
    norm_text = normalize_text(text)
    matched_keywords = set()
    
    for lang, keywords in keywords_dict.items():
        for keyword in keywords:
            norm_keyword = normalize_text(keyword)
            if norm_keyword in norm_text:
                matched_keywords.add(norm_keyword)
    
    score = len(matched_keywords) * scoring_config["procurement"]["strong_trigger"]
    return score

# Example usage with NDJSON enriched tenders
enriched_tenders_file = "outputs/enriched_tenders.ndjson"
scored_tenders = []

with open(enriched_tenders_file, "r", encoding="utf-8") as f:
    lines = f.readlines()[1:]  # skip metadata
    for line in lines:
        tender = json.loads(line)
        full_text = tender.get("full_text", "")
        score = score_tender_text(full_text, STRONG_PROCUREMENT_TRIGGERS, SCORING_CONFIG)
        tender["procurement_score"] = score
        scored_tenders.append(tender)

# Print scored tenders
for t in scored_tenders:
    print(f"{t['number']}: Score = {t['procurement_score']}")