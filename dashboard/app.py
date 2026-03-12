# streamlit_pci_dashboard.py
import streamlit as st
import pandas as pd
import json

# ------------------------------
# Load scored tenders from NDJSON
# ------------------------------
def load_scored_tenders(filename: str):
    tenders = []
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
        # process all lines
        for line in lines:
            if line.strip():
                tenders.append(json.loads(line))
    return tenders

# ------------------------------
# Convert to DataFrame for display
# ------------------------------
def tenders_to_df(tenders: list):
    data = []
    for t in tenders:
        data.append({
            "Tender Number": t.get("number", ""),
            "Description": t.get("description", ""),
            "PCI Score": t.get("pci_score", 0),
            "Matched PCI Keywords": ", ".join(t.get("matched_pci_keywords", [])),
            "Source URL": t.get("details_url", "")
        })
    df = pd.DataFrame(data)
    return df

# ------------------------------
# Streamlit App
# ------------------------------
st.set_page_config(page_title="Tender PCI Dashboard", layout="wide")
st.title("Tender PCI Compliance Dashboard")

# Load data
scored_file = "outputs/scored_tenders.ndjson"
tenders = load_scored_tenders(scored_file)
df = tenders_to_df(tenders)

# Sidebar filters
st.sidebar.header("Filters")
min_score = st.sidebar.number_input("Minimum PCI Score", value=0, step=1)
keyword_filter = st.sidebar.text_input("Filter by PCI Keyword (comma-separated)")

filtered_df = df[df["PCI Score"] >= min_score]

# Apply keyword filter if provided
if keyword_filter.strip():
    keywords = [k.strip().lower() for k in keyword_filter.split(",")]
    filtered_df = filtered_df[
        filtered_df["Matched PCI Keywords"].str.lower().apply(
            lambda x: any(k in x for k in keywords)
        )
    ]

# Display table
st.dataframe(filtered_df, use_container_width=True)

# Download button
csv = filtered_df.to_csv(index=False)
st.download_button("Download Filtered CSV", csv, "tenders_filtered.csv", "text/csv")