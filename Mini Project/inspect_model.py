import spacy
import os

MODEL_DIR = r"C:\Users\Admin\OneDrive\Mini Project\stage2_hierarchical_router"

if os.path.exists(MODEL_DIR):
    nlp = spacy.load(MODEL_DIR)
    doc = nlp("Test billing invoice dispute ticket")
    print("\n📦 --- EXAMINING TRAINED MODEL KEYS ---")
    print("Here are the EXACT keys your model is outputting:")
    for key, value in doc.cats.items():
        print(f"🔑 Key: '{key}' | Raw Probability Value: {value}")
else:
    print("Model directory not found. Please check your path.")