"""
Test script for website language detection
"""

from language_detector import WebsiteLanguageDetector
import json

def test_language_detection():
    """Test the language detector with sample URLs"""
    detector = WebsiteLanguageDetector(verify_ssl=False)
    
    # Test with different types of websites
    test_urls = [
        "https://comprar.gob.ar/"         # Basic English site
    ]
    
    print("Testing Website Language Detection")
    print("=" * 40)
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        result = detector.detect_website_language(url)
        
        if result['error']:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Language: {result.get('language_name', 'Unknown')}")
            print(f"   Code: {result['detected_language']}")
            print(f"   Confidence: {result['confidence']:.2f}")
            print(f"   Methods: {', '.join(result['detection_methods'])}")
            
            # Show encoding analysis if available
            if result['encoding_analysis'].get('has_non_ascii'):
                print("   Non-ASCII chars: Yes")
                if result['encoding_analysis']['unicode_ranges']:
                    print(f"   Unicode ranges: {', '.join(result['encoding_analysis']['unicode_ranges'])}")

def interactive_test():
    """Interactive test for user input"""
    detector = WebsiteLanguageDetector(verify_ssl=False)
    
    print("\nInteractive Language Detection")
    print("Enter a website URL to detect its language (or 'quit' to exit):")
    
    while True:
        url = input("\nURL: ").strip()
        
        if url.lower() in ['quit', 'exit', 'q']:
            break
        
        if not url:
            continue
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        print(f"Analyzing {url}...")
        result = detector.detect_website_language(url)
        
        if result['error']:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Detected Language: {result.get('language_name', 'Unknown')}")
            print(f"   Language Code: {result['detected_language']}")
            print(f"   Confidence: {result['confidence']:.2f}")
            print(f"   Detection Methods: {', '.join(result['detection_methods'])}")
            
            # Show detailed analysis
            print("\n   Detailed Analysis:")
            for method, data in result['all_candidates'].items():
                print(f"   - {method}: {data['language']} (confidence: {data['confidence']:.1f})")

if __name__ == "__main__":
    # Run basic tests
    test_language_detection()
    
    # Then run interactive mode
    interactive_test()
