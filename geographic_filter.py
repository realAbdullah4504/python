"""
Geographic Domain Filtering System for PCI DSS Tender Detection
Implements domain whitelist for allowed regions and blacklist for USA federal sites
"""

import re
from urllib.parse import urlparse
from typing import Optional, List, Tuple

# Import domain configurations from keywords file
from keywords_pci_dss_americas import APPROVED_DOMAINS, EXCLUDED_DOMAINS


class GeographicFilter:
    """
    Geographic domain filtering system for tender detection.
    Filters URLs based on approved domains and excluded domains.
    """
    
    def __init__(self):
        self.approved_domains = APPROVED_DOMAINS
        self.excluded_domains = EXCLUDED_DOMAINS
        self.approved_patterns = self._compile_domain_patterns(self.approved_domains)
        self.excluded_patterns = self._compile_domain_patterns(self.excluded_domains)
    
    def _compile_domain_patterns(self, domains: List[str]) -> List[re.Pattern]:
        """Compile regex patterns for domain matching"""
        patterns = []
        for domain in domains:
            # Escape special regex characters and create pattern
            escaped_domain = re.escape(domain)
            pattern = re.compile(rf'.*{escaped_domain}.*', re.IGNORECASE)
            patterns.append(pattern)
        return patterns
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return None
    
    def _is_approved_domain(self, domain: str) -> bool:
        """Check if domain matches any approved domain pattern"""
        for pattern in self.approved_patterns:
            if pattern.match(domain):
                return True
        return False
    
    def _is_excluded_domain(self, domain: str) -> bool:
        """Check if domain matches any excluded domain pattern"""
        for pattern in self.excluded_patterns:
            if pattern.match(domain):
                return True
        return False
    
    def is_url_allowed(self, url: str) -> Tuple[bool, str]:
        """
        Check if URL is allowed based on geographic filtering rules.
        
        Args:
            url: URL to check
            
        Returns:
            Tuple of (is_allowed, reason)
        """
        domain = self._extract_domain(url)
        
        if not domain:
            return False, "Invalid URL or unable to extract domain"
        
        # First check if domain is excluded
        if self._is_excluded_domain(domain):
            return False, f"Domain excluded: {domain}"
        
        # Then check if domain is approved
        if self._is_approved_domain(domain):
            return True, f"Domain approved: {domain}"
        
        # If neither approved nor explicitly excluded, deny by default
        return False, f"Domain not in approved list: {domain}"
    
    def filter_urls(self, urls: List[str]) -> List[Tuple[str, bool, str]]:
        """
        Filter a list of URLs based on geographic rules.
        
        Args:
            urls: List of URLs to filter
            
        Returns:
            List of tuples (url, is_allowed, reason)
        """
        results = []
        for url in urls:
            is_allowed, reason = self.is_url_allowed(url)
            results.append((url, is_allowed, reason))
        return results
    
    def get_allowed_urls(self, urls: List[str]) -> List[str]:
        """
        Get only the allowed URLs from a list.
        
        Args:
            urls: List of URLs to filter
            
        Returns:
            List of allowed URLs
        """
        filtered_results = self.filter_urls(urls)
        return [url for url, is_allowed, _ in filtered_results if is_allowed]
    
    def get_filtering_stats(self, urls: List[str]) -> dict:
        """
        Get statistics about URL filtering.
        
        Args:
            urls: List of URLs to analyze
            
        Returns:
            Dictionary with filtering statistics
        """
        filtered_results = self.filter_urls(urls)
        allowed_count = sum(1 for _, is_allowed, _ in filtered_results if is_allowed)
        denied_count = len(urls) - allowed_count
        
        # Group denial reasons
        denial_reasons = {}
        for url, is_allowed, reason in filtered_results:
            if not is_allowed:
                denial_reasons[reason] = denial_reasons.get(reason, 0) + 1
        
        return {
            'total_urls': len(urls),
            'allowed_urls': allowed_count,
            'denied_urls': denied_count,
            'allowance_rate': allowed_count / len(urls) if urls else 0,
            'denial_reasons': denial_reasons
        }


# Test cases and validation
def test_geographic_filter():
    """Test the geographic filtering system"""
    filter_system = GeographicFilter()
    
    # Test URLs
    test_urls = [
        "https://www.argentina.gob.ar/licitaciones",
        "https://comprasnet.gov.br/licitacoes",
        "https://sam.gov/content/home",
        "https://www.federalregister.gov/",
        "https://www.example.com/tender",
        "https://contratacionespublicas.gob.cl/",
        "https://usaspending.gov/search/",
        "https://www.gob.mx/tramites",
        "invalid-url"
    ]
    
    print("Geographic Filter Test Results:")
    print("=" * 50)
    
    results = filter_system.filter_urls(test_urls)
    for url, is_allowed, reason in results:
        status = "ALLOWED" if is_allowed else "DENIED"
        print(f"{status}: {url}")
        print(f"  Reason: {reason}")
        print()
    
    # Show statistics
    stats = filter_system.get_filtering_stats(test_urls)
    print("Filtering Statistics:")
    print(f"Total URLs: {stats['total_urls']}")
    print(f"Allowed: {stats['allowed_urls']}")
    print(f"Denied: {stats['denied_urls']}")
    print(f"Allowance Rate: {stats['allowance_rate']:.2%}")
    print("Denial Reasons:")
    for reason, count in stats['denial_reasons'].items():
        print(f"  {reason}: {count}")


if __name__ == "__main__":
    test_geographic_filter()
