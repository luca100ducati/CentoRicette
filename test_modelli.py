import os
import google.generativeai as genai
from dotenv import load_dotenv

# Carica la chiave API dal tuo file .env
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("Modelli disponibili per la generazione di testo:")
print("-" * 40)

# Scorre tutti i modelli associati alla tua chiave e li stampa
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)