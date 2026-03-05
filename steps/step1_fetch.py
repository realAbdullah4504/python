"""
STEP 1: Environment and Data Collection Setup
PCI DSS Tender Detection System - Americas Region (Excluding USA)

This module implements:
1. Geographic filtering system (domain whitelist/blacklist)
2. Keyword database loading and validation
3. Data collection pipeline with web scraping
4. Language detection for content processing
"""

import requests
import urllib3
import re
import json
import time
import logging
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import sys
import os

# Add parent directory to path for importing keywords
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from keywords_pci_dss_americas import (
    APPROVED_DOMAINS, EXCLUDED_DOMAINS, NOISE_EXCLUSION_TERMS,
    STRONG_PROCUREMENT_TRIGGERS, STRUCTURAL_PROCUREMENT_MARKERS,
    ADDITIONAL_PROCUREMENT_TERMS, PCI_PRIMARY_SIGNALS, PCI_SECONDARY_SIGNALS,
    PAYMENT_PROCESSING_TERMS, SCORING_CONFIG
)

# Disable SSL warnings for development (not recommended for production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('step1_fetch.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GeographicFilter:
    """Handles geographic and domain-based filtering"""
    
    def __init__(self):
        self.approved_domains = APPROVED_DOMAINS
        self.excluded_domains = EXCLUDED_DOMAINS
        
    def is_domain_approved(self, url: str) -> bool:
        """Check if domain is in approved list"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check if domain ends with any approved TLD
            for approved in self.approved_domains:
                if domain.endswith(approved.lower()):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error parsing URL {url}: {e}")
            return False
    
    def is_domain_excluded(self, url: str) -> bool:
        """Check if domain should be excluded"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check if domain contains any excluded patterns
            for excluded in self.excluded_domains:
                if excluded in domain:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error parsing URL {url}: {e}")
            return False
    
    def is_geographically_valid(self, url: str) -> Tuple[bool, str]:
        """Comprehensive geographic validation"""
        if not self.is_domain_approved(url):
            return False, "Domain not in approved geographic regions"
        
        if self.is_domain_excluded(url):
            return False, "Domain excluded (USA federal sites)"
        
        return True, "Geographic validation passed"

class LanguageDetector:
    """Detects content language for proper keyword matching"""
    
    def __init__(self):
        self.language_patterns = {
            'spanish': re.compile(r'\b(el|la|los|las|un|una|unos|unas|de|del|en|y|o|pero|que|quien|cual|cuándo|dónde|por qué|cómo|es|son|está|están|fue|fueron|será|serán|ha|han|había|habían|lic|licitación|convocatoria|pliego)\b', re.IGNORECASE),
            'portuguese': re.compile(r'\b(o|a|os|as|um|uma|uns|umas|de|do|da|dos|das|em|e|ou|mas|que|quem|qual|quando|onde|por que|como|é|são|está|estão|foi|foram|será|serão|tem|têm|tinha|tinham|licitação|edital|pregão)\b', re.IGNORECASE),
            'english': re.compile(r'\b(the|and|or|but|in|on|at|to|for|of|with|by|from|up|about|into|through|during|before|after|above|below|between|among|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|could|should|may|might|must|can|tender|procurement|rfp|rfq)\b', re.IGNORECASE)
        }
    
    def detect_language(self, text: str) -> str:
        """Detect primary language of content"""
        if not text or len(text.strip()) < 50:
            return 'english'  # Default fallback
        
        scores = {}
        for lang, pattern in self.language_patterns.items():
            matches = pattern.findall(text.lower())
            scores[lang] = len(matches)
        
        # Return language with highest score
        if scores:
            detected_lang = max(scores, key=scores.get)
            confidence = scores[detected_lang] / len(text.split()) if text.split() else 0
            
            logger.info(f"Language detected: {detected_lang} (confidence: {confidence:.2f})")
            return detected_lang
        
        return 'english'  # Default fallback

