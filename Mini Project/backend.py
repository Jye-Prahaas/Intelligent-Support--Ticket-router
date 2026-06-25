from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from textblob import TextBlob
import spacy
import re
import os
import random

app = FastAPI(
    title="Enterprise ML Support Router & Advanced Privacy Shield",
    description="Production API with case-insensitive name masking, phone, and address structural isolation.",
    version="2.0.0"
)

MODEL_DIR = "stage2_hierarchical_router"

# --- INIT CORE NLP ENGINE & HIERARCHICAL MODEL ---
try:
    nlp = spacy.load("en_core_web_sm")
except:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

if os.path.exists(MODEL_DIR):
    print(f"🧠 Loading hierarchical model weights from '{MODEL_DIR}' into system memory...")
    hierarchical_model = spacy.load(MODEL_DIR)
else:
    print(f"⚠️ Warning: '{MODEL_DIR}' folder not found locally. API will default to manual routing fallback.")
    hierarchical_model = None

# --- PRODUCTION HIERARCHICAL COHERENCE CONTRACT ---
HIERARCHICAL_MAPPING = {
    "Loan_Inquiry": "Banking",
    "Fraud_Alert": "Banking",
    "Server_Down": "Technical",
    "Order_Tracking": "E-Commerce",
    "Cancelled_Order": "E-Commerce",
    "KYC_Verification": "Account",
    "Double_Charge": "Billing",
    "Pharmacy_Refill": "Healthcare",
    "Feedback": "General"
}

class TicketRequest(BaseModel):
    text: str

# --- PIPELINE COMPONENTS ---
def pre_clean_spaces(text: str) -> str:
    # Standardizes numerical sequencing space variations prior to extraction execution
    text = re.sub(r'\+(\d+)', r'\1', text)
    text = re.sub(r'(\d{4})[\s-]+(\d{4})[\s-]+(\d{4})[\s-]+(\d{4})', r'\1\2\3\4', text)
    text = re.sub(r'(\d+)[\s-]+(\d+)[\s-]+(\d+)', r'\1\2\3', text)
    text = re.sub(r'(\d+)[\s-]+(\d+)', r'\1\2', text)
    return text

def pii_shield_v5_ultimate(text: str):
    cleaned_text = pre_clean_spaces(text)
    pii_vault = {}
    all_intervals = []
    
    # Structural entity exclusions to prevent false positive masking over core operational terms
    noun_blacklist = {"phone", "email", "card", "mobile", "user", "ticket", "id", "customer", "ip", "address", "order"}

    # 1. UPGRADED REGEX PATTERNS WITH CASE-INSENSITIVE CONTEXT-AWARE NAME CAPTURING
    patterns = {
        "[KEY]": r'(?i)(?:api[_-]?key|passwd|password|secret|token|auth|key)[:=]\s*([a-zA-Z0-9_\-\.]{16,})',
        "[SECRET]": r'\b[A-Za-z0-9/+=]{20,}\b',
        "[MAIL]": r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b',
        "[PHONE]": r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        "[CARD]": r'\b\d{13,16}\b|\b(?:\d{4}[-\s]?){3}\d{4}\b',
        "[IP]": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        # Case-insensitive contextual name capturing array (Catches lowercase/uppercase trailing tokens)
        "[NAME_CONTEXT]": r'(?i)\b(?:my name is|i am|call me|this is|speaking with|attending to)\s+([a-zA-Z]{2,15})\b'
    }

    # Extract deterministic expressions with absolute Top Priority (Weight = 1)
    for label, pattern in patterns.items():
        for match in re.finditer(pattern, cleaned_text):
            if label == "[NAME_CONTEXT]":
                start_idx = match.start(1)
                end_idx = match.end(1)
                matched_val = match.group(1)
                target_label = "[NAME]"
            else:
                start_idx = match.start()
                end_idx = match.end()
                matched_val = match.group(0)
                target_label = label
                
            if matched_val.lower().strip() not in noun_blacklist:
                all_intervals.append((start_idx, end_idx, target_label, matched_val, 1))

    # 2. STATISTICAL MULTI-LAYER NLP ENGINE WITH EXPLICIT COLLISION BLOCKING
    doc = nlp(cleaned_text)
    
    # Comprehensive label translation array including Geopolitical addresses & Facilities
    label_map = {
        "PERSON": "[NAME]", 
        "DATE": "[DATE]", 
        "TIME": "[DATE]", 
        "GPE": "[ADDRESS]", 
        "FAC": "[ADDRESS]", 
        "LOC": "[ADDRESS]",
        "CARDINAL": "[NUMBER]", 
        "MONEY": "[NUMBER]"
    }

    # Extract statistical entities from the spaCy graph
    for ent in doc.ents:
        if ent.label_ in label_map and ent.text.lower().strip() not in noun_blacklist:
            # Enforce the hierarchy rule: Check if this space was already occupied by an explicit pattern match
            overlap = any(max(start, ent.start_char) < min(end, ent.end_char) for start, end, _, _, priority in all_intervals if priority == 1)
            
            if not overlap:
                all_intervals.append((ent.start_char, ent.end_char, label_map[ent.label_], ent.text, 2))

    # 3. INTERCEPT REMAINING UNCAUGHT UPPERCASE PROPER NOUNS (Secondary Guard)
    for token in doc:
        if token.pos_ == "PROPN" and token.text.lower().strip() not in noun_blacklist:
            # Verify the token is not already registered under existing interval spans
            exists = any(max(start, token.idx) < min(end, token.idx + len(token.text)) for start, end, _, _, _ in all_intervals)
            if not exists and len(token.text) > 1:
                all_intervals.append((token.idx, token.idx + len(token.text), "[NAME]", token.text, 3))

    # 4. REVERSE ORDER INTERVAL SORTING (Prevents index-drift corruption during text substitution)
    all_intervals.sort(key=lambda x: (-x[0], x[4]))

    masked_text = cleaned_text
    last_processed_start = len(cleaned_text) + 1

    for start, end, label, original_val, priority in all_intervals:
        if end <= last_processed_start:
            if label not in pii_vault:
                pii_vault[label] = []
            if original_val.strip() not in pii_vault[label]:
                pii_vault[label].append(original_val.strip())
            masked_text = masked_text[:start] + label + masked_text[end:]
            last_processed_start = start

    return re.sub(r'\s+', ' ', masked_text).strip(), pii_vault

