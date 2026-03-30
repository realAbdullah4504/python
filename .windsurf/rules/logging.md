---
trigger: manual
---

# Logging Guidelines & Standards

## Overview
This document defines logging standards for the tender crawling pipeline across all phases: listing (crawling), details extraction, and PCI analysis.

## 🎯 Core Principles

### 1️⃣ Logger Setup
- **Use centralized `utils.logger` module** for all logging needs
- **Module-level loggers** in engines/processors: `logger = get_logger(__name__, "phase_name")`
- **Raw scripts** can initialize their own logger during prototyping
- **Never use `print()`** - always use proper logging

### 2️⃣ Log Levels
- **INFO**: Normal flow, phase start/end, key events, summaries
- **WARNING**: Skipped items, expected issues, fallback behavior
- **ERROR**: Unexpected errors, failures that need attention
- **DEBUG**: Detailed troubleshooting (use sparingly)

### 3️⃣ Log Message Format
- **Structured context**: Include relevant IDs, names, counts
- **Emoji indicators**: Use emojis for quick visual scanning
- **Consistent prefixes**: Phase names, portal names, URLs
- **No sensitive data**: Avoid logging passwords, tokens, PII

---

## 📋 Phase-Specific Logging

### 🕷️ Listing/Crawling Phase
```python
from utils.logger import get_logger, log_phase_start, log_phase_end, log_portal_processing, log_tender_extraction

logger = get_logger(__name__, "listing")

# Phase start
log_phase_start(logger, "listing", {"portals_count": len(portals)})

# Portal processing
log_portal_processing(logger, portal['name'], portal['country'], len(portal.get("listing_urls", [])))

# URL crawling
logger.info(f"Crawling URL: {url}")
tenders = crawler.crawl(url, portal_config, seen_tender_numbers)
log_tender_extraction(logger, url, len(tenders))

# Phase end
log_phase_end(logger, "listing", {"total_tenders": summary["total_tenders"], "portals_processed": summary["portals_processed"]})
```

### 🔍 Details Extraction Phase
```python
from utils.logger import get_logger, log_phase_start, log_phase_end, log_skip_with_reason

logger = get_logger(__name__, "details")

# Phase start
log_phase_start(logger, "details", {"tenders_to_process": len(tenders)})

# Processing individual tender
logger.info(f"Processing details for tender: {tender.number} ({tender.portal})")

# Skip scenarios
log_skip_with_reason(logger, f"tender {tender.number}", "no detail URL available")
log_skip_with_reason(logger, f"tender {tender.number}", "detail page returned 404")

# Phase end
log_phase_end(logger, "details", {"processed": len(processed), "enriched": len(enriched), "skipped": len(skipped)})
```

### 🛡️ PCI Analysis Phase
```python
from utils.logger import get_logger, log_phase_start, log_phase_end

logger = get_logger(__name__, "pci_analysis")

# Phase start
log_phase_start(logger, "pci_analysis", {"tenders_to_analyze": len(tenders)})

# Analysis results
logger.info(f"Tender {tender.number}: PCI score {tender.pci_score} (high_risk: {tender.high_risk})")

# Phase end
log_phase_end(logger, "pci_analysis", {"analyzed": len(analyzed), "high_risk": high_risk_count, "avg_score": avg_score})
```

---

## 🔧 Implementation Examples

### Engine/Processor Module
```python
from utils.logger import get_logger, log_error_with_context

class CrawlerEngine:
    def __init__(self):
        self.logger = get_logger(__name__, "listing")
    
    def run(self):
        try:
            self.logger.info("Starting crawler engine")
            # ... implementation
        except Exception as e:
            log_error_with_context(self.logger, e, "crawler engine run")
            raise
```

### Strategy Implementation
```python
from utils.logger import get_logger

class TableBasedCrawler:
    def __init__(self):
        self.logger = get_logger(__name__, "listing")
    
    def crawl(self, url, config, seen_numbers):
        self.logger.info(f"Starting table-based crawl for {url}")
        # ... implementation
        self.logger.info(f"Found {len(tenders)} new tenders")
        return tenders
```

### Raw Script (Prototyping)
```python
from utils.logger import setup_logger

logger = setup_logger(__name__, log_file="logs/prototype.log")

def main():
    logger.info("Starting prototype script")
    # ... implementation
    logger.info("Prototype completed")
```

---

## 📁 Log File Organization

### Directory Structure
```
logs/
├── listing_20240329_143022.log
├── details_20240329_143545.log
├── pci_analysis_20240329_144210.log
└── pipeline_20240329_145000.log
```

### File Naming Convention
- **Phase-specific**: `{phase}_{timestamp}.log`
- **Pipeline-wide**: `pipeline_{timestamp}.log`
- **Timestamp format**: `YYYYMMDD_HHMMSS`

---

## ✅ Best Practices

### DO ✅
- Use `get_logger(__name__, "phase")` in modules
- Log phase start/end with `log_phase_start()` and `log_phase_end()`
- Include context (IDs, counts, names) in log messages
- Use appropriate log levels
- Create logs directory automatically

### DON'T ❌
- Use `print()` statements
- Log sensitive information
- Use DEBUG level in production unless troubleshooting
- Create duplicate handlers
- Hardcode log file paths

---

## 🔄 Migration Checklist

### From Raw Scripts to Engines
- [ ] Replace `print()` with `logger.info()`
- [ ] Add module-level logger: `logger = get_logger(__name__, "phase")`
- [ ] Add phase start/end logging
- [ ] Add error logging with context
- [ ] Test log file creation

### For Existing Engines
- [ ] Import `get_logger` and helper functions
- [ ] Initialize logger in `__init__`
- [ ] Replace print statements
- [ ] Add structured logging for key events
- [ ] Verify log levels and formatting

---

## 🚀 Quick Start Template

```python
# New engine/processor template
from utils.logger import get_logger, log_phase_start, log_phase_end, log_error_with_context

class NewEngine:
    def __init__(self):
        self.logger = get_logger(__name__, "phase_name")
    
    def run(self):
        log_phase_start(self.logger, "phase_name", {"context": "value"})
        
        try:
            # Your implementation here
            results = self._process()
            
            log_phase_end(self.logger, "phase_name", {"results_count": len(results)})
            return results
            
        except Exception as e:
            log_error_with_context(self.logger, e, "phase_name run")
            raise
```

This logging system ensures **observability**, **debuggability**, and **consistency** across the entire tender crawling pipeline.

### 2️⃣ Idea for Phases & Raw Scripts

- **Yes, you can initialize the logger in raw scripts** during early prototyping.  
- **Best practice** for scaling: migrate to **module-level loggers** in engines/processors.  
- **Phases (listing, detail, PCI analysis)** should **log start/end, key events, skips, errors**.  

> Think of raw script logs as **temporary**, but engines log **structured and consistent** messages.  

---

### 3️⃣ Recommended Approach

1. **Start small**: Initialize logger in each raw script to get immediate feedback.  
2. **When refactoring to engines/processors**:  
   - Use **module-level loggers** or centralized `get_logger()`  
   - Replace all print statements  
   - Follow levels and context rules  
3. **Document everything in `logger.md`** so AI or new team members can implement logging consistently.  

---

✅ **Key Takeaways**

- Logger MD file is a **guideline & reference** for all scripts and engines.  
- Phases should have **phase-specific logging** for observability.  
- Raw scripts can initialize their own logger early; later everything converges into the **standardized system**.

---

If you want, I can **draft a ready-to-use `logger.md` with examples for each of your phases** (listing, details, PCI analysis) so it’s immediately usable for AI or your team.  

Do you want me to do that next?