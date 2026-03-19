from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


# -----------------------------
# Tender Model (simplified)
# -----------------------------
class TenderModel(BaseModel):
    number: str
    description: str
    portal_name: str
    date: Optional[str] = None
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_portal_a(cls, data: Dict[str, Any]):
        # Portal A uses "expediente"
        return cls(
            number=data.get("expediente"),
            description=data.get("desc"),
            portal_name="Portal A",
            date=data.get("fecha"),
            created_at=datetime.now()
        )

    @classmethod
    def from_portal_b(cls, data: Dict[str, Any]):
        # Portal B uses "number"
        return cls(
            number=data.get("number"),
            description=data.get("description"),
            portal_name="Portal B",
            date=data.get("date"),
            created_at=datetime.now()
        )


# -----------------------------
# Fake raw data from 2 portals
# -----------------------------
portal_a_data = {
    "expediente": "A-123",
    "desc": "Road construction",
    "fecha": "2026-03-19"
}

portal_b_data = {
    "number": "B-456",
    "description": "Bridge repair",
    "date": "2026-03-18"
}


# -----------------------------
# Convert raw → model
# -----------------------------
tender1 = TenderModel.from_portal_a(portal_a_data)
tender2 = TenderModel.from_portal_b(portal_b_data)


# -----------------------------
# Use the model (clean access)
# -----------------------------
print("Tender 1:", tender1.number, "|", tender1.description)
print("Tender 2:", tender2.number, "|", tender2.description)


# -----------------------------
# Convert to dict (for storage)
# -----------------------------
print("\nAs dictionary:")
print(tender1.to_dict())
print(tender2.to_dict())