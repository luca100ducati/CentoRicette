import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiChef:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Errore: GEMINI_API_KEY non trovata nel file .env")
        genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel(
            model_name="gemini-3.5-flash",
            generation_config={"temperature": 0.7, "response_mime_type": "application/json"}
        )

   
    def genera_ricetta(self, ingredienti_disponibili: list) -> dict:
        lista_ingredienti = ", ".join(ingredienti_disponibili)
        prompt = f"""
        Crea UNA singola ricetta usando principalmente questi ingredienti: {lista_ingredienti}.
        Puoi aggiungere ingredienti di base come sale, olio e spezie.
        IMPORTANTE: Se non includi il campo "istruzioni" completo di tutti i passaggi di preparazione, il JSON non sarà valido. NON omettere mai le istruzioni.
        Restituisci SOLO un JSON con questa struttura esatta:
        {{
            "titolo": "Nome della Ricetta",
            "descrizione": "Breve descrizione",
            "tempo_preparazione_min": 30,
            "kcal_totali": 1500,
            "istruzioni": "1. Taglia le verdure. 2. Cuoci per 10 minuti. 3. Servi."
        }}
        """
        try:
            risposta = self.model.generate_content(prompt)
            return json.loads(risposta.text)
        except Exception as e:
            print(f"Errore AI singola: {e}")
            return {}


    def genera_settimana(self, ingredienti_disponibili: list, max_min_pranzi: int, max_min_cene: int) -> dict:
        lista_ingredienti = ", ".join(ingredienti_disponibili)
        prompt = f"""
        Crea un menu settimanale per famiglia (Lunedì-Domenica), 7 pranzi e 7 cene.
        REGOLE:
        1. TEMPO: Pranzi max {max_min_pranzi} min. Cene max {max_min_cene} min.
        2. INGREDIENTI: Usa principalmente {lista_ingredienti}. Aggiungi basi (sale, olio, spezie).
        IMPORTANTE: Se non includi il campo "istruzioni" completo di tutti i passaggi di preparazione, il JSON non sarà valido. NON omettere mai le istruzioni.
        Restituisci SOLO un JSON con questa struttura esatta:
        {{
            "lunedi": {{
                "pranzo": {{"titolo": "Pasta al pomodoro", "tempo_min": 15, "kcal_totali": 2100, "istruzioni": "1. Cuoci... 2. Scola..."}},
                "cena": {{"titolo": "Pollo e Zucchine", "tempo_min": 45, "kcal_totali": 2600, "istruzioni": "1. Taglia... 2. Inforna..."}}
            }}
        }}        
        """
        try:
            risposta = self.model.generate_content(prompt)
            return json.loads(risposta.text)
        except Exception as e:
            print(f"Errore AI: {e}")
            return {}

    def rimescola_pasto(self, ingredienti_disponibili: list, tipo_pasto: str, max_min: int, pasto_escluso: str) -> dict:
        lista_ingredienti = ", ".join(ingredienti_disponibili)
        prompt = f"""
        Crea UNA singola ricetta per {tipo_pasto} in max {max_min} min.
        SCARTA QUESTA RICETTA: {pasto_escluso}.
        Usa: {lista_ingredienti}.
        IMPORTANTE: Se non includi il campo "istruzioni" completo di tutti i passaggi di preparazione, il JSON non sarà valido. NON omettere mai le istruzioni.
        Restituisci SOLO JSON:
        {{ "titolo": "Nuova Ricetta", "tempo_min": 30, "kcal_totali": 2200 }}
        """
        try:
            risposta = self.model.generate_content(prompt)
            return json.loads(risposta.text)
        except:
            return {}