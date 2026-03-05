1. Crawl page → extract text
2. Normalize text (lowercase + remove accents)
3. Check noise keywords
      └─ if noise found → reject page early
4. Match strong procurement triggers
5. Match structural markers
6. Match PCI keywords
7. Calculate scores:
      procurement_score = strong_triggers + structural_markers
      pci_score = PCI primary + PCI secondary
8. Apply thresholds
      └─ if procurement_score >= threshold AND pci_score >= threshold → valid PCI tender