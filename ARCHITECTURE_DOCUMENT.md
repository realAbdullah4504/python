# PCI Tender Detection System Architecture

## Overview

The PCI Tender Detection System is a comprehensive web scraping and analysis pipeline designed to identify and evaluate tenders related to PCI DSS (Payment Card Industry Data Security Standard) compliance. The system crawls tender portals, extracts detailed information, and analyzes content for PCI compliance signals.

## System Architecture

### High-Level Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐    ┌──────────────────┐
│   Pipeline      │───▶│  Tender Listings │───▶│   Tender Details    │───▶│  PCI Analysis    │
│  Orchestrator   │    │    Crawler       │    │   Crawler           │    │   Engine         │
└─────────────────┘    └──────────────────┘    └─────────────────────┘    └──────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐    ┌──────────────────┐
│  Configuration  │    │  tenders.ndjson  │    │enriched_tenders.    │    │scored_tenders.   │
│   Management    │    │   (raw data)     │    │ndjson (full text)   │    │ndjson (scores)   │
└─────────────────┘    └──────────────────┘    └─────────────────────┘    └──────────────────┘
```

## Core Components

### 1. Pipeline Orchestrator (`pipeline/run_pipeline.py`)

**Role**: Main controller that coordinates the entire workflow

**Key Functions**:
- `crawl_all_portals()`: Iterates through configured tender portals
- `main()`: Executes the three-step pipeline process
- Configuration management via `config/portals.json`

**Workflow**:
1. **Step 1**: Crawl tender listings from all active portals
2. **Step 2**: Extract detailed information for each tender
3. **Step 3**: Analyze PCI compliance signals

**Data Flow**:
```
Portals Config → Listing Crawler → Details Crawler → PCI Analyzer → Output Files
```

### 2. Tender Listings Crawler (`crawlers/crawl_listings.py`)

**Role**: Extracts basic tender information from portal listing pages

**Key Functions**:
- `crawl_all_tenders()`: Main crawling function with pagination support
- `extract_listing_rows()`: Parses HTML tables to extract tender data
- `simulate_postback()`: Handles ASP.NET postback events for navigation
- `extract_pagination_links()`: Identifies and processes pagination controls

**Technical Implementation**:
- Uses Playwright for browser automation
- BeautifulSoup for HTML parsing
- Handles ASP.NET WebForms postback mechanisms
- Supports incremental crawling (avoids duplicates)

**Data Structure**:
```python
{
    "number": "TENDER-001",
    "description": "PCI DSS compliance services",
    "type": "Service",
    "date": "2024-03-15",
    "status": "Active",
    "url": "portal_url",
    "details_url": "postback_target",
    "page_no": 1,
    "pagination_target": "ctl00$Content$gvTenders",
    "pagination_argument": "Page$2"
}
```

**Error Handling**:
- Retry mechanisms for failed requests
- Resource cleanup with proper browser shutdown
- Graceful handling of missing elements

### 3. Tender Details Crawler (`crawlers/crawl_details.py`)

**Role**: Extracts full text content from individual tender detail pages

**Key Functions**:
- `process_tenders()`: Orchestrates detail extraction for multiple tenders
- `process_single_tender()`: Handles individual tender detail extraction
- `load_processed_tenders_from_ndjson()`: Prevents reprocessing
- `extract_full_text_from_page()`: Cleans and extracts text content

**Technical Implementation**:
- Multi-tab browsing to avoid state conflicts
- Postback simulation for navigation to detail pages
- Full text extraction and cleaning
- Incremental processing with deduplication

**Data Enrichment**:
```python
# Original tender data + enriched fields
{
    # ... original fields ...
    "full_text": "Complete tender description and requirements...",
    "details_url": "actual_detail_page_url"
}
```

**Performance Optimizations**:
- Browser context reuse
- Tab isolation for each tender
- Immediate file flushing for data persistence

### 4. PCI Compliance Detection Engine (`steps/pci_compliance_detection.py`)

**Role**: Analyzes tender content for PCI DSS compliance signals

**Key Classes**:
- `PCIComplianceDetector`: Main detection engine with pattern matching

**Detection Methodology**:
- **Primary Signals**: Direct PCI DSS references (100% accuracy target)
- **Secondary Signals**: Version numbers, payment card terms (>95% accuracy)
- **Scoring System**: Weighted calculation based on signal types

**Signal Detection**:
```python
# Primary signals (high confidence)
"PCI DSS", "Payment Card Industry", "Data Security Standard"

# Secondary signals (supporting evidence)
"v4.0", "4.0.1", "Cardholder Data", "CHD", "Payment Gateway"
```

**Scoring Algorithm**:
```python
total_score = (primary_signals * 2.0) + 
              (version_4_refs * 1.5) + 
              (payment_card_terms * 1.0)
