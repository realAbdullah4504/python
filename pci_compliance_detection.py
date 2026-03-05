"""
STEP 3: PCI Compliance Signal Detection
Implements PCI DSS and payment card compliance detection with high accuracy
"""

import re
import unicodedata
from typing import Dict, List, Tuple, Set
from keywords_pci_dss_americas import PCI_COMPLIANCE_SIGNALS


def normalize_text(text):
    """Remove accents and normalize text for matching"""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


class PCIComplianceDetector:
    """
    PCI Compliance Signal Detection System
    Detects primary and secondary PCI signals with high accuracy
    """
    
    def __init__(self):
        self.primary_pci_signals = PCI_COMPLIANCE_SIGNALS["primary"]
        self.secondary_pci_signals = PCI_COMPLIANCE_SIGNALS["secondary"]
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for efficient matching"""
        # Primary PCI signals - exact phrase matching with punctuation handling
        self.primary_patterns = []
        for signal in self.primary_pci_signals:
            # Create pattern for both accented and non-accented versions
            normalized_signal = normalize_text(signal)
            pattern = re.compile(
                r'\b' + re.escape(normalized_signal) + r'\b',
                re.IGNORECASE | re.UNICODE
            )
            self.primary_patterns.append((signal, pattern))  # Store original and pattern
        
        # Secondary PCI signals - version detection and technical terms
        self.secondary_patterns = []
        for signal in self.secondary_pci_signals:
            normalized_signal = normalize_text(signal)
            pattern = re.compile(
                r'\b' + re.escape(normalized_signal) + r'\b',
                re.IGNORECASE | re.UNICODE
            )
            self.secondary_patterns.append((signal, pattern))  # Store original and pattern
        
        # Special version patterns for better accuracy (already normalized)
        self.version_patterns = [
            re.compile(r'\bpci\s*dss\s*[vV]?4\.0\b', re.IGNORECASE),
            re.compile(r'\bpci\s*dss\s*[vV]?4\.0\.1\b', re.IGNORECASE),
            re.compile(r'\b[vV]?4\.0(\.1)?\s*(?=pci|dss|compliance)', re.IGNORECASE)
        ]
    
    def detect_primary_signals(self, text: str) -> Dict[str, List[Tuple[str, int]]]:
        """
        Detect primary PCI signals with 100% accuracy target
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with detected signals and their positions
        """
        detected = {"signals": [], "positions": []}
        
        # Normalize the input text for matching
        normalized_text = normalize_text(text)
        
        for original_signal, pattern in self.primary_patterns:
            matches = pattern.finditer(normalized_text)
            for match in matches:
                position = match.start()
                detected["signals"].append(original_signal)  # Return original with accents
                detected["positions"].append((original_signal, position))
        
        return detected
    
    def detect_secondary_signals(self, text: str) -> Dict[str, List[Tuple[str, int]]]:
        """
        Detect secondary PCI signals with >95% accuracy target
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with detected signals and their positions
        """
        detected = {"signals": [], "positions": []}
        
        # Normalize the input text for matching
        normalized_text = normalize_text(text)
        
        # Check regular secondary patterns
        for original_signal, pattern in self.secondary_patterns:
            matches = pattern.finditer(normalized_text)
            for match in matches:
                position = match.start()
                detected["signals"].append(original_signal)  # Return original with accents
                detected["positions"].append((original_signal, position))
        
        # Check special version patterns (work on normalized text)
        for pattern in self.version_patterns:
            matches = pattern.finditer(normalized_text)
            for match in matches:
                version_text = match.group()
                position = match.start()
                detected["signals"].append(version_text)
                detected["positions"].append((version_text, position))
        
        return detected
    
    def calculate_pci_score(self, text: str) -> Dict[str, float]:
        """
        Calculate PCI compliance score based on detected signals
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with detailed scoring information
        """
        primary_results = self.detect_primary_signals(text)
        secondary_results = self.detect_secondary_signals(text)
        
        # Scoring weights
        primary_weight = 3.0
        secondary_weight = 1.0
        version_weight = 1.5
        
        primary_score = len(primary_results["signals"]) * primary_weight
        secondary_score = len(secondary_results["signals"]) * secondary_weight
        
        # Bonus for version detection
        version_bonus = 0
        for signal, _ in secondary_results["positions"]:
            if any(version in signal.lower() for version in ["4.0", "v4", "4.0.1"]):
                version_bonus += version_weight
        
        total_score = primary_score + secondary_score + version_bonus
        
        return {
            "total_score": total_score,
            "primary_score": primary_score,
            "secondary_score": secondary_score,
            "version_bonus": version_bonus,
            "primary_signals": primary_results["signals"],
            "secondary_signals": secondary_results["signals"],
            "has_primary_pci": len(primary_results["signals"]) > 0,
            "has_secondary_pci": len(secondary_results["signals"]) > 0
        }
    
    def validate_detection_accuracy(self, test_cases: List[Dict]) -> Dict[str, float]:
        """
        Validate detection accuracy against test cases
        
        Args:
            test_cases: List of test cases with expected results
            
        Returns:
            Accuracy metrics
        """
        total_tests = len(test_cases)
        primary_correct = 0
        secondary_correct = 0
        
        for test_case in test_cases:
            text = test_case["text"]
            expected_primary = test_case.get("expected_primary", [])
            expected_secondary = test_case.get("expected_secondary", [])
            
            primary_results = self.detect_primary_signals(text)
            secondary_results = self.detect_secondary_signals(text)
            
            # Check primary accuracy
            detected_primary = set(primary_results["signals"])
            expected_primary_set = set(expected_primary)
            
            if detected_primary == expected_primary_set:
                primary_correct += 1
            
            # Check secondary accuracy (allowing some flexibility)
            detected_secondary = set(secondary_results["signals"])
            expected_secondary_set = set(expected_secondary)
            
            # Calculate intersection over union for secondary
            if expected_secondary_set:
                iou = len(detected_secondary & expected_secondary_set) / len(detected_secondary | expected_secondary_set)
                if iou >= 0.95:  # 95% accuracy threshold
                    secondary_correct += 1
        
        return {
            "primary_accuracy": primary_correct / total_tests if total_tests > 0 else 0,
            "secondary_accuracy": secondary_correct / total_tests if total_tests > 0 else 0,
            "total_tests": total_tests
        }


def main():
    """Test the PCI compliance detection system"""
    detector = PCIComplianceDetector()
    
    # Test cases
    test_texts = [
        "This tender requires PCI DSS v4.0 compliance for payment processing Dados de cartão",
        "The system must handle Cardholder Data (CHD) according to PCI-DSS standards",
        "Procesamiento de pagos con Gateway de pagos certified PCI DSS 4.0.1",
        "Regular business document without PCI references",
        "Payment card data protection following Payment Card Industry requirements",
        "Sistema para Tarjetahabiente con Datos de tarjeta y procesamiento de pagos"
    ]
    
    print("PCI Compliance Signal Detection Test")
    print("=" * 50)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: {text[:60]}...")
        score = detector.calculate_pci_score(text)
        
        print(f"  Primary signals: {score['primary_signals']}")
        print(f"  Secondary signals: {score['secondary_signals']}")
        print(f"  Total PCI score: {score['total_score']:.2f}")
        print(f"  Has primary PCI: {score['has_primary_pci']}")
        print(f"  Has secondary PCI: {score['has_secondary_pci']}")


if __name__ == "__main__":
    main()
