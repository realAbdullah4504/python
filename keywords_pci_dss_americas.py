"""
PCI DSS Tender Detection Keywords - Americas Region (Excluding USA)
Generated from PCI_DSS_TENDER_DETECTION_DOCUMENT.md
"""

# Strong Procurement Triggers (High Weight)
STRONG_PROCUREMENT_TRIGGERS = {
    "spanish": [
        "Licitación", "Licitación Pública", "Licitación Privada", "Licitación Internacional",
        "Concurso Público", "Concurso de Precios", "Convocatoria", "Convocatoria Abierta",
        "Llamado a Licitación", "Llamado a Concurso", "Proceso de Contratación", 
        "Proceso de Compra", "Bases y Condiciones", "Pliego", "Pliego de Bases y Condiciones",
        "Pliego Técnico", "Pliego Administrativo", "Cartel de Licitación", 
        "Términos de Referencia", "TDR", "Solicitud de Propuesta", "Solicitud de Cotización",
        "Solicitud de Oferta", "Invitación a Cotizar", "Invitación a Ofertar",
        "Presentación de Ofertas", "Apertura de Ofertas", "Acto de Apertura", "Adjudicación"
    ],
    "portuguese": [
        "Licitação", "Edital", "Edital de Licitação", "Pregão", "Pregão Eletrônico",
        "Tomada de Preços", "Concorrência Pública", "Chamamento Público", 
        "Processo Licitatório", "Termo de Referência", "Carta Convite", 
        "Proposta Comercial", "Proposta Técnica", "Recebimento de Propostas",
        "Julgamento das Propostas", "Homologação", "Adjudicação"
    ],
    "english": [
        "RFP", "RFQ", "RFI", "ITB", "IFB", "EOI", "Tender", "Tender Notice", 
        "Bidding Process", "Procurement", "Solicitation", "Call for Proposals",
        "Invitation to Bid", "Terms of Reference", "ToR", "Tender Document",
        "Bidding Document", "Scope of Work", "SOW", "Statement of Work",
        "Technical Specifications", "Bid Submission", "Proposal Submission", "Contract Award"
    ]
}

# Structural Procurement Markers (Mandatory at least 1)
STRUCTURAL_PROCUREMENT_MARKERS = {
    "spanish": [
        "Fecha límite", "Cierre de recepción", "Plazo de recepción", "Cronograma",
        "Calendario del proceso", "Consultas hasta", "Ronda de consultas", "Aclaraciones",
        "Anexos", "Formulario de oferta", "Garantía de mantenimiento de oferta",
        "Garantía de cumplimiento", "Expediente N°", "Licitación N°", 
        "Objeto de la contratación", "Alcance del servicio"
    ],
    "portuguese": [
        "Data limite", "Prazo para envio", "Cronograma", "Sessão de abertura",
        "Anexos", "Número do processo", "Objeto da contratação", "Critérios de julgamento"
    ],
    "english": [
        "Submission deadline", "Due date", "Closing date", "Timeline", "Schedule",
        "Evaluation criteria", "Award criteria", "Send proposals to", "Submit proposal to",
        "Attachments", "Annex", "Solicitation number", "Tender reference", "Bid number"
    ]
}

# PCI / Payment Compliance Signals
PCI_COMPLIANCE_SIGNALS = {
    "primary": [
        "PCI DSS", "PCI-DSS", "Payment Card Industry", "PCI compliance"
    ],
    "secondary": [
        "4.0", "4.0.1", "v4.0", "v4.0.1", "Cardholder Data", "CHD", 
        "Payment card data", "Datos de tarjeta", "Dados de cartão", "Tarjetahabiente",
        "Procesamiento de pagos", "Pasarela de pagos", "Gateway de pagos",
        "Switch transaccional", "Adquirencia", "Adquirente"
    ]
}

# Noise Exclusion List
NOISE_EXCLUSION_LIST = {
    "english": [
        "training", "course", "webinar", "workshop", "bootcamp", "blog", "article",
        "news", "press release", "hiring", "job", "career", "template", "guide", "what is"
    ],
    "spanish": [
        "curso", "capacitación", "seminario", "blog", "noticia", "comunicado",
        "empleo", "vacante", "guía", "plantilla", "¿qué es?"
    ],
    "portuguese": [
        "curso", "treinamento", "blog", "notícia", "vaga", "emprego", "guia", "modelo"
    ]
}

# Geographic Domain Filtering
APPROVED_DOMAINS = [
    ".gob.ar", ".gob.mx", ".gov.br", ".gub.uy", ".gob.pe", ".gob.cl", ".gov.co",
    ".gob.ec", ".gob.pa", ".gob.do", ".gob.sv", ".gob.gt", ".gob.hn", ".gob.ni",
    ".gob.bo", ".gob.py"
]

EXCLUDED_DOMAINS = [
    "sam.gov", "federalregister.gov", "usaspending.gov"
]

# Scoring System Configuration
SCORING_CONFIG = {
    "procurement": {
        "strong_trigger": 4,
        "additional_procurement": 2,
        "structural_marker": 2,
        "deadline_date": 2,
        "email_submission": 2
    },
    "pci": {
        "primary_pci": 3,
        "version_4": 1,
        "payment_card_terms": 1
    },
    "thresholds": {
        "min_procurement_score": 6,
        "min_pci_score": 3
    }
}

# Helper function to get all keywords as flat lists
def get_all_procurement_keywords():
    """Returns all procurement keywords as a flat list"""
    all_keywords = []
    for lang_keywords in STRONG_PROCUREMENT_TRIGGERS.values():
        all_keywords.extend(lang_keywords)
    return all_keywords

def get_all_structural_markers():
    """Returns all structural markers as a flat list"""
    all_markers = []
    for lang_markers in STRUCTURAL_PROCUREMENT_MARKERS.values():
        all_markers.extend(lang_markers)
    return all_markers

def get_all_pci_keywords():
    """Returns all PCI keywords as a flat list"""
    all_pci = []
    all_pci.extend(PCI_COMPLIANCE_SIGNALS["primary"])
    all_pci.extend(PCI_COMPLIANCE_SIGNALS["secondary"])
    return all_pci

def get_all_noise_keywords():
    """Returns all noise keywords as a flat list"""
    all_noise = []
    for lang_noise in NOISE_EXCLUSION_LIST.values():
        all_noise.extend(lang_noise)
    return all_noise

# Example usage and testing
if __name__ == "__main__":
    print("PCI DSS Tender Detection Keywords - Americas Region")
    print("=" * 50)
    
    print(f"Strong Procurement Triggers: {len(get_all_procurement_keywords())}")
    print(f"Structural Markers: {len(get_all_structural_markers())}")
    print(f"PCI Keywords: {len(get_all_pci_keywords())}")
    print(f"Noise Keywords: {len(get_all_noise_keywords())}")
    print(f"Approved Domains: {len(APPROVED_DOMAINS)}")
    print(f"Excluded Domains: {len(EXCLUDED_DOMAINS)}")