def predict_intent(text: str):
    if not hierarchical_model:
        return {
            "primary_intent": "Unclassified / Human Review",
            "primary_confidence": "0.00%",
            "sub_intent": "Requires Manual Assignment",
            "sub_confidence": "0.00%"
        }
    
    doc = hierarchical_model(text)
    if not doc.cats:
        return {
            "primary_intent": "Unclassified / Human Review",
            "primary_confidence": "0.00%",
            "sub_intent": "Requires Manual Assignment",
            "sub_confidence": "0.00%"
        }

    macro_cats = {k: v for k, v in doc.cats.items() if "_" not in k}
    micro_cats = {k: v for k, v in doc.cats.items() if "_" in k}

    best_p = max(macro_cats, key=macro_cats.get) if macro_cats else "Unclassified / Human Review"
    p_conf = macro_cats[best_p] if macro_cats else 0.0

    best_s = max(micro_cats, key=micro_cats.get) if micro_cats else "Requires Manual Assignment"
    s_conf = micro_cats[best_s] if micro_cats else 0.0

    return {
        "primary_intent": best_p,
        "primary_confidence": f"{p_conf:.2%}",
        "sub_intent": best_s,
        "sub_confidence": f"{s_conf:.2%}"
    }

def stage_3_priority_with_sentiment(text: str, final_intent: str):
    sentiment = TextBlob(text).sentiment.polarity
    base_scores = {"Healthcare": 5.0, "Banking": 4.5, "Technical": 3.0, "E-Commerce": 2.5, "Account": 2.5, "Refund": 2.5, "Billing": 2.5, "General": 2.0, "Unclassified / Human Review": 2.0}
    priority_score = base_scores.get(final_intent, 2.0)

    urgency_map = {"EMERGENCY": 5.0, "CRITICAL": 4.0, "URGENT": 3.0, "IMMEDIATE": 3.5, "ASAP": 2.5, "RIGHT NOW": 2.5, "FRAUD": 4.0, "UNAUTHORIZED": 3.5, "BREACHED": 4.0}
    for word, boost in urgency_map.items():
        if word in text.upper():
            priority_score += boost

    if sentiment < 0:
        priority_score += abs(sentiment) * 5.0

    tier = "P1 - Critical" if priority_score >= 9.0 else "P2 - High" if priority_score >= 6.0 else "P3 - Normal"
    return {"final_score": round(priority_score, 2), "sentiment_detected": round(sentiment, 2), "target_tier": tier}

# --- ENDPOINT ORCHESTRATION ---
@app.post("/api/v1/route-ticket")
async def process_ticket(request: TicketRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Ticket content cannot be empty.")
    
    # 1. CONTEXT-PURE MACHINE LEARNING INFERENCE 
    intent_data = predict_intent(request.text)
    raw_macro_confidence = float(intent_data['primary_confidence'].strip('%'))
    
    final_intent = intent_data['primary_intent']
    final_sub_intent = intent_data['sub_intent']

    # 2. HIERARCHICAL CONTRACT ALIGNMENT CHECK
    if final_sub_intent in HIERARCHICAL_MAPPING:
        final_intent = HIERARCHICAL_MAPPING[final_sub_intent]

    # --- NOISE ISOLATION SAFETY FILTER ---
    if raw_macro_confidence < 0.15:
        final_intent = "Unclassified / Human Review"
        final_sub_intent = "Requires Manual Assignment"
        masked_text, pii_vault = pii_shield_v5_ultimate(request.text)
        
        return {
            "ticket_id": f"SR-{random.randint(100, 999)}",
            "routing": {
                "department": final_intent,
                "sub_category": final_sub_intent,
                "priority_tier": "P3 - Normal",
                "confidence_scores": {
                    "macro_score": intent_data['primary_confidence'],
                    "micro_score": intent_data['sub_confidence']
                }
            },
            "payload": {
                "score": 2.0,
                "sentiment": 0.0,
                "anonymized_content": masked_text,
                "pii_vault": pii_vault
            }
        }

    # 3. SECURE PAYLOAD MASK PROCESSING (Scores >= 0.15%)
    masked_text, pii_vault = pii_shield_v5_ultimate(request.text)

    # 4. SERVICE LAYER ESCALATION ANALYSIS
    priority_data = stage_3_priority_with_sentiment(request.text, final_intent)

    return {
        "ticket_id": f"SR-{random.randint(100, 999)}",
        "routing": {
            "department": final_intent,
            "sub_category": final_sub_intent,
            "priority_tier": priority_data['target_tier'],
            "confidence_scores": {
                "macro_score": intent_data['primary_confidence'],
                "micro_score": intent_data['sub_confidence']
            }
        },
        "payload": {
            "score": priority_data['final_score'],
            "sentiment": priority_data['sentiment_detected'],
            "anonymized_content": masked_text,
            "pii_vault": pii_vault
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)