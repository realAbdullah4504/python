from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

llm = OllamaLLM(model="mistral", temperature=0)

prompt = PromptTemplate.from_template(
"""
You are a procurement classifier.

Tender means:
- government procurement
- bids
- request for proposal (RFP)
- request for quotation (RFQ)
- contract bidding

Examples:

Text: Government invites bids for supply of equipment
Answer: Tender

Text: Request for proposal for building construction
Answer: Tender

Text: Our company launched a new mobile app
Answer: Not Tender

Text: Learn Python programming tutorial
Answer: Not Tender

Now classify:

Text: {text}

Answer:
"""
)

chain = prompt | llm

dataset = [
    {"text": "Government invites bids for supply of medical equipment.", "label": "Tender"},
    {"text": "Our company launched a new mobile app.", "label": "Not Tender"},
    {"text": "Request for proposal for road construction.", "label": "Tender"},
    {"text": "Learn Python programming with this tutorial.", "label": "Not Tender"},
]

tp = fp = tn = fn = 0

for item in dataset:
    prediction = chain.invoke({"text": item["text"]}).strip()
    true_label = item["label"]

    print("Text:", item["text"])
    print("Prediction:", prediction, "| True:", true_label)
    print()

    if prediction == "Tender" and true_label == "Tender":
        tp += 1
    elif prediction == "Tender" and true_label == "Not Tender":
        fp += 1
    elif prediction == "Not Tender" and true_label == "Not Tender":
        tn += 1
    elif prediction == "Not Tender" and true_label == "Tender":
        fn += 1

# Metrics
precision = tp / (tp + fp) if (tp + fp) else 0
recall = tp / (tp + fn) if (tp + fn) else 0
accuracy = (tp + tn) / (tp + tn + fp + fn)

print("Precision:", precision)
print("Recall:", recall)
print("Accuracy:", accuracy)