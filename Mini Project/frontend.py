import streamlit as st
import requests
import json


st.set_page_config(page_title="Intelligent Router", layout="wide")

# Custom CSS 
st.markdown("""
    <style>
        /* Base typography and background adjustments */
        .reportview-container .main .block-container {
            padding-top: 2rem;
        }
        h2 {
            font-weight: 600;
            color: #0F172A; /* Slate 900 */
            margin-bottom: 0.25rem;
        }
        p.subtitle {
            color: #475569; /* Slate 600 */
            font-size: 1rem;
            margin-bottom: 2rem;
        }
        /* Style metric blocks to look like clean dashboard cards */
        [data-testid="stMetricSimpleValue"] {
            font-size: 1.5rem !important;
            font-weight: 600 !important;
            color: #1E293B !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748B !important;
        }
    </style>
""", unsafe_allow_html=True)


st.markdown("<h2>Automated Support Ticket Router and Anonymization Engine</h2>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Enterprise Multi-Label NLP Pipeline and Secure PII Vault Core</p>", unsafe_allow_html=True)
st.markdown("---")


col1, col2 = st.columns([5, 6], gap="large")

with col1:
    st.markdown("### Input Customer Support Ticket")
    
    raw_input = st.text_area(
        "Enter raw customer request (include dummy names, credit cards, IPs, or keys to test the PII shield boundaries):",
        height=200,
        placeholder="Type or paste customer conversation records here...",
        label_visibility="collapsed"
    )
    
    
    st.markdown("**Live Presentation Quick-Test Templates:**")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Inject Banking Fraud Ticket", use_container_width=True):
            raw_input = "Hello, I am John Doe. I noticed a highly suspicious unauthorized charge on my debit card 4111-4920-1182-3941 that I did not make. Someone breached my online portfolio using device IP 192.168.1.10. Please place an immediate hold on my account right now."
            st.rerun()
    with btn_col2:
        if st.button("Inject System Outage Ticket", use_container_width=True):
            raw_input = "Our production cluster is completely down and throwing 504 gateway timeout exceptions. The server host terminal is completely unresponsive when attempting to ping the master instance at 192.168.12.5. Please hotfix immediately."
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    submit_button = st.button("Process and Route Ticket", type="primary", use_container_width=True)

with col2:
    st.markdown("### Integrated Pipeline Production Results")
    
    if submit_button:
        if not raw_input.strip():
            st.warning("Please type or inject a support ticket snippet to route.")
        else:
            with st.spinner("Processing through PII Shield and Hierarchical Transformer layers..."):
                try:
                    
                    response = requests.post("http://127.0.0.1:8000/api/v1/route-ticket", json={"text": raw_input})
                    
                    if response.status_code == 200:
                        res_data = response.json()
                        routing = res_data["routing"]
                        payload = res_data["payload"]

                        
                        m_col1, m_col2, m_col3 = st.columns(3)
                        with m_col1:
                            st.metric(label="Assigned Department", value=routing["department"])
                        with m_col2:
                            st.metric(label="Priority Allocation", value=routing["priority_tier"])
                        with m_col3:
                            sentiment_val = payload["sentiment"]
                            sentiment_label = "Positive" if sentiment_val > 0 else "Negative" if sentiment_val < 0 else "Neutral"
                            st.metric(label=f"Sentiment ({sentiment_label})", value=f"{sentiment_val}")

                        st.markdown("---")
                        
                        
                        with st.expander("Smart Classification Analysis Logs", expanded=True):
                            st.write(f"**Micro Sub-Category Intent:** `{routing['sub_category']}`")
                            st.write(f"**Macro Domain Confidence Band:** `{routing['confidence_scores']['macro_score']}`")
                            st.write(f"**Micro Intent Confidence Band:** `{routing['confidence_scores']['micro_score']}`")
                            st.write(f"**Calculated Urgency Score Metric:** `{payload['score']} / 12.0`")

                        
                        st.markdown("**Redacted and Masked Content Payload (Zero Data Leakage Queue):**")
                        st.info(payload["anonymized_content"], icon=None)

                        
                        with st.expander("Isolated PII Decoupling Vault (Secure Ledger Mapping)", expanded=True):
                            if payload["pii_vault"]:
                                st.json(payload["pii_vault"])
                            else:
                                st.write("No active sensitive elements or high-risk identifiers detected inside the core string.")
                                
                        
                        with st.expander("View Complete JSON Inter-Service Output Contract"):
                            st.code(json.dumps(res_data, indent=4), language="json")

                except requests.exceptions.ConnectionError:
                    st.error("Could not bridge interface connections. Please confirm that the FastAPI backend API script (backend.py) is successfully compiled and active on port 8000.")
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        st.text("Awaiting processing actions. Submit an incoming text sample on the left panel to execute real-time parsing layers.")