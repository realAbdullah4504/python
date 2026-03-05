"""
Strong Procurement Keywords Checker
Simplified version that only checks for strong procurement triggers
"""

import re
import unicodedata
from keywords_pci_dss_americas import STRONG_PROCUREMENT_TRIGGERS

def normalize_text(text):
    """Remove accents and normalize text for matching"""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text

class StrongKeywordChecker:
    def __init__(self):
        self._prepare_keyword_patterns()
    
    def _prepare_keyword_patterns(self):
        """Prepare regex patterns for efficient matching"""
        self.procurement_patterns = {}
        
        # Prepare procurement patterns with normalized keywords
        for lang, keywords in STRONG_PROCUREMENT_TRIGGERS.items():
            patterns = []
            for keyword in keywords:
                # Create pattern for both accented and non-accented versions
                normalized_keyword = normalize_text(keyword)
                pattern = re.compile(r'\b' + re.escape(normalized_keyword) + r'\b', re.IGNORECASE)
                patterns.append((keyword, pattern))  # Store original keyword and pattern
            self.procurement_patterns[lang] = patterns
    
    def check_strong_keywords(self, text):
        """Check for strong procurement keywords only"""
        found_keywords = []
        
        # Normalize the input text for matching
        normalized_text = normalize_text(text)
        
        for lang, patterns in self.procurement_patterns.items():
            for original_keyword, pattern in patterns:
                if pattern.search(normalized_text):
                    found_keywords.append({
                        'language': lang,
                        'keyword': original_keyword  # Return the original keyword with accents
                    })
        
        return found_keywords
    
    def print_keyword_report(self, text, url=None):
        """Print simple keyword detection report"""
        print("=" * 50)
        print("STRONG PROCUREMENT KEYWORDS CHECK")
        print("=" * 50)
        
        if url:
            print(f"URL: {url}")
        
        found_keywords = self.check_strong_keywords(text)
        
        if found_keywords:
            print(f"✅ Found {len(found_keywords)} strong procurement keywords:")
            for kw in found_keywords:
                print(f"  • [{kw['language'].title()}] {kw['keyword']}")
        else:
            print("❌ No strong procurement keywords found")
        
        print("=" * 50)
        return len(found_keywords) > 0


# Example usage and testing
if __name__ == "__main__":
    checker = StrongKeywordChecker()
    
    # Test cases
    test_cases = [
        {
            "name": "Valid Argentine Tender",
            "url": "https://comprar.gob.ar/licitacion/123",
            "text": """
            Licitación Pública N° 2026/12345
            Objeto de la contratación: Servicios de auditoría PCI DSS 4.0
            Fecha límite de presentación: 31/03/2026
            Las propuestas deben ser enviadas a licitaciones@ministerio.gob.ar
            Pliego de bases y condiciones disponible en anexo.
            """
        },
        {
            "name": "Brazil Tender",
            "url": "https://www.gov.br/compras/edital/456",
            "text": """
            Edital de Licitação 2026/456
            Objeto: Implementação de soluções PCI DSS v4.0.1
            Data limite: 15/04/2026
            Envio de propostas para compras@banco.gov.br
            Anexos técnicos disponíveis para download.
            """
        },
        {
            "name": "Training Content (Should be Rejected)",
            "url": "https://example.com/course",
            "text": """
            Curso de capacitación sobre PCI DSS 4.0
            Aprenda sobre payment card industry compliance
            Webinar gratuito sobre procesamiento de pagos
            """
        },
        {
            "name": "Simple Text with Tender",
            "url": None,
            "text": "We have a public tender for RFP services"
        },
        {
            "name": "Accent Test - Non-accented Spanish",
            "url": None,
            "text": "Proceso de Licitacion Publica para servicios. Se requiere presentacion de ofertas."
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['name']}")
        checker.print_keyword_report(test_case["text"], test_case["url"])
        print("\n" + "="*60 + "\n")