class ContentExtractor:
    """Handles web content extraction and cleaning"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_content(self, url: str, timeout: int = 30) -> Optional[Tuple[str, Dict]]:
        """Fetch and extract content from URL"""
        try:
            logger.info(f"Fetching content from: {url}")
            
            response = self.session.get(url, verify=False, timeout=timeout)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract main content
            main_content = ""
            
            # Try to find main content areas
            for selector in ['main', 'article', '.content', '#content', '.main-content']:
                main_elem = soup.select_one(selector)
                if main_elem:
                    main_content = main_elem.get_text(separator=' ', strip=True)
                    break
            
            # Fallback to body if no main content found
            if not main_content:
                main_content = soup.get_text(separator=' ', strip=True)
            
            # Clean up text
            main_content = re.sub(r'\s+', ' ', main_content).strip()
            
            # Extract metadata
            metadata = {
                'title': soup.title.string if soup.title else '',
                'status_code': response.status_code,
                'content_length': len(main_content),
                'content_type': response.headers.get('content-type', ''),
                'fetch_time': time.time()
            }
            
            logger.info(f"Successfully extracted {len(main_content)} characters from {url}")
            return main_content, metadata
            
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing content from {url}: {e}")
            return None
    
    def save_content(self, url: str, content: str, metadata: Dict, output_dir: str = 'data'):
        """Save extracted content to file"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename from URL
            parsed = urlparse(url)
            filename = re.sub(r'[^a-zA-Z0-9]', '_', parsed.netloc + parsed.path)
            filename = filename[:100]  # Limit length
            timestamp = int(time.time())
            
            # Save content
            content_file = os.path.join(output_dir, f"{filename}_{timestamp}.txt")
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"Title: {metadata.get('title', '')}\n")
                f.write(f"Fetch Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(metadata.get('fetch_time', time.time())))}\n")
                f.write(f"Content Length: {metadata.get('content_length', 0)}\n")
                f.write("-" * 50 + "\n\n")
                f.write(content)
            
            # Save metadata
            metadata_file = os.path.join(output_dir, f"{filename}_{timestamp}_metadata.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            logger.info(f"Content saved to {content_file}")
            return content_file, metadata_file
            
        except Exception as e:
            logger.error(f"Error saving content: {e}")
            return None, None

class KeywordValidator:
    """Validates keyword databases and structure"""
    
    def __init__(self):
        self.required_categories = [
            'STRONG_PROCUREMENT_TRIGGERS',
            'STRUCTURAL_PROCUREMENT_MARKERS', 
            'PCI_PRIMARY_SIGNALS',
            'NOISE_EXCLUSION_TERMS'
        ]
    
    def validate_keyword_structure(self) -> Tuple[bool, List[str]]:
        """Validate all keyword databases are properly structured"""
        issues = []
        
        try:
            # Check each required category
            for category in self.required_categories:
                if not hasattr(sys.modules['keywords_pci_dss_americas'], category):
                    issues.append(f"Missing keyword category: {category}")
                    continue
                
                keywords = getattr(sys.modules['keywords_pci_dss_americas'], category)
                
                if not isinstance(keywords, dict):
                    issues.append(f"Category {category} is not a dictionary")
                    continue
                
                # Check for required languages
                required_languages = ['spanish', 'portuguese', 'english']
                for lang in required_languages:
                    if lang not in keywords:
                        issues.append(f"Missing language '{lang}' in category {category}")
                    elif not isinstance(keywords[lang], list):
                        issues.append(f"Language '{lang}' in category {category} is not a list")
                    elif len(keywords[lang]) == 0:
                        issues.append(f"Language '{lang}' in category {category} is empty")
            
            # Validate scoring configuration
            if not hasattr(sys.modules['keywords_pci_dss_americas'], 'SCORING_CONFIG'):
                issues.append("Missing SCORING_CONFIG")
            else:
                scoring = SCORING_CONFIG
                if 'procurement' not in scoring or 'pci' not in scoring:
                    issues.append("Incomplete scoring configuration")
            
            is_valid = len(issues) == 0
            
            if is_valid:
                logger.info("All keyword databases validated successfully")
            else:
                logger.error(f"Keyword validation found {len(issues)} issues")
                for issue in issues:
                    logger.error(f"  - {issue}")
            
            return is_valid, issues
            
        except Exception as e:
            logger.error(f"Error validating keywords: {e}")
            return False, [f"Validation error: {e}"]

class DataCollectionPipeline:
    """Main data collection pipeline orchestrating all components"""
    
    def __init__(self):
        self.geo_filter = GeographicFilter()
        self.lang_detector = LanguageDetector()
        self.content_extractor = ContentExtractor()
        self.keyword_validator = KeywordValidator()
        
    def validate_environment(self) -> bool:
        """Validate environment setup before starting"""
        logger.info("Validating environment setup...")
        
        # Validate keyword databases
        keywords_valid, keyword_issues = self.keyword_validator.validate_keyword_structure()
        if not keywords_valid:
            logger.error("Keyword validation failed - cannot proceed")
            return False
        
        # Test geographic filtering
        test_urls = [
            "https://comprar.gob.ar/",  # Should be approved
            "https://www.sam.gov/",     # Should be excluded
            "https://example.com/"      # Should be rejected
        ]
        
        for url in test_urls:
            is_valid, reason = self.geo_filter.is_geographically_valid(url)
            logger.info(f"Geographic test {url}: {is_valid} - {reason}")
        
        logger.info("Environment validation completed")
        return True
    
    def process_url(self, url: str) -> Optional[Dict]:
        """Process a single URL through the complete pipeline"""
        logger.info(f"Processing URL: {url}")
        
        # Step 1: Geographic validation
        geo_valid, geo_reason = self.geo_filter.is_geographically_valid(url)
        if not geo_valid:
            logger.warning(f"URL rejected by geographic filter: {geo_reason}")
            return None
        
        # Step 2: Content extraction
        content_result = self.content_extractor.fetch_content(url)
        if not content_result:
            logger.error(f"Failed to extract content from {url}")
            return None
        
        content, metadata = content_result
        
        # Step 3: Language detection
        detected_language = self.lang_detector.detect_language(content)
        metadata['detected_language'] = detected_language
        
        # Step 4: Save content
        content_file, metadata_file = self.content_extractor.save_content(url, content, metadata)
        
        # Step 5: Return processing results
        result = {
            'url': url,
            'status': 'success',
            'content_length': len(content),
            'language': detected_language,
            'content_file': content_file,
            'metadata_file': metadata_file,
            'metadata': metadata
        }
        
        logger.info(f"Successfully processed {url}")
        return result
    
    def process_urls_batch(self, urls: List[str]) -> List[Dict]:
        """Process multiple URLs in batch"""
        logger.info(f"Processing batch of {len(urls)} URLs")
        
        results = []
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing URL {i}/{len(urls)}")
            
            try:
                result = self.process_url(url)
                if result:
                    results.append(result)
                
                # Add delay to be respectful
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
                results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                })
        
        logger.info(f"Batch processing completed. Success: {len([r for r in results if r['status'] == 'success'])}, Errors: {len([r for r in results if r['status'] == 'error'])}")
        return results

