"""
STEP 4: Noise Exclusion System Implementation
Filters to eliminate non-tender content with <1% false positive rate
"""

import re
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse
from keywords_pci_dss_americas import NOISE_EXCLUSION_LIST


class NoiseExclusionSystem:
    """
    Noise Exclusion System for filtering non-tender content
    Implements immediate disqualification for noise terms
    """
    
    def __init__(self):
        self.noise_keywords = NOISE_EXCLUSION_LIST
        
        # Compile regex patterns for efficiency
        self._compile_noise_patterns()
        
        # URL patterns for common non-tender sites
        self.excluded_url_patterns = [
            r'blog\.',
            r'news\.',
            r'jobs?\.',
            r'careers?\.',
            r'training\.',
            r'education\.',
            r'webinar\.',
            r'course\.',
            r'academy\.',
            r'university\.',
            r'school\.',
            r'medium\.com',
            r'linkedin\.com/learning',
            r'youtube\.com',
            r'udemy\.com',
            r'coursera\.org',
            r'edx\.org'
        ]
        
        # Meta-tag patterns for non-tender content
        self.excluded_meta_patterns = [
            r'article',
            r'blog',
            r'news',
            r'press.?release',
            r'hiring',
            r'job.?posting',
            r'training',
            r'webinar',
            r'course',
            r'educational',
            r'tutorial',
            r'guide'
        ]
        
        # Author/Source exclusion patterns
        self.excluded_author_patterns = [
            r'training\s+provider',
            r'educational\s+institution',
            r'news\s+outlet',
            r'media\s+company',
            r'blog\s+author',
            r'content\s+creator'
        ]
    
    def _compile_noise_patterns(self):
        """Pre-compile noise keyword patterns for efficient matching"""
        self.noise_patterns = {}
        
        for language, keywords in self.noise_keywords.items():
            patterns = []
            for keyword in keywords:
                # Handle variations: singular, plural, possessive
                base_pattern = re.escape(keyword)
                pattern_variations = [
                    rf'\b{base_pattern}s?\b',  # singular/plural
                    rf'\b{base_pattern}\'?s?\b'  # handle possessive
                ]
                
                # Compile case-insensitive pattern
                compiled_pattern = re.compile(
                    '|'.join(pattern_variations),
                    re.IGNORECASE | re.UNICODE
                )
                patterns.append(compiled_pattern)
            
            self.noise_patterns[language] = patterns
    
    def detect_noise_terms(self, text: str, language: str = None) -> Dict[str, List[Tuple[str, int]]]:
        """
        Detect noise terms in text with immediate disqualification logic
        
        Args:
            text: Text to analyze
            language: Specific language to check (None for all languages)
            
        Returns:
            Dictionary with detected noise terms and positions
        """
        detected = {"terms": [], "positions": [], "languages": set()}
        
        languages_to_check = [language] if language else self.noise_keywords.keys()
        
        for lang in languages_to_check:
            if lang not in self.noise_patterns:
                continue
                
            for i, pattern in enumerate(self.noise_patterns[lang]):
                matches = pattern.finditer(text)
                for match in matches:
                    term = self.noise_keywords[lang][i]
                    position = match.start()
                    detected["terms"].append(term)
                    detected["positions"].append((term, position, lang))
                    detected["languages"].add(lang)
        
        # Convert set to list for JSON serialization
        detected["languages"] = list(detected["languages"])
        
        return detected
    
    def is_excluded_url(self, url: str) -> Dict[str, bool]:
        """
        Check if URL matches exclusion patterns
        
        Args:
            url: URL to check
            
        Returns:
            Dictionary with exclusion results
        """
        if not url:
            return {"excluded": False, "reason": "No URL provided"}
        
        try:
            parsed_url = urlparse(url.lower())
            domain = parsed_url.netloc
            path = parsed_url.path
            
            # Check domain patterns
            for pattern in self.excluded_url_patterns:
                if re.search(pattern, domain):
                    return {
                        "excluded": True,
                        "reason": f"Domain matches exclusion pattern: {pattern}",
                        "pattern": pattern
                    }
            
            # Check path patterns
            for pattern in self.excluded_url_patterns:
                if re.search(pattern, path):
                    return {
                        "excluded": True,
                        "reason": f"Path matches exclusion pattern: {pattern}",
                        "pattern": pattern
                    }
            
        except Exception as e:
            return {"excluded": False, "reason": f"URL parsing error: {str(e)}"}
        
        return {"excluded": False, "reason": "URL not excluded"}
    
    def check_meta_tags(self, meta_content: str) -> Dict[str, List[str]]:
        """
        Check meta tags for exclusion patterns
        
        Args:
            meta_content: Meta tag content (title, description, etc.)
            
        Returns:
            Dictionary with detected exclusion patterns
        """
        detected = {"patterns": [], "matches": []}
        
        if not meta_content:
            return detected
        
        for pattern in self.excluded_meta_patterns:
            if re.search(pattern, meta_content, re.IGNORECASE):
                detected["patterns"].append(pattern)
                detected["matches"].append(pattern)
        
        return detected
    
    def check_author_source(self, author_content: str) -> Dict[str, List[str]]:
        """
        Check author/source information for exclusion patterns
        
        Args:
            author_content: Author or source information
            
        Returns:
            Dictionary with detected exclusion patterns
        """
        detected = {"patterns": [], "matches": []}
        
        if not author_content:
            return detected
        
        for pattern in self.excluded_author_patterns:
            if re.search(pattern, author_content, re.IGNORECASE):
                detected["patterns"].append(pattern)
                detected["matches"].append(pattern)
        
        return detected
    
    def should_exclude_content(self, 
                             text: str = None,
                             url: str = None,
                             meta_tags: Dict[str, str] = None,
                             author: str = None) -> Dict[str, any]:
        """
        Comprehensive check if content should be excluded
        
        Args:
            text: Main content text
            url: Content URL
            meta_tags: Dictionary of meta tags (title, description, etc.)
            author: Author or source information
            
        Returns:
            Dictionary with exclusion decision and reasons
        """
        exclusion_reasons = []
        should_exclude = False
        
        # Check noise terms in main text
        if text:
            noise_results = self.detect_noise_terms(text)
            if noise_results["terms"]:
                should_exclude = True
                exclusion_reasons.append({
                    "type": "noise_terms",
                    "reason": f"Found {len(noise_results['terms'])} noise terms",
                    "details": noise_results["terms"][:5]  # Show first 5
                })
        
        # Check URL exclusion
        if url:
            url_results = self.is_excluded_url(url)
            if url_results["excluded"]:
                should_exclude = True
                exclusion_reasons.append({
                    "type": "url_exclusion",
                    "reason": url_results["reason"]
                })
        
        # Check meta tags
        if meta_tags:
            for tag_name, tag_content in meta_tags.items():
                meta_results = self.check_meta_tags(tag_content)
                if meta_results["patterns"]:
                    should_exclude = True
                    exclusion_reasons.append({
                        "type": "meta_exclusion",
                        "reason": f"Meta tag '{tag_name}' contains exclusion patterns",
                        "details": meta_results["patterns"]
                    })
        
        # Check author/source
        if author:
            author_results = self.check_author_source(author)
            if author_results["patterns"]:
                should_exclude = True
                exclusion_reasons.append({
                    "type": "author_exclusion",
                    "reason": "Author/source matches exclusion patterns",
                    "details": author_results["patterns"]
                })
        
        return {
            "should_exclude": should_exclude,
            "exclusion_reasons": exclusion_reasons,
            "confidence": 1.0 if should_exclude else 0.0  # Binary decision
        }
    
    def validate_false_positive_rate(self, test_cases: List[Dict]) -> Dict[str, float]:
        """
        Validate false positive rate on test dataset
        
        Args:
            test_cases: List of test cases with expected exclusion status
            
        Returns:
            False positive rate metrics
        """
        total_tests = len(test_cases)
        false_positives = 0
        false_negatives = 0
        true_positives = 0
        true_negatives = 0
        
        for test_case in test_cases:
            text = test_case.get("text", "")
            url = test_case.get("url")
            meta_tags = test_case.get("meta_tags", {})
            author = test_case.get("author")
            expected_exclude = test_case.get("should_exclude", False)
            
            result = self.should_exclude_content(text, url, meta_tags, author)
            actual_exclude = result["should_exclude"]
            
            if expected_exclude and actual_exclude:
                true_positives += 1
            elif not expected_exclude and not actual_exclude:
                true_negatives += 1
            elif not expected_exclude and actual_exclude:
                false_positives += 1
            elif expected_exclude and not actual_exclude:
                false_negatives += 1
        
        false_positive_rate = false_positives / total_tests if total_tests > 0 else 0
        false_negative_rate = false_negatives / total_tests if total_tests > 0 else 0
        accuracy = (true_positives + true_negatives) / total_tests if total_tests > 0 else 0
        
        return {
            "false_positive_rate": false_positive_rate,
            "false_negative_rate": false_negative_rate,
            "accuracy": accuracy,
            "total_tests": total_tests,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "true_positives": true_positives,
            "true_negatives": true_negatives
        }


