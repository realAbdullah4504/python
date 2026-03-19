import json
from typing import List, Dict, Set
from datetime import datetime
import os


def load_existing_tender_numbers(filename: str = "outputs/tenders.ndjson") -> Set[str]:
    """Load existing tender docIds from NDJSON file"""
    existing_docids = set()
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    # Use docId for deduplication, fallback to number for backward compatibility
                    if "docId" in data and data["docId"]:
                        existing_docids.add(data["docId"])
                    elif "number" in data:
                        existing_docids.add(data["number"])
    except FileNotFoundError:
        pass
    return existing_docids


def save_tenders_to_ndjson(tenders: List, filename: str = "outputs/tenders.ndjson") -> bool:
    """Save a list of tenders to NDJSON file (append mode)"""
    try:
        # Convert TenderModel objects to dictionaries if needed
        tender_dicts = []
        for tender in tenders:
            if hasattr(tender, 'to_dict'):
                # Convert TenderModel to dictionary
                tender_dict = tender.to_dict()
            else:
                # Already a dictionary
                tender_dict = tender
            
            # Add creation date time
            tender_dict["created_at"] = datetime.now().isoformat()
            tender_dicts.append(tender_dict)
        
        # Save to file
        with open(filename, 'a', encoding='utf-8') as f:
            for tender_dict in tender_dicts:
                json.dump(tender_dict, f, ensure_ascii=False)
                f.write('\n')
    except Exception as e:
        print(f"Error saving tenders: {e}")
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


def load_seen_tender_numbers(filename: str = "outputs/seen_tenders.ndjson") -> Set[str]:
    """Load existing tender numbers from NDJSON state file"""
    seen_numbers = set()
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    seen_numbers.add(data)
    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        print(f"Error reading {filename}. Starting with empty set.")
    
    print(f"Loaded {len(seen_numbers)} seen tender numbers from {filename}")
    return seen_numbers


def save_seen_tender_numbers(tender_numbers: Set[str], filename: str = "outputs/seen_tenders.ndjson") -> None:
    """Save a set of tender numbers to NDJSON state file"""
    try:
        # Append only the new numbers - NO FILE LOADING!
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'a', encoding='utf-8') as f:
            for number in tender_numbers:
                json.dump(number, f, ensure_ascii=False)
                f.write('\n')
    except Exception as e:
        print(f"Error saving tender numbers to state file: {e}")


def load_portal_config(config_path: str = "config/portals.json") -> Dict:
    """Load portal configuration from JSON file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


def ensure_output_directory(file_path: str) -> None:
    """Create output directory if it doesn't exist"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
