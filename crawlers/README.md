# Tender Crawling System Documentation

## Overview

This is a modular, extensible web crawling system designed to extract tender information from various government and procurement portals. The system uses a strategy pattern to handle different portal types and structures, providing a unified interface for data collection and processing.

## Details Extraction System

The system includes a comprehensive details extraction framework for processing tender documents and web pages.

### Details Strategy Interface (`interfaces/details_strategy.py`)

The `IDetailsStrategy` abstract base class defines the contract for all details extraction strategies:

**Required Methods**:
- `extract_details()`: Extract details for a single tender
- `can_handle()`: Check if strategy can handle a tender
- `get_strategy_type()`: Return strategy identifier
- `filter_tenders()`: Filter tenders this strategy can process

**Common Methods**:
- `validate_tender()`: Validate tender has required fields
- `process_tender()`: Process tender with error handling

### Details Engine (`core/details_engine.py`)

The `DetailsEngine` class orchestrates details extraction workflow:

**Key Features**:
- Strategy registration and management
- Tender filtering by strategy type
- Unified processing interface
- Error handling and logging

**Main Methods**:
- `run()`: Execute complete details extraction workflow
- `process_tender()`: Process single tender with appropriate strategy
- `filter_tenders_by_strategy()`: Group tenders by processing strategy

### Available Details Strategies

#### PDF Details Strategy (`strategies/pdf_details_strategy.py`)

Handles extraction from PDF documents using both direct text extraction and OCR fallback.

**Features**:
- Direct PDF text extraction using PyPDF2
- OCR fallback for scanned PDFs using Tesseract
- PDF URL validation and downloading
- Configurable timeout settings

**Use Cases**:
- Portals with downloadable PDF documents
- Scanned tender documents requiring OCR
- Structured PDF files with embedded text

#### Postback Details Strategy (`strategies/postback_details_strategy.py`)

Handles extraction from web pages requiring postback navigation.

**Features**:
- Playwright-based web navigation
- Postback event simulation
- Pagination target extraction
- Browser context management

**Use Cases**:
- Portals with JavaScript-based navigation
- Sites requiring form submissions
- Multi-page tender listings

### Utility Components

#### PDF Text Extractor (`processors/pdf_text_extractor.py`)

Utility class for PDF processing:

**Features**:
- PDF download with timeout handling
- Direct text extraction from PDF bytes
- OCR processing for scanned documents
- Multi-language text extraction (Spanish, English)

#### Postback Navigator (`processors/postback_navigator.py`)

Utility class for web navigation:

**Features**:
- Browser context setup and cleanup
- Pagination target extraction
- Tender details navigation
- Postback event simulation

### Details Factory (`strategies/details_factory.py`)

Factory for creating details strategies based on configuration:

**Features**:
- Strategy registration and creation
- Portal configuration-based strategy selection
- Global factory instance for convenience

### Usage

#### Basic Details Extraction

```python
from crawlers.core.details_engine import DetailsEngine

# Initialize engine
engine = DetailsEngine()

# Run details extraction
result = engine.run()
print(f"Processed {result['processed']} tenders")
```

#### Strategy-Specific Processing

```python
from crawlers.strategies.details_factory import create_details_strategy

# Create specific strategy
pdf_strategy = create_details_strategy("pdf")

# Filter and process tenders
tenders = load_tenders_needing_details()
pdf_tenders = pdf_strategy.filter_tenders(tenders)

for tender in pdf_tenders:
    enriched_tender = pdf_strategy.process_tender(tender)
    update_tender_with_details(enriched_tender)
```

#### Command Line Interface

```bash
# Process all tenders with available strategies
python crawlers/crawl_details.py

# Process with specific strategy
python crawlers/crawl_details.py --strategy pdf

# Limit number of tenders
python crawlers/crawl_details.py --max-tenders 10

# List available strategies
python crawlers/crawl_details.py --list-strategies
```

### Backward Compatibility

The original scripts are preserved with modular backends:

- `crawl_details_pdf_modular.py`: PDF extraction using new modular system
- `crawl_details_postback_modular.py`: Postback extraction using new modular system

These maintain the original interface while using the new architecture.

### Configuration

Details extraction is configured through the existing portal configuration:

```json
{
  "portals": [
    {
      "name": "Portal Name",
      "config": {
        "details": {
          "type": "pdf|postback",
          "timeout": 60
        }
      }
    }
  ]
}
```

### Integration with Existing System

The details extraction system integrates seamlessly with the existing crawler architecture:

1. **Listing Crawling**: Main crawler extracts tender listings
2. **Details Extraction**: Details engine processes tenders needing details
3. **Unified Storage**: All data saved to standardized NDJSON format

### Error Handling

The system implements comprehensive error handling:

