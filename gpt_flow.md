1. First Understand the 4 Different Problems

Many people mix these together.

1️⃣ Discovery

Find which pages exist.

Example:

https://portal.com/tenders
 ├ page 1
 ├ page 2
 ├ page 3

Goal:

Collect ALL tender URLs
2️⃣ Crawling

Visit pages and download HTML.

Example:

tender_url -> fetch HTML

Result:

raw_html/
   tender_1.html
   tender_2.html
3️⃣ Extraction

Parse HTML and extract structured data.

Example:

title
description
deadline
budget
country
attachments

Output:

{
  "title": "...",
  "deadline": "...",
  "description": "..."
}
4️⃣ Processing

Your AI scoring / PCI classification.

Example:

Procurement scoring
PCI scoring
category classification
2. Best Pipeline Architecture

Your system should look like this:

                 ┌─────────────┐
                 │ Seed URL    │
                 └──────┬──────┘
                        │
                        ▼
                ┌──────────────┐
                │ Link Crawler │
                └──────┬───────┘
                       │
                       ▼
             ┌──────────────────┐
             │ Tender URL Queue │
             └────────┬─────────┘
                      │
                      ▼
                ┌────────────┐
                │ Page Fetch │
                └─────┬──────┘
                      │
                      ▼
                ┌────────────┐
                │ HTML Store │
                └─────┬──────┘
                      │
                      ▼
                ┌──────────────┐
                │ Data Extract │
                └─────┬────────┘
                      │
                      ▼
               ┌───────────────┐
               │ Tender JSON   │
               └─────┬─────────┘
                     │
                     ▼
               ┌──────────────┐
               │ AI Scoring   │
               └──────────────┘
3. Technologies Best For Your Case

You have three levels of scrapers.

Level 1 — Static Sites (Fastest)

Use:

requests
BeautifulSoup

Example:

requests.get(url)

Advantages

✔ fastest
✔ cheapest
✔ simple

Works for:

80% of government portals
Level 2 — Dynamic Sites

Use:

Playwright

Why?

Tender portals often use:

ASP.NET
postback
javascript links
pagination

Example:

javascript:__doPostBack(...)

Requests cannot handle this.

Playwright can.

Level 3 — Heavy JS / Authentication

Use:

Playwright + session handling

Examples:

login portals
captcha portals
token requests
4. Best Crawler Strategy

Use a queue-based crawler.

Breadth First Crawl
seed page
   │
   ├ link1
   ├ link2
   ├ link3

Algorithm:

queue = [seed]

while queue:
    url = queue.pop()

    html = fetch(url)

    extract links

    add new links to queue
5. Domain Restriction (VERY IMPORTANT)

Never crawl the entire internet.

Restrict to:

allowed_domains

Example:

comprar.gob.ar

Filter:

if parsed_url.netloc not in allowed_domains:
    skip
6. Link Normalization

Always normalize URLs:

urljoin(base_url, link)

Example:

/tenders/123

becomes

https://portal.com/tenders/123
7. Deduplication

You must track:

visited_urls

Example:

visited = set()
8. Tender Detection

Instead of crawling everything, detect tender pages.

Examples:

/tender/
/licitacion/
/bid/
/procurement/

Or pattern:

tender_id=123
9. Store Raw HTML (VERY IMPORTANT)

Enterprise systems always store raw pages.

Why?

Because extraction rules change.

Example storage:

raw_pages/
   portal/
      123.html
      124.html
10. Recommended Folder Architecture

For your project:

tender_pipeline/

crawler/
    crawler.py
    queue_manager.py
    domain_filter.py

fetcher/
    requests_fetcher.py
    playwright_fetcher.py

extractor/
    tender_extractor.py

storage/
    html_store.py
    json_store.py

pipeline/
    scoring_engine.py

config/
    portals.yaml
11. Crawl Strategy Used by Large Companies

Companies like:

Google

Scrapy Cloud

Diffbot

Use:

Distributed crawler
Queue
Workers
Extractor
Storage

Later when your system grows:

Kafka / Redis Queue
multiple crawler workers

But for now keep it simple.

12. Best Minimal Setup for You

For your proof of concept:

Use:

Playwright crawler
+
BS4 extraction
+
JSON output

Pipeline:

Playwright → HTML
BS4 → Data
JSON → scoring
13. Real Production Advice

The biggest mistake beginners make:

❌ optimizing crawler early

Instead:

crawl ONE portal
build full pipeline
debug
then generalize

Exactly like you are doing.

This is correct engineering thinking.

14. One Important Rule

Separate these:

crawler
extractor
scorer

Never mix them.

15. If I Were Building Your System

I would build 5 modules:

1 crawler
2 fetcher
3 extractor
4 scoring engine
5 storage

If you want, I can also show you the exact minimal crawler architecture (about 150 lines) that can:

✔ crawl internal links
✔ handle ASP.NET postbacks
✔ detect tender pages
✔ save HTML

This will be a very solid base for your project.