def main():
    """Test the noise exclusion system"""
    noise_system = NoiseExclusionSystem()
    
    # Test cases
    test_cases = [
        {
            "text": "This is a training course about PCI compliance",
            "url": "https://blog.example.com/pci-training",
            "should_exclude": True
        },
        {
            "text": "Official tender notice for PCI DSS compliance services",
            "url": "https://www.gob.mx/licitacion-pci-dss",
            "should_exclude": False
        },
        {
            "text": "Webinar announcement: Understanding Payment Card Industry standards",
            "meta_tags": {"title": "Free PCI DSS Webinar", "description": "Educational content"},
            "should_exclude": True
        },
        {
            "text": "Licitación Pública para servicios de certificación PCI DSS",
            "url": "https://www.argentina.gob.ar/contrataciones",
            "should_exclude": False
        }
    ]
    
    print("Noise Exclusion System Test")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Text: {test_case['text'][:50]}...")
        print(f"  URL: {test_case.get('url', 'N/A')}")
        print(f"  Expected Exclude: {test_case['should_exclude']}")
        
        result = noise_system.should_exclude_content(
            text=test_case.get("text"),
            url=test_case.get("url"),
            meta_tags=test_case.get("meta_tags"),
            author=test_case.get("author")
        )
        
        print(f"  Actual Exclude: {result['should_exclude']}")
        print(f"  Match: {'✓' if result['should_exclude'] == test_case['should_exclude'] else '✗'}")
        
        if result["exclusion_reasons"]:
            print("  Reasons:")
            for reason in result["exclusion_reasons"]:
                print(f"    - {reason['type']}: {reason['reason']}")
    
    # Validate false positive rate
    validation_results = noise_system.validate_false_positive_rate(test_cases)
    print(f"\nValidation Results:")
    print(f"  False Positive Rate: {validation_results['false_positive_rate']:.2%}")
    print(f"  Accuracy: {validation_results['accuracy']:.2%}")


if __name__ == "__main__":
    main()
