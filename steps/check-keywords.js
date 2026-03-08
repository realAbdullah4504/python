const STRONG_PROCUREMENT_TRIGGERS = {
  spanish: [
    "Licitación",
    "Licitación Pública",
    "Licitación Privada",
    "Licitación Internacional",
    "Concurso Público",
    "Concurso de Precios",
    "Convocatoria",
    "Convocatoria Abierta",
    "Llamado a Licitación",
    "Llamado a Concurso",
    "Proceso de Contratación",
    "Proceso de Compra",
    "Bases y Condiciones",
    "Pliego",
    "Pliego de Bases y Condiciones",
    "Pliego Técnico",
    "Pliego Administrativo",
    "Cartel de Licitación",
    "Términos de Referencia",
    "TDR",
    "Solicitud de Propuesta",
    "Solicitud de Cotización",
    "Solicitud de Oferta",
    "Invitación a Cotizar",
    "Invitación a Ofertar",
    "Presentación de Ofertas",
    "Apertura de Ofertas",
    "Acto de Apertura",
    "Adjudicación",
  ],
  portuguese: [
    "Licitação",
    "Edital",
    "Edital de Licitação",
    "Pregão",
    "Pregão Eletrônico",
    "Tomada de Preços",
    "Concorrência Pública",
    "Chamamento Público",
    "Processo Licitatório",
    "Termo de Referência",
    "Carta Convite",
    "Proposta Comercial",
    "Proposta Técnica",
    "Recebimento de Propostas",
    "Julgamento das Propostas",
    "Homologação",
    "Adjudicação",
  ],
  english: [
    "RFP",
    "RFQ",
    "RFI",
    "ITB",
    "IFB",
    "EOI",
    "Tender",
    "Tender Notice",
    "Bidding Process",
    "Procurement",
    "Solicitation",
    "Call for Proposals",
    "Invitation to Bid",
    "Terms of Reference",
    "ToR",
    "Tender Document",
    "Bidding Document",
    "Scope of Work",
    "SOW",
    "Statement of Work",
    "Technical Specifications",
    "Bid Submission",
    "Proposal Submission",
    "Contract Award",
  ],
};

const STRUCTURAL_PROCUREMENT_MARKERS = {
  spanish: [
    "Fecha límite",
    "Cierre de recepción",
    "Plazo de recepción",
    "Cronograma",
    "Calendario del proceso",
    "Consultas hasta",
    "Ronda de consultas",
    "Aclaraciones",
    "Anexos",
    "Formulario de oferta",
    "Garantía de mantenimiento de oferta",
    "Garantía de cumplimiento",
    "Expediente N°",
    "Licitación N°",
    "Objeto de la contratación",
    "Alcance del servicio",
  ],
  portuguese: [
    "Data limite",
    "Prazo para envio",
    "Cronograma",
    "Sessão de abertura",
    "Anexos",
    "Número do processo",
    "Objeto da contratação",
    "Critérios de julgamento",
  ],
  english: [
    "Submission deadline",
    "Due date",
    "Closing date",
    "Timeline",
    "Schedule",
    "Evaluation criteria",
    "Award criteria",
    "Send proposals to",
    "Submit proposal to",
    "Attachments",
    "Annex",
    "Solicitation number",
    "Tender reference",
    "Bid number",
  ],
};

const PCI_COMPLIANCE_SIGNALS = {
  primary: ["PCI DSS", "PCI-DSS", "Payment Card Industry", "PCI compliance"],
  secondary: [
    "4.0",
    "4.0.1",
    "v4.0",
    "v4.0.1",
    "Cardholder Data",
    "CHD",
    "Payment card data",
    "Datos de tarjeta",
    "Dados de cartão",
    "Tarjetahabiente",
    "Procesamiento de pagos",
    "Pasarela de pagos",
    "Gateway de pagos",
    "Switch transaccional",
    "Adquirencia",
    "Adquirente",
  ],
};