```

**Text Processing**:
- Unicode normalization for accented characters
- Regex pattern compilation for performance
- Position tracking for signal validation

## Data Flow Architecture

### File-Based Pipeline

```
1. Raw Listings     → outputs/tenders.ndjson
2. Enriched Data    → outputs/enriched_tenders.ndjson  
3. Analyzed Results → outputs/scored_tenders.ndjson
```

**NDJSON Format**:
- One JSON object per line
- Append-only writes for data integrity
- Easy streaming and incremental processing

### Configuration Management

**Portal Configuration** (`config/portals.json`):
```json
{
  "portals": [
    {
      "name": "Comprar Gob AR",
      "country": "Argentina",
      "type": "national",
      "active": true,
      "listing_urls": [
        "https://comprar.gob.ar/Compras.aspx?qs=W1HXHGHtH10="
      ],
      "selectors": {
        "main_table": "table",
        "table_body": "tbody",
        "table_row": "tr",
        "header_row_class": "tr-header",
        "pagination_row_class": "pagination-gv",
        "link": "a",
        "table_cell": "td"
      },
      "column_mapping": {
        "number": 0,
        "description": 1,
        "type": 2,
        "date": 3,
        "status": 4
      }
    }
  ]
}
```

**Configuration Features**:
- **Selectors**: CSS selectors for HTML element identification
- **Column Mapping**: Field-to-index mapping for table data extraction
- **Portal Metadata**: Country, type, and activation status
- **URL Management**: Multiple listing URLs per portal

**PCI Keywords** (`config/keywords_pci_dss_americas.py`):
- Primary and secondary signal definitions
- Scoring configuration
- Threshold settings

## Technology Stack

### Core Technologies
- **Python 3.x**: Primary programming language
- **Playwright**: Browser automation for modern web applications
- **BeautifulSoup4**: HTML parsing and extraction
- **Regex**: Pattern matching for signal detection

### Data Processing
- **NDJSON**: Streaming data format
- **JSON**: Configuration and data exchange
- **Unicode normalization**: Multi-language text processing

### External Dependencies
- **Web Browsers**: Chromium via Playwright
- **Configuration Files**: JSON-based portal and keyword definitions

## Error Handling & Resilience

### Crawler Resilience
- Retry mechanisms with exponential backoff
- Browser resource cleanup
- Graceful handling of missing elements
- Incremental processing to avoid data loss

### Data Integrity
- Atomic file operations
- Immediate flushing for data persistence
- Duplicate detection and prevention
- Validation of data structures

### Monitoring & Logging
- Progress tracking for long-running operations
- Error reporting with context
- Performance metrics collection

## Performance Considerations

### Optimization Strategies
- Browser context reuse
- Parallel processing capabilities
- Incremental crawling (avoid reprocessing)
- Efficient regex compilation

### Scalability Features
- Configurable processing limits
- Modular architecture for easy extension
- File-based data persistence for large datasets
- Memory-efficient streaming processing

## Security & Compliance

### Data Handling
- No sensitive data storage in code
- Configuration-based approach
- Safe text processing with normalization

### Web Scraping Ethics
- Respect robots.txt configurations
- Rate limiting and polite crawling
- Error handling to avoid server overload

## Extension Points

### Adding New Portals

1. **Update `config/portals.json`**:
   - Add new portal configuration with required metadata
   - Define CSS selectors for HTML element identification
   - Configure column mapping for data extraction
   - Set listing URLs and activation status

2. **Test Portal Integration**:
   - Verify selector patterns work with target portal
   - Test postback mechanisms for navigation
   - Validate column mapping matches table structure

3. **Adjust Extraction Patterns** (if needed):
   - Modify selectors for portal-specific HTML structure
   - Update column mapping for different table layouts
   - Add portal-specific handling if required

### Enhancing PCI Detection
1. Update `keywords_pci_dss_americas.py`
2. Add new signal categories
3. Adjust scoring weights

### Adding Analysis Steps
1. Create new step modules in `steps/` directory
2. Integrate into pipeline orchestrator
3. Define output data structures

## Deployment Architecture

### Local Development
- Direct Python execution
- File-based configuration
- Local browser automation

### Production Considerations
- Container deployment with Docker
- Scheduled execution via cron
- Monitoring and alerting
- Data backup strategies

## Monitoring & Maintenance

### Health Checks
- File existence validation
- Data format verification
- Browser automation status

### Maintenance Tasks
- Log file rotation
- Temporary file cleanup
- Configuration updates
- Performance tuning

---

**Document Version**: 1.0  
**Last Updated**: March 2025  
**System Version**: PCI Tender Detection System v1.0
