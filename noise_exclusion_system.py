"""
STEP 4: Noise Exclusion System Implementation
Minimal version for filtering non-tender content
"""

import re
from typing import Dict, List
from keywords_pci_dss_americas import NOISE_EXCLUSION_LIST


class NoiseExclusionSystem:
    """Minimal noise exclusion system"""
    
    def __init__(self):
        self.noise_keywords = NOISE_EXCLUSION_LIST
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile noise keyword patterns"""
        self.noise_patterns = {}
        for lang, keywords in self.noise_keywords.items():
            patterns = []
            for keyword in keywords:
                pattern = re.compile(r'\b' + re.escape(keyword) + r's?\b', re.IGNORECASE)
                patterns.append(pattern)
            self.noise_patterns[lang] = patterns
    
    def detect_noise_terms(self, text: str) -> List[str]:
        """Detect noise terms in text"""
        found_terms = []
        for lang, patterns in self.noise_patterns.items():
            for i, pattern in enumerate(patterns):
                if pattern.search(text):
                    found_terms.append(self.noise_keywords[lang][i])
        return found_terms
    
    def should_exclude_content(self, text: str = None) -> Dict:
        """Determine if content should be excluded based on noise terms only"""
        reasons = []
        should_exclude = False
        
        if text:
            noise_terms = self.detect_noise_terms(text)
            if noise_terms:
                should_exclude = True
                reasons.append(f"Found noise terms: {noise_terms}")
        
        return {
            "should_exclude": should_exclude,
            "reasons": reasons
        }


def main():
    """Test the minimal noise exclusion system"""
    system = NoiseExclusionSystem()
    
    test_cases = [
        {
            "text": "This is a training course about PCI compliance",
            "should_exclude": True
        },
        {
            "text": "Official tender notice for PCI DSS compliance services",
            "should_exclude": False
        },
        {
            "text": "Webinar announcement for payment card industry",
            "should_exclude": True
        }
    ]
    
    print("Minimal Noise Exclusion System Test")
    print("=" * 40)
    
    for i, test_case in enumerate(test_cases, 1):
        result = system.should_exclude_content(text=test_case.get("text"))
        
        print(f"\nTest {i}:")
        print(f"  Text: {test_case['text'][:40]}...")
        print(f"  Expected: {test_case['should_exclude']}")
        print(f"  Actual: {result['should_exclude']}")
        print(f"  Match: {'✓' if result['should_exclude'] == test_case['should_exclude'] else '✗'}")
        if result['reasons']:
            for reason in result['reasons']:
                print(f"  Reason: {reason}")


if __name__ == "__main__":
    main()