const NOISE_EXCLUSION_LIST = {
  english: [
    "training",
    "course",
    "webinar",
    "workshop",
    "bootcamp",
    "blog",
    "article",
    "news",
    "press release",
    "hiring",
    "job",
    "career",
    "template",
    "guide",
    "what is",
  ],
  spanish: [
    "curso",
    "capacitación",
    "seminario",
    "blog",
    "noticia",
    "comunicado",
    "empleo",
    "vacante",
    "guía",
    "plantilla",
    "¿qué es?",
  ],
  portuguese: [
    "curso",
    "treinamento",
    "blog",
    "notícia",
    "vaga",
    "emprego",
    "guia",
    "modelo",
  ],
};

const APPROVED_DOMAINS = [
  ".gob.ar",
  ".gob.mx",
  ".gov.br",
  ".gub.uy",
  ".gob.pe",
  ".gob.cl",
  ".gov.co",
  ".gob.ec",
  ".gob.pa",
  ".gob.do",
  ".gob.sv",
  ".gob.gt",
  ".gob.hn",
  ".gob.ni",
  ".gob.bo",
  ".gob.py",
];

const EXCLUDED_DOMAINS = ["sam.gov", "federalregister.gov", "usaspending.gov"];

const SCORING_CONFIG = {
  procurement: {
    strong_trigger: 4,
    additional_procurement: 2,
    structural_marker: 2,
    deadline_date: 2,
    email_submission: 2,
  },
  pci: {
    primary_pci: 3,
    version_4: 1,
    payment_card_terms: 1,
  },
  thresholds: {
    min_procurement_score: 6,
    min_pci_score: 3,
  },
};

const keywords = [
  ...STRONG_PROCUREMENT_TRIGGERS.english,
  ...STRONG_PROCUREMENT_TRIGGERS.spanish,
  ...STRONG_PROCUREMENT_TRIGGERS.portuguese,
  ...PCI_COMPLIANCE_SIGNALS.primary,
  ...PCI_COMPLIANCE_SIGNALS.secondary,
  ...NOISE_EXCLUSION_LIST.english,
  ...NOISE_EXCLUSION_LIST.spanish,
  ...NOISE_EXCLUSION_LIST.portuguese,
];
const links = [
  { link: "ctl00$CPH1$GridListaPliegosAperturaProxima$ctl02$lnkNumeroProceso" },
  { link: "ctl00$CPH1$GridListaPliegosAperturaProxima$ctl03$lnkNumeroProceso" },
  { link: "ctl00$CPH1$GridListaPliegosAperturaProxima$ctl04$lnkNumeroProceso" },
  { link: "ctl00$CPH1$GridListaPliegosAperturaProxima$ctl05$lnkNumeroProceso" },
  { link: "ctl00$CPH1$GridListaPliegosAperturaProxima$ctl06$lnkNumeroProceso" },
  { link: "ctl00$CPH1$GridListaPliegosAperturaProxima$ctl07$lnkNumeroProceso" },
  { link: "ctl00$CPH1$GridListaPliegosAperturaProxima$ctl08$lnkNumeroProceso" },
  { link: "ctl00$CPH1$GridListaPliegosAperturaProxima$ctl09$lnkNumeroProceso" },
  { link: "ctl00$CPH1$GridListaPliegosAperturaProxima$ctl10$lnkNumeroProceso" },
  { link: "ctl00$CPH1$GridListaPliegosAperturaProxima$ctl11$lnkNumeroProceso" },
  { link: "ctl00$CPH1$GridListaPliegosAperturaProxima" },
];

function checkLinksForKeywords(links, keywords) {
  if (
    !Array.isArray(links) ||
    !Array.isArray(keywords) ||
    keywords.length === 0
  )
    return [];

  // Escape special regex characters in keywords and join with |
  const escapedKeywords = keywords.map((keyword) =>
    keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  );
  const keywordPattern = escapedKeywords.join("|");
  const keywordRegex = new RegExp(keywordPattern, "i");

  return links
    .filter((link) => {
      if (typeof link !== "string") return false;
      return keywordRegex.test(link);
    })
    .map((link) => {
      // Find which keywords matched this link
      const matchedTerms = keywords.filter((keyword) =>
        new RegExp(keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i").test(
          link
        )
      );
      return {
        link: link,
        matchedTerms: matchedTerms,
      };
    });
}

const hasMatches = checkLinksForKeywords(links, keywords);
console.log(hasMatches);
