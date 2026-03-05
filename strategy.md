1️⃣ High-Level Flow

Start at Portal Listing Page

Example: https://comprar.gob.ar/licitaciones

This page contains a list of tender entries with links to detailed pages.

Extract Links

Identify all internal links pointing to tender details.

Apply domain and URL filtering:

Only allow approved government/financial domains.

Exclude .gov US domains, sam.gov, etc.

Keep a queue of URLs to visit.

Visit Tender Detail Pages

For each URL in the queue:

Fetch page content.

Normalize text (lowercase + remove accents).

Extract main content (ignore headers, footers, menus).

Keyword Detection

Noise Check First:

If noise keywords are present → mark page as invalid → skip PCI scoring.

Strong Procurement Triggers:

Count number of strong procurement keywords.

Structural Markers:

Check if at least one marker is present.

PCI Signals:

Primary PCI terms → +3 points

Secondary PCI/payment card terms → +1 point each

Additional Scoring:

Deadline/date → +2

Email submission → +2

Compute Scores

Procurement score ≥ 6 AND PCI score ≥ 3 → page classified as a valid PCI tender.

Else → ignore or log as non-relevant.

Storing Results

For each valid tender, store:

URL

Portal/domain

Extracted text

Detected keywords and PCI terms

Scores (procurement + PCI)

Optional: attachments or PDF links

Mark the source portal → for tracing and feedback loop.

Internal Link Handling

Keep a visited URL set → avoid revisiting pages.

If a listing page has pagination, queue next pages for scraping.

Optionally follow related links within the same portal if they point to tenders.

Feedback Loop / Manual Verification

Each stored tender can later be:

Marked as valid, false positive, or borderline.

Adjust keyword weights or model confidence accordingly.

2️⃣ Logical Flow Diagram (Conceptual)
[Portal Listing Page]
        │
        ▼
[Extract Internal Tender Links]
        │
        ▼
[Filter Domains & Queue URLs]
        │
        ▼
[Visit Tender Page]
        │
        ▼
[Extract & Normalize Text]
        │
        ▼
[Check Noise Keywords] ──Yes──> Skip Page / Disqualify
        │
        No
        │
        ▼
[Match Strong Procurement Keywords]
        │
[Match Structural Markers]
        │
[Match PCI Signals]
        │
        ▼
[Compute Scores]
        │
  Meets Thresholds?
     ┌───────Yes───────┐
     ▼                  ▼
[Store Tender]      Ignore / Log
3️⃣ Key Considerations for Internal Links

Pagination:

Keep crawling next page links until the last page.

Relative vs Absolute URLs:

Normalize URLs before adding to the queue.

Avoid loops:

Maintain a visited URL set.

Optional filtering:

Only follow URLs that contain tender identifiers like /licitacion/, /edital/, /rfp/.

Attachments:

Extract PDF/DOC links for scoring or archival.

4️⃣ How Keyword Matching Integrates

Extract text from each detail page.

Normalize (lowercase + remove accents).

Check noise first → discard if present.

Count strong procurement keywords → +4 for first +2 per additional.

Check structural markers → +2 if present.

Check PCI keywords → primary + secondary.

Include deadline/email bonus points.

Compute total → classify tender.

5️⃣ Storing / Output

For each validated tender, your system should store a structured record:

Field	Example
portal_url	https://comprar.gob.ar
tender_url	https://comprar.gob.ar/licitacion/123
procurement_keywords	["Licitación Pública", "Pliego de Bases"]
structural_markers	["Fecha límite"]
pci_keywords	["PCI DSS", "v4.0"]
procurement_score	8
pci_score	4
attachments	[pdf_url1, pdf_url2]
timestamp_scraped	2026-03-05 12:30
classification	valid_tender
✅ Summary Logic

Start at listing page → extract tender links → queue them.

Filter approved domains → ignore others.

For each tender page:

Normalize text.

Reject noise first.

Detect procurement keywords + structural markers.

Detect PCI signals.

Compute scores.

If thresholds met → store tender with all metadata.

Keep visited URL set → handle pagination → optional attachments.

Provide feedback loop for continual improvement.