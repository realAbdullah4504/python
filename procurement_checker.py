"""
Strong Procurement Keywords Checker
Simplified version that only checks for strong procurement triggers
"""

import re
import unicodedata
from typing import Dict
from keywords_pci_dss_americas import STRONG_PROCUREMENT_TRIGGERS, STRUCTURAL_PROCUREMENT_MARKERS, SCORING_CONFIG

def normalize_text(text):
    """Remove accents and normalize text for matching"""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text

class StrongKeywordChecker:
    def __init__(self):
        self._prepare_keyword_patterns()
        self.scoring_config = SCORING_CONFIG["procurement"]
        self.thresholds = SCORING_CONFIG["thresholds"]
    
    def _prepare_keyword_patterns(self):
        """Prepare regex patterns for efficient matching"""
        self.procurement_patterns = {}
        self.structural_patterns = {}
        
        # Prepare procurement patterns with normalized keywords
        for lang, keywords in STRONG_PROCUREMENT_TRIGGERS.items():
            patterns = []
            for keyword in keywords:
                # Create pattern for both accented and non-accented versions
                normalized_keyword = normalize_text(keyword)
                pattern = re.compile(r'\b' + re.escape(normalized_keyword) + r'\b', re.IGNORECASE)
                patterns.append((keyword, pattern))  # Store original keyword and pattern
            self.procurement_patterns[lang] = patterns
        
        # Prepare structural marker patterns
        for lang, markers in STRUCTURAL_PROCUREMENT_MARKERS.items():
            patterns = []
            for marker in markers:
                normalized_marker = normalize_text(marker)
                pattern = re.compile(r'\b' + re.escape(normalized_marker) + r'\b', re.IGNORECASE)
                patterns.append((marker, pattern))
            self.structural_patterns[lang] = patterns
    
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
    
    def detect_structural_markers(self, text):
        """Detect structural procurement markers"""
        found_markers = []
        normalized_text = normalize_text(text)
        
        for lang, patterns in self.structural_patterns.items():
            for original_marker, pattern in patterns:
                if pattern.search(normalized_text):
                    found_markers.append({
                        'language': lang,
                        'marker': original_marker
                    })
        
        return found_markers
    
    def detect_additional_signals(self, text):
        """Detect additional procurement signals like dates and emails"""
        normalized_text = normalize_text(text)
        signals = {
            'deadline_dates': [],
            'email_submission': False
        }
        
        # Date patterns
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # DD/MM/YYYY or DD-MM-YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',   # YYYY/MM/DD or YYYY-MM-DD
            r'\b\d{1,2}\sde\s\w+\sde\s\d{4}\b',    # DD de mes de YYYY (Spanish)
            r'\b\d{1,2}\sde\s\w+\sde\s\d{4}\b',    # DD de mes de YYYY (Portuguese)
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, normalized_text)
            signals['deadline_dates'].extend(matches)
        
        # Email submission pattern
        email_pattern = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
        if email_pattern.search(text):
            signals['email_submission'] = True
        
        return signals
    
    def calculate_procurement_score(self, text: str) -> Dict[str, float]:
        """
        Calculate procurement score based on detected signals
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with detailed scoring information
        """
        # Detect all signals
        strong_keywords = self.check_strong_keywords(text)
        structural_markers = self.detect_structural_markers(text)
        additional_signals = self.detect_additional_signals(text)
        
        # Calculate scores based on configuration
        strong_score = 0
        additional_procurement_score = 0
        
        if len(strong_keywords) > 0:
            # First strong keyword gets strong_trigger weight
            strong_score = self.scoring_config["strong_trigger"]
            
            # Additional strong keywords (beyond the first one) get additional_procurement weight
            if len(strong_keywords) > 1:
                additional_procurement_score = (len(strong_keywords) - 1) * self.scoring_config["additional_procurement"]
        
        structural_score = len(structural_markers) * self.scoring_config["structural_marker"]
        deadline_score = len(additional_signals["deadline_dates"]) * self.scoring_config["deadline_date"]
        email_score = self.scoring_config["email_submission"] if additional_signals["email_submission"] else 0
        
        total_score = strong_score + structural_score + deadline_score + email_score + additional_procurement_score
        
        return {
            "total_score": total_score,
            "strong_score": strong_score,
            "structural_score": structural_score,
            "deadline_score": deadline_score,
            "email_score": email_score,
            "additional_procurement_score": additional_procurement_score,
            "strong_keywords": strong_keywords,
            "structural_markers": structural_markers,
            "deadline_dates": additional_signals["deadline_dates"],
            "email_submission": additional_signals["email_submission"],
            "meets_threshold": total_score >= self.thresholds["min_procurement_score"],
            "threshold_met": self.thresholds["min_procurement_score"]
        }
    
    def print_keyword_report(self, text, url=None):
        """Print detailed procurement scoring report"""
        print("=" * 60)
        print("PROCUREMENT SCORING REPORT")
        print("=" * 60)
        
        if url:
            print(f"URL: {url}")
        
        score = self.calculate_procurement_score(text)
        
        print("\n📊 TOTAL SCORE: {:.1f} (Threshold: {})".format(score['total_score'], score['threshold_met']))
        print("🎯 MEETS THRESHOLD: {}".format('✅ YES' if score['meets_threshold'] else '❌ NO'))
        
        print("\n📈 SCORE BREAKDOWN:")
        print("  • Strong procurement keywords: {:.1f} ({} found)".format(score['strong_score'], len(score['strong_keywords'])))
        print("  • Structural markers: {:.1f} ({} found)".format(score['structural_score'], len(score['structural_markers'])))
        print("  • Deadline dates: {:.1f} ({} found)".format(score['deadline_score'], len(score['deadline_dates'])))
        print("  • Email submission: {:.1f} ({})".format(score['email_score'], 'Yes' if score['email_submission'] else 'No'))
        print("  • Additional procurement: {:.1f}".format(score['additional_procurement_score']))
        
        if score['strong_keywords']:
            print("\n🔍 STRONG PROCUREMENT KEYWORDS:")
            for kw in score['strong_keywords']:
                print("  • [{}] {}".format(kw['language'].title(), kw['keyword']))
        
        if score['structural_markers']:
            print("\n🏗️  STRUCTURAL MARKERS:")
            for marker in score['structural_markers']:
                print("  • [{}] {}".format(marker['language'].title(), marker['marker']))
        
        if score['deadline_dates']:
            print("\n📅 DEADLINE DATES FOUND:")
            for date in score['deadline_dates'][:5]:  # Show max 5 dates
                print("  • {}".format(date))
            if len(score['deadline_dates']) > 5:
                print("  • ... and {} more".format(len(score['deadline_dates']) - 5))
        
        print("=" * 60)
        return score['meets_threshold']


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
