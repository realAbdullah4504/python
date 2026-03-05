# Website Language Detection Script

This script provides comprehensive language detection for websites using multiple detection methods.

## Features

- **HTML lang attribute detection**: Checks `<html lang="...">` tags
- **Meta tags analysis**: Analyzes various meta tags for language information
- **HTTP headers detection**: Checks `Content-Language` headers
- **Content-based detection**: Uses `langdetect` library for text analysis
- **Character encoding analysis**: Analyzes Unicode ranges for language hints
- **Confidence scoring**: Provides confidence scores for detection results

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from language_detector import WebsiteLanguageDetector

detector = WebsiteLanguageDetector()
result = detector.detect_website_language('https://example.com')

print(f"Language: {result.get('language_name', 'Unknown')}")
print(f"Code: {result['detected_language']}")
print(f"Confidence: {result['confidence']:.2f}")
```

### Batch Processing

```python
urls = [
    'https://www.google.com',
    'https://www.bbc.com',
    'https://www.elmundo.es'
]

results = detector.batch_detect_languages(urls)
for result in results:
    print(f"{result['url']} -> {result.get('language_name', 'Unknown')}")
```

### Interactive Testing

Run the test script for interactive testing:

```bash
python test_language_detector.py
```

### Command Line Usage

Run the main script directly:

```bash
python language_detector.py
```

## Output Format

The detection result is a dictionary containing:

```json
{
    "url": "https://example.com",
    "detected_language": "en",
    "language_name": "English",
    "confidence": 0.9,
    "detection_methods": ["html_lang (0.9)", "content_analysis (0.8)"],
    "all_candidates": {
        "html_lang": {"language": "en", "confidence": 0.9},
        "content_analysis": {"language": "en", "confidence": 0.8}
    },
    "encoding_analysis": {
        "has_non_ascii": false,
        "unicode_ranges": [],
        "likely_languages": []
    }
}
```

## Supported Languages

The script supports detection of major world languages including:

- English (en)
- Spanish (es)
- Portuguese (pt)
- French (fr)
- German (de)
- Italian (it)
- Dutch (nl)
- Japanese (ja)
- Chinese (zh)
- Korean (ko)
- Russian (ru)
- Arabic (ar)
- And many more...

## Detection Methods

1. **HTML lang attribute** (confidence: 0.9) - Most reliable
2. **Content analysis** (confidence: 0.8) - Text-based detection
3. **Meta tags** (confidence: 0.7) - Various meta tags
4. **HTTP headers** (confidence: 0.6) - Content-Language header
5. **Encoding analysis** (confidence: 0.4) - Unicode range analysis

## Error Handling

The script includes comprehensive error handling for:
- Network connectivity issues
- Invalid URLs
- Encoding problems
- Parsing errors
- Insufficient text content

## Logging

The script uses Python's logging module for debugging and monitoring. Logs are written to console output.

## Performance

- Single URL detection: ~1-2 seconds
- Batch processing: Optimized for multiple URLs
- Memory efficient: Processes one URL at a time

## Dependencies

- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `langdetect` - Language detection from text
- `charset-normalizer` - Character encoding detection
