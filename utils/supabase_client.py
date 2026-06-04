import os
from typing import List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

class CentoricetteDB:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL", "")
        key: str = os.environ.get("SUPABASE_KEY", "")
        
        if not url or not key:
            raise ValueError("Errore: SUPABASE_URL e SUPABASE_KEY devono essere impostate nel file .env")
        
        self.client: Client = create_client(url, key)

    # --- GESTIONE MEMBRI FAMIGLIA ---
    def ottieni_membri(self) -> List[Dict[str, Any]]:
        """Recupera tutti i componenti della famiglia attivi."""
        risposta = self.client.table("membri_famiglia").select("*").eq("attivo", True).execute()
        return risposta.data

    def aggiorna_kcal_membro(self, membro_id: str, nuove_kcal: int) -> List[Dict[str, Any]]:
        """Aggiorna il target calorico di un membro."""
        risposta = self.client.table("membri_famiglia").update({"kcal_target": nuove_kcal}).eq("id", membro_id).execute()
        return risposta.data

    # --- GESTIONE INGREDIENTI (DISPENSA VELOCE) ---
    def ottieni_ingredienti_per_categoria(self, categoria: str) -> List[Dict[str, Any]]:
        """Recupera gli ingredienti di una determinata categoria (es. 'freschi')."""
        risposta = self.client.table("ingredienti").select("*").eq("categoria", categoria).order("nome").execute()
        return risposta.data

    def toggle_disponibilita_ingrediente(self, ingrediente_id: str, in_casa: bool) -> List[Dict[str, Any]]:
        """
        Cambia istantaneamente lo stato dell'ingrediente (In casa True/False).
        Ottimo per la UX dei freschi che vanno e vengono.
        """
        import datetime
        ora_attuale = datetime.datetime.now(datetime.timezone.utc).isoformat()
        risposta = self.client.table("ingredienti").update({
            "in_casa": in_casa,
            "ultimo_aggiornamento": ora_attuale
        }).eq("id", ingrediente_id).execute()
        return risposta.data

    def ottieni_ingredienti_disponibili(self) -> List[str]:
        """Ritorna una lista di stringhe con i nomi di tutto ciò che è 'in_casa' per darlo in pasto all'AI."""
        risposta = self.client.table("ingredienti").select("nome").eq("in_casa", True).execute()
        return [item['nome'] for item in risposta.data]

    def aggiungi_nuovo_ingrediente_anagrafica(self, nome: str, categoria: str) -> List[Dict[str, Any]]:
        """Aggiunge un nuovo ingrediente di base al database se non esiste."""
        risposta = self.client.table("ingredienti").insert({"nome": nome.lower(), "categoria": categoria}).execute()
        return risposta.data

    def elimina_ingrediente(self, ingrediente_id: str) -> bool:
        """Elimina definitivamente un ingrediente dal database."""
        try:
            self.client.table("ingredienti").delete().eq("id", ingrediente_id).execute()
            return True
        except Exception as e:
            print(f"Errore durante l'eliminazione: {e}")
            return False

