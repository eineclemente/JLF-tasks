import os
import streamlit as st
import pandas as pd
import json
from openai import OpenAI

# Configuration — load key from environment variable
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    st.error("Missing OPENROUTER_API_KEY environment variable. Set it in your .env file.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def extract_lead_data(raw_text):
    """Sends raw text to LLM and returns structured JSON."""
    system_prompt = (
        "You are a strict data extraction engine. Analyze the email and return ONLY a JSON object. "
        "LOGIC FOR sentiment_score: "
        "IF the sender is positive, interested, or excited, THEN set sentiment_score to 10. "
        "ELSE set sentiment_score to 1 (angry/uninterested). "
        "Return this structure: {'client_name': string, 'company_name': string, "
        "'sentiment_score': number, 'budget_range': string, 'summary': string, 'Is_Urgent': Boolean}. "
        "If no client_name is mentioned in the email, set it to the string \"null\". "
        "For 'Is_Urgent': set to true ONLY if the email contains the words 'ASAP' or 'Yesterday', otherwise set to false."
    )

    try:
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract data from this email: {raw_text}"}
            ],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

SENTIMENT_MAP = {10: "Very Excited", 1: "Angry"}

def style_leads(row):
    styles = [''] * len(row)

    # 1. Style the merged Status column
    status_idx = row.index.get_loc('Status')
    if "Excited" in str(row['Status']):
        styles[status_idx] = 'background-color: #28a745; color: white; font-weight: bold;'
    else:
        styles[status_idx] = 'background-color: #dc3545; color: white; font-weight: bold;'

    # 2. Style the Urgency checkbox
    urgent_idx = row.index.get_loc('Is_Urgent')
    if row['Is_Urgent']:
        styles[urgent_idx] = 'color: #d9534f; font-weight: bold;'
    else:
        styles[urgent_idx] = 'color: #6c757d;'

    return styles

# --- UI Setup ---
st.set_page_config(page_title="Lead Parser Pro", page_icon="📥")
st.title("📥 Messy Lead Transformer")
st.markdown("Upload a CSV/XLSX with a column named **'raw_data'** to extract clean JSON leads.")

uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    st.write("Preview of Raw Data:", df.head())

    if st.button("🚀 Process & Extract Leads"):
        if 'raw_data' not in df.columns:
            st.error("Error: The file must contain a column named 'raw_data'.")
        else:
            extracted_leads = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for index, row in df.iterrows():
                status_text.text(f"Processing row {index + 1} of {len(df)}...")
                result = extract_lead_data(row['raw_data'])
                extracted_leads.append(result)

                progress = (index + 1) / len(df)
                progress_bar.progress(progress)

            with open("leads.json", "w") as f:
                json.dump(extracted_leads, f, indent=4)

            # Store results in session state so they persist across reruns
            st.session_state['extracted_leads'] = extracted_leads

    # Display results from session state (fixed, won't re-call LLM on rerun)
    if 'extracted_leads' in st.session_state:
        extracted_leads = st.session_state['extracted_leads']

        st.success("✅ Extraction Complete!")

        results_df = pd.DataFrame(extracted_leads)

        # Merge Score and Label into one column
        results_df['Status'] = results_df['sentiment_score'].map(SENTIMENT_MAP)

        # Keep Is_Urgent as boolean for checkbox display
        results_df['Is_Urgent'] = results_df['Is_Urgent'].apply(lambda x: bool(x))

        st.subheader("Final Lead Analysis")
        st.dataframe(
            results_df.style.apply(style_leads, axis=1),
            use_container_width=True
        )

        json_string = json.dumps(extracted_leads, indent=4)
        st.download_button(
            label="Download leads.json",
            file_name="leads.json",
            mime="application/json",
            data=json_string
        )
