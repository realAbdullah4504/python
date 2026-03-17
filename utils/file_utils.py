import json
from typing import List, Dict, Set
from datetime import datetime
import os


def load_existing_tender_numbers(filename: str = "outputs/tenders.ndjson") -> Set[str]:
    """Load existing tender numbers from NDJSON file"""
    existing_numbers = set()
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if "number" in data:
                        existing_numbers.add(data["number"])
    except FileNotFoundError:
        pass
    return existing_numbers


def save_tender_to_ndjson(tender: Dict, filename: str = "outputs/tenders.ndjson") -> bool:
    """Save a single tender to NDJSON file (append mode)"""
    try:
        # Add creation date time to the tender
        tender["created_at"] = datetime.now().isoformat()
        with open(filename, 'a', encoding='utf-8') as f:
            json.dump(tender, f, ensure_ascii=False)
            f.write('\n')
    except Exception as e:
        print(f"Error saving tender {tender.get('number', 'unknown')}: {e}")
        return False
    return True


def load_tenders_from_ndjson(filename: str = "outputs/tenders.ndjson") -> List[Dict]:
    """Load tenders from NDJSON file and sort by created_at (latest first)"""
    tenders = []

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                tenders.append(json.loads(line))

    # Sort tenders by created_at (latest first)
    tenders.sort(
        key=lambda x: datetime.fromisoformat(x["created_at"]),
        reverse=True
    )

    print(f"Loaded {len(tenders)} tenders from {filename}")
    return tenders


def load_processed_tenders_from_ndjson(filename: str = "outputs/enriched_tenders.ndjson") -> set[str]:
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


def save_enriched_tender(tender: Dict, filename: str = "outputs/enriched_tenders.ndjson") -> None:
    """Save enriched tender to NDJSON file"""
    with open(filename, 'a', encoding='utf-8') as f:
        json.dump(tender, f, ensure_ascii=False)
        f.write('\n')
        f.flush()  # Ensure immediate write to disk


def save_tenders_to_json(tenders: List[Dict], filename: str) -> None:
    """Save tenders to JSON file"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(tenders, f, ensure_ascii=False, indent=2)


def load_portal_config(config_path: str = "config/portals.json") -> Dict:
    """Load portal configuration from JSON file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


def ensure_output_directory(file_path: str) -> None:
    """Create output directory if it doesn't exist"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