# --- GESTIONE NUCLEO FAMIGLIARE ---
    def aggiungi_membro_famiglia(self, nome: str, sesso: str, eta: int, peso_kg: float, altezza_cm: float, fattore_attivita: float, kcal_target: int) -> bool:
        """Salva un nuovo membro e il suo fabbisogno giornaliero totale."""
        dati = {
            "nome": nome.capitalize(),
            "sesso": sesso,
            "eta": eta,
            "peso_kg": peso_kg,
            "altezza_cm": altezza_cm,
            "fattore_attivita": fattore_attivita,
            "kcal_target": kcal_target,
            "attivo": True
        }
        try:
            self.client.table("membri_famiglia").insert(dati).execute()
            return True
        except Exception as e:
            print(f"Errore durante l'aggiunta del membro: {e}")
            return False

    def elimina_membro(self, id_membro: str) -> bool:
        """Rimuove un membro dal database."""
        try:
            self.client.table("membri_famiglia").delete().eq("id", id_membro).execute()
            return True
        except Exception as e:
            print(f"Errore durante l'eliminazione del membro: {e}")
            return False


    # --- GESTIONE RICETTE ---
    def salva_ricetta(self, titolo: str, descrizione: str, istruzioni: str, tempo_min: int, kcal_totali: int, da_ai: bool = True) -> Dict[str, Any]:
        """Salva una nuova ricetta nel database."""
        dati_ricetta = {
            "titolo": titolo,
            "descrizione": descrizione,
            "istruzioni": istruzioni,
            "tempo_preparazione_min": tempo_min,
            "kcal_totali": kcal_totali,
            "creato_da_ai": da_ai
        }
        risposta = self.client.table("ricette").insert(dati_ricetta).execute()
        return risposta.data[0] if risposta.data else {}

    def valuta_ricetta(self, ricetta_id: str, voto: int) -> List[Dict[str, Any]]:
        """Salva il gradimento della famiglia (Feature futura)."""
        risposta = self.client.table("ricette").update({"voto": voto}).eq("id", ricetta_id).execute()
        return risposta.data

    # --- CALENDARIO PASTI ---
    def assegna_ricetta_a_calendario(self, data_pasto: str, tipo: str, ricetta_id: str, note: str = "") -> List[Dict[str, Any]]:
        """Inserisce o aggiorna un pasto nel calendario settimanale."""
        dati = {
            "data": data_pasto,
            "pasto": tipo,
            "ricetta_id": ricetta_id,
            "note": note
        }
        # Utilizza l'upsert basandosi sulla chiave unica (data, pasto)
        risposta = self.client.table("calendario_pasti").upsert(dati, on_conflict="data,pasto").execute()
        return risposta.data

    def salva_menu_settimanale(self, dati_menu: dict) -> bool:
        """Salva il JSON del menu settimanale, sovrascrivendo il precedente."""
        try:
            # Prima svuotiamo la tabella per tenere solo il menu attivo
            self.client.table('menu_settimanale').delete().neq('id', 0).execute()
            # Poi inseriamo il nuovo
            self.client.table('menu_settimanale').insert({'dati_menu': dati_menu}).execute()
            return True
        except Exception as e:
            print(f"Errore salvataggio menu settimanale: {e}")
            return False

    def ottieni_menu_settimanale(self) -> dict:
        """Recupera l'ultimo menu settimanale salvato, se esiste."""
        try:
            risposta = self.client.table('menu_settimanale').select('*').order('data_salvataggio', desc=True).limit(1).execute()
            if risposta.data:
                return risposta.data[0]['dati_menu']
            return {}
        except Exception as e:
            print(f"Errore recupero menu settimanale: {e}")
            return {}

    def elimina_menu_settimanale(self) -> bool:
        """Cancella il calendario per iniziare una nuova settimana."""
        try:
            self.client.table('menu_settimanale').delete().neq('id', 0).execute()
            return True
        except Exception as e:
            print(f"Errore eliminazione menu: {e}")
            return False

    def ottieni_tutte_le_ricette(self):
        """Recupera le ricette salvate."""
        risposta = self.client.table("ricette").select("*").execute()
        return risposta.data

    def valuta_ricetta(self, ricetta_id: str, voto: int) -> bool:
        """Aggiorna il voto in stelle di una ricetta salvata."""
        try:
            self.client.table('ricette').update({'valutazione': voto}).eq('id', ricetta_id).execute()
            return True
        except Exception as e:
            print(f"Errore salvataggio valutazione: {e}")
            return False

    def ottieni_ingredienti_esauriti(self):
        """Recupera tutti gli ingredienti con in_casa = False per la lista spesa."""
        try:
            risposta = self.client.table('ingredienti').select('*').eq('in_casa', False).execute()
            return risposta.data
        except Exception as e:
            print(f"Errore recupero lista spesa: {e}")
            return []

    def elimina_ricetta(self, id_ricetta: str) -> bool:
        """Elimina definitivamente una ricetta dal ricettario."""
        try:
            self.client.table('ricette').delete().eq('id', id_ricetta).execute()
            return True
        except Exception as e:
            print(f"Errore durante l'eliminazione della ricetta: {e}")
            return False

if __name__ == "__main__":
    # Test rapido di inizializzazione
    try:
        db = CentoricetteDB()
        print("Connessione a Supabase completata con successo!")
    except Exception as e:
        print(f"Errore durante la connessione: {e}")


