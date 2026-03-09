"""
Website Language Detection Script

This script provides comprehensive language detection for websites using multiple methods:
1. HTML lang attribute detection
2. HTTP Content-Language header detection
3. Meta tags analysis
4. Content-based language detection using langdetect library
5. Character encoding analysis

Requirements:
- requests
- beautifulsoup4
- langdetect
- charset-normalizer
"""

import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import logging
from langdetect import detect, DetectorFactory
from charset_normalizer import from_bytes
import json
import urllib3

# Disable SSL warnings for development (not recommended for production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set seed for consistent results
DetectorFactory.seed = 0

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebsiteLanguageDetector:
    """Comprehensive website language detection system"""
    
    def __init__(self, verify_ssl: bool = False):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.verify_ssl = verify_ssl
        
        # Common language codes and their names
        self.language_codes = {
            'en': 'English',
            'es': 'Spanish',
            'pt': 'Portuguese',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'nl': 'Dutch',
            'ja': 'Japanese',
            'zh': 'Chinese',
            'ko': 'Korean',
            'ru': 'Russian',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'th': 'Thai',
            'vi': 'Vietnamese',
            'pl': 'Polish',
            'tr': 'Turkish',
            'sv': 'Swedish',
            'da': 'Danish',
            'no': 'Norwegian',
            'fi': 'Finnish'
        }
    
    def fetch_website_content(self, url: str) -> Tuple[Optional[str], Optional[Dict], Optional[str]]:
        """
        Fetch website content and return HTML, headers, and encoding
        
        Args:
            url: Website URL to analyze
            
        Returns:
            Tuple of (html_content, headers, encoding)
        """
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True, verify=self.verify_ssl)
            response.raise_for_status()
            
            # Get encoding from headers or content
            encoding = response.encoding or 'utf-8'
            
            # Try to detect encoding from content if needed
            if encoding == 'ISO-8859-1' or not encoding:
                detected = from_bytes(response.content)
                if detected.best():
                    encoding = detected.best().encoding
            
            # Decode content with detected encoding
            try:
                html_content = response.content.decode(encoding, errors='replace')
            except (UnicodeDecodeError, LookupError):
                html_content = response.content.decode('utf-8', errors='replace')
                encoding = 'utf-8'
            
            return html_content, dict(response.headers), encoding
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None, None, None
    
    def detect_html_lang_attribute(self, soup: BeautifulSoup) -> Optional[str]:
        """Detect language from HTML lang attribute"""
        # Check html tag
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            lang = html_tag.get('lang').strip().lower()
            if lang:
                return lang.split('-')[0]  # Return primary language code
        
        return None
    
    def detect_meta_language(self, soup: BeautifulSoup) -> List[str]:
        """Detect language from meta tags"""
        languages = []
        
        # Check various meta tags that might contain language information
        meta_selectors = [
            'meta[http-equiv="content-language"]',
            'meta[name="language"]',
            'meta[property="og:locale"]',
            'meta[name="dc.language"]'
        ]
        
        for selector in meta_selectors:
            meta_tags = soup.select(selector)
            for meta in meta_tags:
                content = meta.get('content', '').strip().lower()
                if content:
                    # Extract language code from content
                    lang_match = re.match(r'^([a-z]{2,3})', content)
                    if lang_match:
                        languages.append(lang_match.group(1))
                    else:
                        languages.append(content)
        
        return languages
    
    def detect_http_language(self, headers: Dict) -> List[str]:
        """Detect language from HTTP headers"""
        languages = []
        
        # Check Content-Language header
        content_lang = headers.get('content-language', '')
        if content_lang:
            # Extract language codes
            for lang in content_lang.split(','):
                lang = lang.strip().lower()
                lang_match = re.match(r'^([a-z]{2,3})', lang)
                if lang_match:
                    languages.append(lang_match.group(1))
        
        return languages
    
    def detect_content_language(self, text: str) -> Optional[str]:
        """Detect language from text content using langdetect"""
        try:
            # Clean text for better detection
            cleaned_text = re.sub(r'\s+', ' ', text)
            cleaned_text = re.sub(r'[^\w\s]', ' ', cleaned_text)
            cleaned_text = cleaned_text.strip()
            
            # Need minimum text for reliable detection
            if len(cleaned_text) < 50:
                return None
            
            # Detect language
            lang = detect(cleaned_text)
            return lang
            
        except Exception as e:
            logger.warning(f"Content language detection failed: {e}")
            return None
    
    def analyze_character_encoding(self, html_content: str) -> Dict[str, any]:
        """Analyze character encoding for language hints"""
        analysis = {
            'has_non_ascii': False,
            'unicode_ranges': [],
            'likely_languages': []
        }
        
        # Check for non-ASCII characters
        non_ascii_chars = re.findall(r'[^\x00-\x7F]', html_content)
        if non_ascii_chars:
            analysis['has_non_ascii'] = True
            
            # Analyze Unicode ranges for language hints
            char_ranges = set()
            for char in set(non_ascii_chars):
                code_point = ord(char)
                if 0x0600 <= code_point <= 0x06FF:  # Arabic
                    char_ranges.add('arabic')
                elif 0x0400 <= code_point <= 0x04FF:  # Cyrillic
                    char_ranges.add('cyrillic')
                elif 0x0590 <= code_point <= 0x05FF:  # Hebrew
                    char_ranges.add('hebrew')
                elif 0x4E00 <= code_point <= 0x9FFF:  # CJK Unified Ideographs
                    char_ranges.add('cjk')
                elif 0x3040 <= code_point <= 0x309F:  # Hiragana
                    char_ranges.add('japanese')
                elif 0x30A0 <= code_point <= 0x30FF:  # Katakana
                    char_ranges.add('japanese')
                elif 0xAC00 <= code_point <= 0xD7AF:  # Hangul
                    char_ranges.add('korean')
                elif 0x0E00 <= code_point <= 0x0E7F:  # Thai
                    char_ranges.add('thai')
            
            analysis['unicode_ranges'] = list(char_ranges)
            
            # Map ranges to likely languages
            range_to_lang = {
                'arabic': ['ar'],
                'cyrillic': ['ru', 'bg', 'uk', 'be'],
                'hebrew': ['he'],
                'cjk': ['zh', 'ja', 'ko'],
                'japanese': ['ja'],
                'korean': ['ko'],
                'thai': ['th']
            }
            
            likely_langs = set()
            for range_name in char_ranges:
                if range_name in range_to_lang:
                    likely_langs.update(range_to_lang[range_name])
            
            analysis['likely_languages'] = list(likely_langs)
        
        return analysis
    
    def detect_website_language(self, url: str) -> Dict[str, any]:
        """
        Comprehensive website language detection
        
        Args:
            url: Website URL to analyze
            
        Returns:
            Dictionary containing detection results and confidence scores
        """
        logger.info(f"Analyzing language for: {url}")
        
        result = {
            'url': url,
            'detected_language': None,
            'confidence': 0.0,
            'detection_methods': [],
            'all_candidates': {},
            'encoding_analysis': {},
            'error': None
        }
        
        # Fetch website content
        html_content, headers, _ = self.fetch_website_content(url)
        if not html_content:
            result['error'] = 'Failed to fetch website content'
            return result
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Collect all detection methods
            candidates = {}
            
            # 1. HTML lang attribute
            html_lang = self.detect_html_lang_attribute(soup)
            if html_lang:
                candidates['html_lang'] = {'language': html_lang, 'confidence': 0.9}
            
            # 2. Meta tags
            meta_langs = self.detect_meta_language(soup)
            for lang in meta_langs:
                if 'meta_tags' not in candidates:
                    candidates['meta_tags'] = {'language': lang, 'confidence': 0.7}
                else:
                    candidates['meta_tags']['confidence'] += 0.1
            
            # 3. HTTP headers
            if headers:
                http_langs = self.detect_http_language(headers)
                for lang in http_langs:
                    if 'http_headers' not in candidates:
                        candidates['http_headers'] = {'language': lang, 'confidence': 0.6}
                    else:
                        candidates['http_headers']['confidence'] += 0.1
            
            # 4. Content-based detection
            # Extract text content for analysis
            text_content = soup.get_text(separator=' ', strip=True)
            content_lang = self.detect_content_language(text_content)
            if content_lang:
                candidates['content_analysis'] = {'language': content_lang, 'confidence': 0.8}
            
            # 5. Character encoding analysis
            encoding_analysis = self.analyze_character_encoding(html_content)
            result['encoding_analysis'] = encoding_analysis
            
            # Add encoding-based candidates
            if encoding_analysis['likely_languages']:
                for lang in encoding_analysis['likely_languages']:
                    if 'encoding_analysis' not in candidates:
                        candidates['encoding_analysis'] = {'language': lang, 'confidence': 0.4}
                    else:
                        candidates['encoding_analysis']['confidence'] += 0.1
            
            # Determine final result
            if candidates:
                # Count language votes
                language_votes = {}
                method_details = {}
                
                for method, data in candidates.items():
                    lang = data['language']
                    conf = data['confidence']
                    
                    if lang not in language_votes:
                        language_votes[lang] = 0
                        method_details[lang] = []
                    
                    language_votes[lang] += conf
                    method_details[lang].append(f"{method} ({conf:.1f})")
                
                # Select language with highest confidence
                best_lang = max(language_votes, key=language_votes.get)
                best_confidence = language_votes[best_lang]
                
                result['detected_language'] = best_lang
                result['confidence'] = min(best_confidence, 1.0)
                result['detection_methods'] = method_details[best_lang]
                result['all_candidates'] = candidates
            
            # Add language name
            if result['detected_language']:
                lang_name = self.language_codes.get(result['detected_language'], 
                                                   result['detected_language'].upper())
                result['language_name'] = lang_name
            
        except Exception as e:
            logger.error(f"Error analyzing {url}: {e}")
            result['error'] = str(e)
        
        return result
    
    def batch_detect_languages(self, urls: List[str]) -> List[Dict[str, any]]:
        """Detect languages for multiple URLs"""
        results = []
        
        for url in urls:
            try:
                result = self.detect_website_language(url)
                results.append(result)
                
                # Log result
                if result['detected_language']:
                    logger.info(f"{url} -> {result['language_name']} ({result['confidence']:.2f})")
                else:
                    logger.warning(f"{url} -> Language detection failed")
                    
            except Exception as e:
                logger.error(f"Failed to process {url}: {e}")
                results.append({
                    'url': url,
                    'error': str(e),
                    'detected_language': None,
                    'confidence': 0.0
                })
        
        return results


def main():
    """Example usage of the language detector"""
    detector = WebsiteLanguageDetector()
    
    # Test URLs
    test_urls = [
        'https://www.google.com',
        'https://www.bbc.com',
        'https://www.elmundo.es',
        'https://www.lemonde.fr',
        'https://www.gov.br'
    ]
    
    print("Website Language Detection Results")
    print("=" * 50)
    
    results = detector.batch_detect_languages(test_urls)
    
    for result in results:
        print(f"\nURL: {result['url']}")
        
        if result['error']:
            print(f"Error: {result['error']}")
        else:
            print(f"Language: {result.get('language_name', 'Unknown')}")
            print(f"Code: {result['detected_language']}")
            print(f"Confidence: {result['confidence']:.2f}")
            print(f"Methods: {', '.join(result['detection_methods'])}")
    
    # Save detailed results to JSON
    with open('language_detection_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\nDetailed results saved to language_detection_results.json")


if __name__ == "__main__":
    main()
