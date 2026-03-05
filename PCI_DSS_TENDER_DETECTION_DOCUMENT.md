# DOCUMENT FOR ABDU – PCI DSS TENDER DETECTION (AMERICAS EXCLUDING USA)

## 1️⃣ Strategic Objective

We are NOT searching for informational content about PCI DSS.
We ONLY want to detect:
- Official procurement processes
- Public or private tenders
- Formal RFP / RFQ / bidding documents
- Structured procurement portals
- Documents requesting proposals from vendors

### Region Scope:
✅ **Include:**
- Latin America
- Caribbean
- Central America
- South America
- Puerto Rico

❌ **Exclude:**
- United States (.gov, .us federal portals)

---

## 2️⃣ Core Detection Logic (Procurement-First Model)

**DO NOT trigger alerts based on PCI alone.**

Trigger alerts ONLY if:
1. **Strong procurement/tender signals are detected**
2. **AND PCI or payment card compliance signals are present**
3. **AND noise terms are absent**

---

## 3️⃣ Ultra-Detailed Procurement Keyword Dictionary (Americas – Spanish + Portuguese + English)

These are region-adapted terms commonly used in LATAM government and financial procurement portals.
You should detect at least 2 of these OR 1 strong + 1 structural marker.

### A) Strong Procurement Triggers (High Weight)

**If any of these appear, assign high score:**

#### Spanish:
- Licitación
- Licitación Pública
- Licitación Privada
- Licitación Internacional
- Concurso Público
- Concurso de Precios
- Convocatoria
- Convocatoria Abierta
- Llamado a Licitación
- Llamado a Concurso
- Proceso de Contratación
- Proceso de Compra
- Bases y Condiciones
- Pliego
- Pliego de Bases y Condiciones
- Pliego Técnico
- Pliego Administrativo
- Cartel de Licitación (Costa Rica)
- Términos de Referencia
- TDR
- Solicitud de Propuesta
- Solicitud de Cotización
- Solicitud de Oferta
- Invitación a Cotizar
- Invitación a Ofertar
- Presentación de Ofertas
- Apertura de Ofertas
- Acto de Apertura
- Adjudicación

#### Portuguese (Brazil):
- Licitação
- Edital
- Edital de Licitação
- Pregão
- Pregão Eletrônico
- Tomada de Preços
- Concorrência Pública
- Chamamento Público
- Processo Licitatório
- Termo de Referência
- Carta Convite
- Proposta Comercial
- Proposta Técnica
- Recebimento de Propostas
- Julgamento das Propostas
- Homologação
- Adjudicação

#### English (Caribbean, international banks):
- RFP
- RFQ
- RFI
- ITB
- IFB
- EOI
- Tender
- Tender Notice
- Bidding Process
- Procurement
- Solicitation
- Call for Proposals
- Invitation to Bid
- Terms of Reference (ToR)
- Tender Document
- Bidding Document
- Scope of Work (SOW)
- Statement of Work
- Technical Specifications
- Bid Submission
- Proposal Submission
- Contract Award

### B) Structural Procurement Markers (Mandatory at least 1)

These distinguish real tenders from informational pages:

#### Spanish:
- Fecha límite
- Cierre de recepción
- Plazo de recepción
- Cronograma
- Calendario del proceso
- Consultas hasta
- Ronda de consultas
- Aclaraciones
- Anexos
- Formulario de oferta
- Garantía de mantenimiento de oferta
- Garantía de cumplimiento
- Expediente N°
- Licitación N°
- Objeto de la contratación
- Alcance del servicio

#### Portuguese:
- Data limite
- Prazo para envio
- Cronograma
- Sessão de abertura
- Anexos
- Número do processo
- Objeto da contratação
- Critérios de julgamento

#### English:
- Submission deadline
- Due date
- Closing date
- Timeline
- Schedule
- Evaluation criteria
- Award criteria
- Send proposals to
- Submit proposal to
- Attachments
- Annex
- Solicitation number
- Tender reference
- Bid number

---

## 4️⃣ PCI / Payment Compliance Signals

After procurement context is confirmed, check for:

### Primary:
- PCI DSS
- PCI-DSS
- Payment Card Industry
- PCI compliance

### Secondary:
- 4.0
- 4.0.1
- v4.0
- v4.0.1
- Cardholder Data
- CHD
- Payment card data
- Datos de tarjeta
- Dados de cartão
- Tarjetahabiente
- Procesamiento de pagos
- Pasarela de pagos
- Gateway de pagos
- Switch transaccional
- Adquirencia
- Adquirente

**DO NOT require QSA/ROC/AOC as mandatory.**

---

## 5️⃣ Noise Exclusion List (Very Important)

Exclude any page containing:

#### English:
- training
- course
- webinar
- workshop
- bootcamp
- blog
- article
- news
- press release
- hiring
- job
- career
- template
- guide
- what is

#### Spanish:
- curso
- capacitación
- seminario
- blog
- noticia
- comunicado
- empleo
- vacante
- guía
- plantilla
- ¿qué es?

#### Portuguese:
- curso
- treinamento
- blog
- notícia
- vaga
- emprego
- guia
- modelo

---

## 6️⃣ Scoring System (Recommended)

### Procurement Score:
- +4 if strong trigger detected
- +2 per additional procurement term
- +2 if structural marker found
- +2 if deadline/date detected
- +2 if email for proposal submission detected

### PCI Score:
- +3 if "PCI DSS" found
- +1 if version 4.0 or 4.0.1 found
- +1 if payment-card-related terms found

### Disqualify:
- If noise term detected
- If procurement score < 6
- If PCI score < 3

### Alert only if:
**Procurement score ≥ 6 AND PCI score ≥ 3**

---

## 7️⃣ Geographic Filtering (Exclude USA)

### Exclude:
- .gov domains from United States federal procurement
- sam.gov
- federalregister.gov
- usaspending.gov

### Include:
- .gob.ar
- .gob.mx
- .gov.br
- .gub.uy
- .gob.pe
- .gob.cl
- .gov.co
- .gob.ec
- .gob.pa
- .gob.do
- .gob.sv
- .gob.gt
- .gob.hn
- .gob.ni
- .gob.bo
- .gob.py
- Caribbean government portals
- Regional development banks
- Financial institutions procurement portals

---

## 8️⃣ Example Tender Pages (For Pattern Recognition)

These are real procurement-style examples so you understand structure:

### Argentina Government Procurement Portal:
https://comprar.gob.ar

### Brazil Federal Procurement:
https://www.gov.br/compras

### Chile Public Procurement:
https://www.mercadopublico.cl

### Mexico Government Procurement:
https://compranet.hacienda.gob.mx

### Colombia Public Procurement:
https://www.colombiacompra.gov.co

### Costa Rica (Carteles):
https://www.sicop.go.cr

### Peru SEACE:
https://www.seace.gob.pe

### Inter-American Development Bank:
https://www.iadb.org/en/work-with-us/procurement

### Caribbean Development Bank:
https://www.caribank.org/work-with-us/procurement

### These portals clearly show:
- Process number
- Submission deadline
- Attachments
- Evaluation criteria
- Award notice

**That is the pattern we want to detect.**

---

## Implementation Notes

1. **Priority Order:** Always check procurement signals first, then PCI signals
2. **Language Detection:** Implement proper language detection for Spanish/Portuguese content
3. **Domain Validation:** Strict geographic filtering is critical
4. **False Positive Prevention:** The noise exclusion list is essential for accuracy
5. **Threshold Tuning:** The scoring system may need fine-tuning based on real-world testing

---

*Document created for PCI DSS Tender Detection System - Americas Region (Excluding USA)*
