import re

def calculate_procurement_score(text):
    score = 0
    detected = []

    keywords = ["tender", "licitación", "bidding", "proposal", "RFP"]

    for word in keywords:
        if word.lower() in text.lower():
            score += 2
            detected.append(word)

    if re.search(r"\b\d{2}/\d{2}/\d{4}\b", text):
        score += 1
        detected.append("deadline_date")

    if "@" in text:
        score += 1
        detected.append("email_found")

    return score, detected


sample_text = """
Licitación Pública para servicios de auditoría PCI DSS 4.0.
Fecha límite: 31/03/2026
Enviar propuesta a compras@empresa.gov.ar
"""

score, detected = calculate_procurement_score(sample_text)

print("Score:", score)
print("Detected:", detected)