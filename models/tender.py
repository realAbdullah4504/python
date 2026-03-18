from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TenderModel(BaseModel):
    """
    Generic tender data model for unified structure across different crawlers.
    """
    
    # Document identifier from source system
    docId: Optional[str] = Field(None, description="Document ID from source system")
    
    # Unique tender number/expediente
    number: str = Field(..., description="Unique tender number or expediente")
    
    # Tender description
    description: str = Field(..., description="Full description of the tender")
    
    # Document type
    type: Optional[str] = Field("", description="Document type (e.g., Informe, Resolución)")
    
    # Date information
    date: Optional[str] = Field("", description="Publication or last updated date")
    
    # Status
    status: str = Field("active", description="Current status of the tender")
    
    # URLs
    url: str = Field(..., description="Source URL where tender was found")
    details_url: Optional[str] = Field(None, description="Direct URL to tender details or document")
    
    # Pagination info
    page_no: int = Field(1, description="Page number where tender was found")
    
    # Portal information
    portal_name: str = Field(..., description="Name of the source portal")
    
    # Category information
    category: Optional[str] = Field("", description="Category or classification of the tender")
    
    # Metadata
    created_at: str = Field(..., description="Timestamp when this record was created")
    
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return self.model_dump(exclude_none=True)
    
    def to_json(self) -> str:
        """Convert model to JSON string"""
        return self.model_dump_json(exclude_none=True, indent=2)
    
    @classmethod
    def from_pattern_tender(cls, pattern_tender: Dict[str, Any], portal_name: str, source_url: str) -> "TenderModel":
        """Create TenderModel from pattern-based tender data"""
        doc_id = pattern_tender.get("docId", "")
        details_url = f"https://www.csjn.gov.ar/documentos/descargar?ID={doc_id}" if doc_id else None
        
        return cls(
            docId=doc_id,
            number=pattern_tender.get("expediente", ""),
            description=pattern_tender.get("description", ""),
            type=pattern_tender.get("document_type", ""),
            date=pattern_tender.get("date", ""),
            status="active",
            url=source_url,
            details_url=details_url,
            page_no=1,
            portal_name=portal_name,
            category=pattern_tender.get("category", ""),
            created_at=datetime.now().isoformat()
        )
    
    @classmethod
    def from_table_tender(cls, table_tender: Dict[str, Any], portal_name: str) -> "TenderModel":
        """Create TenderModel from table-based tender data"""
        return cls(
            number=table_tender.get("number", ""),
            description=table_tender.get("description", ""),
            type=table_tender.get("type", ""),
            date=table_tender.get("date", ""),
            status=table_tender.get("status", "active"),
            url=table_tender.get("url", ""),
            details_url=table_tender.get("details_url"),
            page_no=table_tender.get("page_no", 1),
            portal_name=portal_name,
            created_at=datetime.now().isoformat()
        )


class TenderList(BaseModel):
    """Container for multiple tenders"""
    tenders: list[TenderModel]
    total_count: int
    portal_name: str
    created_at: str
    
    @classmethod
    def create_empty(cls, portal_name: str) -> "TenderList":
        """Create empty tender list"""
        return cls(
            tenders=[],
            total_count=0,
            portal_name=portal_name,
            created_at=datetime.now().isoformat()
        )
    
    def add_tender(self, tender: TenderModel) -> None:
        """Add a tender to the list"""
        self.tenders.append(tender)
        self.total_count = len(self.tenders)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump()