- **Strategy Selection**: Graceful fallback if strategy unavailable
- **Network Errors**: Retry logic and timeout handling
- **Processing Errors**: Individual tender failures don't stop batch processing
- **Validation**: Tender validation before processing

### Performance Considerations

- **Memory Efficiency**: Tenders processed individually to minimize memory usage
- **Browser Management**: Proper cleanup of browser resources
- **Parallel Processing**: Can be extended for concurrent strategy execution
- **Caching**: Strategy instances reused for efficiency

### Extensibility

Adding new details extraction strategies:

1. Implement `IDetailsStrategy` interface
2. Register with `DetailsFactory`
3. Add configuration support
4. Test with sample data

```python
from crawlers.interfaces.details_strategy import IDetailsStrategy

class CustomDetailsStrategy(IDetailsStrategy):
    def extract_details(self, tender):
        # Implementation here
        pass
    
    def can_handle(self, tender):
        # Logic to determine if this strategy applies
        return True
    
    def get_strategy_type(self):
        return "custom"
    
    def filter_tenders(self, tenders):
        # Filter tenders this strategy can handle
        return tenders

# Register the strategy
from crawlers.strategies.details_factory import get_details_factory
factory = get_details_factory()
factory.register_strategy("custom", CustomDetailsStrategy)
```

## Architecture

The system follows a layered architecture with clear separation of concerns:

```
crawlers/
├── main.py                 # Entry point and public API
├── core/                   # Orchestration components
├── strategies/             # Crawler strategy implementations
├── interfaces/             # Abstract interfaces and contracts
├── models/                 # Data models and structures
├── processors/             # Data processing utilities
├── pagination/             # Pagination handling
└── config/                 # Configuration management
```

## Core Components

### 1. Main Entry Point (`main.py`)

The main module provides the primary public interface for the crawling system:

```python
def crawl_all_tenders(url: str, portal_config: Dict, seen_tender_numbers: Set[str]) -> List[TenderModel]
```

**Purpose**: Main function to crawl and parse all tenders from a portal using the strategy pattern.

**Key Features**:
- Uses `CrawlerFactory` to select appropriate crawler strategy
- Handles error cases gracefully
- Returns standardized `TenderModel` objects

### 2. Crawler Engine (`core/crawler_engine.py`)

The `CrawlerEngine` class is the main orchestrator for the crawling workflow.

**Key Responsibilities**:
- Load and manage portal configurations
- Coordinate crawling across multiple portals and URLs
- Handle seen tender tracking to avoid duplicates
- Provide error handling and logging
- Memory-efficient processing with portal-by-portal saving

**Main Methods**:
- `run()`: Execute crawling for all active portals and returns summary statistics
- `_crawl_single_url()`: Crawl individual URLs using selected strategy
- `_save_portal_tenders()`: Save tenders from a single portal to storage

**Memory Management**:
- Processes portals sequentially to minimize memory usage
- Saves tenders immediately after each portal completes processing
- Only stores temporary portal data in memory during processing

**Error Recovery**:
- Process crash only loses current portal's progress
- Previous portals are already saved to storage
- Provides robust recovery mechanism for large-scale crawling operations

### 3. Strategy Pattern Implementation

#### Crawler Factory (`strategies/crawler_factory.py`)

The `CrawlerFactory` implements the Factory pattern to create appropriate crawler strategies based on portal configuration.

**Available Strategies**:
- `pattern_based`: For portals with structured HTML patterns
- `table_based`: For portals with tabular data layouts

**Key Methods**:
- `create_crawler()`: Create appropriate strategy instance
- `register_strategy()`: Register new crawler strategies
- `get_available_strategies()`: List available strategy types

#### Strategy Interface (`interfaces/crawler_strategy.py`)

The `ICrawlerStrategy` abstract base class defines the contract for all crawler implementations:

**Required Methods**:
- `crawl()`: Main crawling method
- `get_crawler_type()`: Return strategy identifier
- `can_handle()`: Check if strategy can handle portal configuration

## Data Models

### Tender Model (`models/tender.py`)

The `TenderModel` class provides a unified structure for tender data across different portals:

**Core Fields**:
- `docId`: Document identifier from source system
- `number`: Unique tender number/expediente
- `description`: Full tender description
- `type`: Document type (e.g., Informe, Resolución)
- `date`: Publication or last updated date
- `status`: Current tender status
- `url`: Source URL
- `details_url`: Direct URL to tender details
- `portal_name`: Source portal name
- `created_at`: Record creation timestamp

**Factory Methods**:
- `from_pattern_tender()`: Create from pattern-based data
- `from_table_tender()`: Create from table-based data

## Strategy Implementations

### Pattern-Based Crawler (`strategies/pattern_based_crawler.py`)

Handles portals with structured HTML patterns using CSS selectors and regex patterns.