def main():
    """Main execution function for Step 1"""
    logger.info("=" * 60)
    logger.info("STEP 1: Environment and Data Collection Setup")
    logger.info("=" * 60)
    
    # Initialize pipeline
    pipeline = DataCollectionPipeline()
    
    # Validate environment
    if not pipeline.validate_environment():
        logger.error("Environment validation failed. Exiting.")
        return
    
    # Test URLs from different regions
    test_urls = [
        "https://comprar.gob.ar/",           # Argentina
        "https://www.comprasnet.gov.br/",     # Brazil  
        "https://www.mercadopublico.cl/",    # Chile
        "https://compranet.hacienda.gob.mx/", # Mexico
    ]
    
    # Process test URLs
    results = pipeline.process_urls_batch(test_urls)
    
    # Generate summary report
    logger.info("=" * 60)
    logger.info("STEP 1 EXECUTION SUMMARY")
    logger.info("=" * 60)
    
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'error']
    
    logger.info(f"Total URLs processed: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info("Successful URLs:")
        for result in successful:
            logger.info(f"  - {result['url']} ({result['language']}, {result['content_length']} chars)")
    
    if failed:
        logger.warning("Failed URLs:")
        for result in failed:
            logger.warning(f"  - {result['url']}: {result.get('error', 'Unknown error')}")
    
    # Validation criteria check
    logger.info("=" * 60)
    logger.info("VALIDATION CRITERIA CHECK")
    logger.info("=" * 60)
    
    validation_passed = True
    
    # Check 1: Domain filtering excludes USA federal sites
    usa_test_url = "https://sam.gov/"
    is_excluded, reason = pipeline.geo_filter.is_geographically_valid(usa_test_url)
    if is_excluded:
        logger.error("❌ USA federal sites not properly excluded")
        validation_passed = False
    else:
        logger.info("✅ USA federal sites properly excluded")
    
    # Check 2: Language detection accuracy
    if successful:
        languages_detected = [r['language'] for r in successful]
        unique_languages = set(languages_detected)
        logger.info(f"✅ Languages detected: {unique_languages}")
    else:
        logger.warning("⚠️  No successful content extraction to validate language detection")
    
    # Check 3: Data pipeline functionality
    if len(successful) >= 1:
        logger.info("✅ Data pipeline successfully extracts content")
    else:
        logger.error("❌ Data pipeline failed to extract content")
        validation_passed = False
    
    if validation_passed:
        logger.info("🎉 STEP 1 VALIDATION PASSED - Ready for Step 2")
    else:
        logger.error("❌ STEP 1 VALIDATION FAILED - Fix issues before proceeding")

if __name__ == "__main__":
    main()