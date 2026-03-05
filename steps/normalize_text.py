import unicodedata
import re

def normalize_text(text):
    # Lowercase
    text = text.lower()
    
    # Remove accents
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    
    # Optional: remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text

normalized_text = normalize_text("Licitación Pública")
print(normalized_text)