**Use Cases**:
- Portals with consistent HTML structure
- Sites with predictable data patterns
- Pages requiring specific element extraction

### Table-Based Crawler (`strategies/table_based_crawler.py`)

Handles portals that present data in HTML table formats.

**Use Cases**:
- Portals with tabular data layouts
- Sites using HTML tables for tender listings
- Pages requiring table row/column parsing

## Data Processing

### Tender Processor (`processors/tender_processor.py`)

Provides utilities for processing and transforming tender data:

**Features**:
- Data validation and cleaning
- Field mapping and normalization
- Format standardization

### Deduplication Service (`processors/deduplication_service.py`)

Handles duplicate detection and removal:

**Features**:
- Tender number comparison
- Content similarity detection
- Seen tender tracking

## Configuration System

The system uses JSON configuration files to define portal settings:

**Configuration Structure**:
```json
{
  "portals": [
    {
      "name": "Portal Name",
      "country": "Country Code",
      "active": true,
      "listing_urls": ["url1", "url2"],
      "crawler_config": {
        "strategy": "pattern_based|table_based",
        "selectors": {...},
        "pagination": {...}
      }
    }
  ]
}
```

## Usage

### Basic Usage

```python
from crawlers.main import crawl_all_tenders
from crawlers.core import CrawlerEngine

# Option 1: Direct crawling
tenders = crawl_all_tenders(url, portal_config, seen_numbers)

# Option 2: Using engine (recommended)
engine = CrawlerEngine()
result = engine.run()
print(f"Processed {result['total_tenders']} tenders from {result['portals_processed']} portals")
```

### Adding New Portal Support

1. Create configuration in `config/portals.json`
2. If needed, implement new strategy by extending `ICrawlerStrategy`
3. Register strategy with `CrawlerFactory.register_strategy()`

### Custom Strategy Implementation

```python
from crawlers.interfaces.crawler_strategy import ICrawlerStrategy

class CustomCrawler(ICrawlerStrategy):
    def crawl(self, url, portal_config, seen_tender_numbers):
        # Implementation here
        pass
    
    def get_crawler_type(self):
        return "custom"
    
    def can_handle(self, portal_config):
        # Logic to determine if this strategy applies
        return True

# Register the strategy
CrawlerFactory.register_strategy("custom", CustomCrawler)
```

## Error Handling

The system implements comprehensive error handling:

- **Strategy Selection**: Raises `ValueError` if no suitable strategy found
- **Network Errors**: Graceful handling of connection issues
- **Parsing Errors**: Fallback mechanisms for malformed data
- **Configuration Errors**: Validation of portal configurations

## Best Practices

1. **Configuration Management**: Keep portal configurations in separate files
2. **Strategy Selection**: Use appropriate strategy for portal structure
3. **Error Handling**: Implement proper error handling in custom strategies
4. **Testing**: Test strategies with sample portal data
5. **Logging**: Use structured logging for debugging
6. **Rate Limiting**: Respect portal rate limits and robots.txt

## Dependencies

- **pydantic**: Data validation and modeling
- **requests**: HTTP client for web scraping
- **beautifulsoup4**: HTML parsing
- **lxml**: XML/HTML parser (optional)

## Output Format

The system outputs tender data in standardized format:
- Individual tenders as `TenderModel` objects
- Support for JSON serialization
- NDJSON format for bulk output
- Configurable output paths

## Performance Considerations

- **Memory Efficiency**: Portal-by-portal processing minimizes memory footprint
- **Incremental Saving**: Tenders are saved immediately after each portal completes
- **Error Recovery**: Process crashes only affect current portal, preserving previous work
- **Concurrent Processing**: Can be extended for parallel crawling of independent portals
- **Caching**: Seen tender tracking reduces duplicate processing
- **Rate Limiting**: Built-in delays to respect server limits

## Extensibility

The system is designed for easy extension:

1. **New Strategies**: Implement `ICrawlerStrategy` interface
2. **Custom Processors**: Add data transformation logic
3. **Storage Backends**: Implement custom output handlers
4. **Monitoring**: Add metrics and health checks

## Security Considerations

- **Input Validation**: Validate all external inputs
- **URL Safety**: Sanitize and validate URLs
- **Data Privacy**: Handle sensitive data appropriately
- **Access Control**: Respect portal authentication requirements

## Troubleshooting

### Common Issues

1. **No Strategy Found**: Check portal configuration completeness
2. **Parsing Errors**: Verify CSS selectors and patterns
3. **Duplicate Data**: Ensure seen tender tracking is working
4. **Rate Limits**: Implement appropriate delays

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When contributing to the system:

1. Follow existing code patterns and conventions
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure backward compatibility where possible
5. Use appropriate error handling and logging

## License

[Add your license information here]
