1. Overall pipeline
Search / crawl layer: find candidate URLs that might be tenders.
Page pre-filter: quick checks (language, country/domain, size) to drop obvious junk.
Tender classifier (procurement-only): decide if the page is a tender/procurement page at all.
PCI classifier (payment-only): decide if the tender is PCI/payment-card related.
Final decision: apply noise filters + scoring thresholds → alert / no alert.
Everything below is about steps 1, 3 and 5.
2. Search strategy (how to find candidates)
2.1. Seed sources (high-signal portals)
Start from known procurement portals (from the doc and others you add over time):
National portals: comprar.gob.ar, compranet.hacienda.gob.mx, gov.br/compras, mercadopublico.cl, colombiacompra.gov.co, seace.gob.pe, sicop.go.cr, etc.
Regional banks: IDB, Caribbean Development Bank, CAF, World Bank Latin America sections.
Large financial institutions’ procurement portals in the region.
Crawling rule:
Only follow links that:
Contain procurement-like path fragments: /licitaciones, /compras, /procurement, /tenders, /contrataciones, /compras-publicas, /bidding, etc.
Or contain strong terms in the anchor text, e.g. Licitación, Licitaciones, Tenders, Procurement, RFP.
This guarantees you’re mostly inside tender sections.
2.2. Web search strategy (Google/Bing/API)
For broader coverage, build templated queries in ES/PT/EN:
Spanish examples:
"PCI DSS" licitación site:.gob.ar
"PCI DSS" "pliego de bases y condiciones" site:.gob.mx
"PCI DSS" "términos de referencia" pagos site:.gob.cl
Portuguese:
"PCI DSS" edital site:.gov.br
"PCI DSS" "termo de referência" pagamentos site:.gov.br
English (Caribbean/banks):
"PCI DSS" "Request for Proposals" site:.org
"PCI DSS" "Invitation to Bid" "Caribbean"
Region restriction:
Prefer site: filters with LatAm/Caribbean TLDs and known bank domains.
Avoid / blacklist:
.gov without country code that belongs to USA
sam.gov, federalregister.gov, usaspending.gov.
You then push all SERP URLs into your candidate queue.
2.3. Refresh / monitoring strategy
For each high-value portal:
Crawl index pages (e.g. “active tenders”, “open procedures”) every N hours.
Only re-fetch detail pages when:
New tender IDs appear.
Status changes (open → awarded) to capture award notices if needed.
3. Classifier design – “is this a tender or not?”
Think of this as a two-layer rule-based classifier with scoring:
Layer 1: Procurement / tender classifier
Layer 2: PCI/payment classifier
Noise & geography filters
Below is the design for Layer 1 (tender or not).
3.1. Features (signals) to extract
From HTML (after boilerplate removal):
Strong procurement keywords (high weight)
From your doc (in ES/PT/EN): Licitación, Licitación Pública, Concurso Público, Llamado a Licitación, Bases y Condiciones, Pliego, Pregão Eletrônico, Edital, Processo Licitatório, RFP, RFQ, Tender, Invitation to Bid, Call for Proposals, etc.
Structural markers:
Deadline terms: Fecha límite, Cierre de recepción, Data limite, Submission deadline, Closing date, etc.
Process IDs / numbers: Licitación N°, Número do processo, Solicitation number, Tender reference, Bid number.
Sections like Cronograma, Calendario del proceso, Evaluation criteria, Award criteria, Objeto de la contratación, Objeto da contratação, Scope of Work.
Form / attachment structure:
Links with text: Pliego, Anexos, Attachments, Download tender, Bidding document, Terms of Reference.
Presence of PDFs with typical names: pliego_*.pdf, edital_*.pdf, RFP_*.pdf, TERMINOS_DE_REFERENCIA*.pdf, etc.
Contact / submission details:
Enviar propuestas a, Send proposals to, submit proposal to, email pattern near those phrases.
Language & region:
Language detection → Spanish, Portuguese or English.
Domain/TLD & geo terms.
3.2. Tender scoring logic (procurement score)
Implement the scoring already in your doc, but only for procurement here:
Initialize proc_score = 0.
Strong triggers:
For each strong procurement word found in title or main heading (H1/H2): +4 (only once needed).
Additional occurrences in body: +2 each (cap at some max to avoid inflation).
Structural markers:
Any of the structural terms list: +2.
Dates / deadlines:
Regex for dates near “submission”, “cierre”, “data limite” etc.: +2.
Submission channel:
Email or portal link close to “submit” expressions: +2.
Decision (is it a tender?):
If proc_score < 6 → Not a tender.
If proc_score ≥ 6 → Treat as tender candidate and pass to PCI layer.
This is exactly how you “see” a tender:
Many tender-specific words plus clear structure (deadlines, process number, attachments, etc.).
3.3. PCI/payment classifier (second layer)
On pages that passed the tender check:
Extract PCI features:
+3 if PCI DSS or PCI-DSS.
+1 if version mentions: 4.0, 4.0.1, v4.0, v4.0.1 near “PCI”.
+1 if payment-card terms: cardholder data, CHD, payment card data, datos de tarjeta, dados de cartão, tarjetahabiente, procesamiento de pagos, etc.
Decision:
If pci_score < 3 → tender is not PCI-related (ignore or classify separately).
If pci_score ≥ 3 → PCI-related tender candidate.
3.4. Noise & geography filters
On any candidate (tender + PCI):
Noise exclusion:
If text contains training, course, webinar, blog, article, news, job, career, guía, curso, treinamento, etc. (from your list) in title or early content, immediately discard.
Geo exclusion:
Reject if domain is in USA federal list: sam.gov, federalregister.gov, usaspending.gov, or .gov with context clearly USA.
Optionally require: domain ends with one of included ccTLDs or known regional institutions’ domains.
4. End-to-end decision rule
Putting it all together:
Search layer finds URL.
Fetch HTML → clean text.
Compute:
proc_score (tender features)
pci_score (PCI features)
has_noise (noise terms present?)
is_geo_ok (LATAM/Caribbean, non-USA?)
Final label:
If has_noise → reject.
If !is_geo_ok → reject.
If proc_score < 6 → not a tender.
If pci_score < 3 → tender but not PCI-related.
If proc_score ≥ 6 AND pci_score ≥ 3 AND !has_noise AND is_geo_ok
→ “PCI DSS tender (Americas excl. USA)” = ALERT.
5. Optional: simple pseudocode structure
def classify_page(html, url):    text = extract_main_text(html)    lang = detect_language(text)    if not geo_allowed(url, text):        return "reject_geo"    if contains_noise_terms(text):        return "reject_noise"    proc_score = compute_procurement_score(text, html, lang)    if proc_score < 6:        return "not_tender"    pci_score = compute_pci_score(text)    if pci_score < 3:        return "tender_not_pci"    return "pci_tender_alert