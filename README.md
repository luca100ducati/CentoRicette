# 🍲 Centoricette

**Centoricette** è una web application intelligente progettata per rivoluzionare l'organizzazione della cucina familiare. Unisce la gestione della dispensa, il calcolo del fabbisogno calorico e la potenza dell'Intelligenza Artificiale per creare menù settimanali su misura, azzerare gli sprechi e semplificare la spesa.

---

## ✨ Funzionalità Principali

* 📦 **Dispensa Dinamica:** Cataloga i tuoi ingredienti in Freschi, Freezer, Scatolame e Base. Un semplice interruttore ti permette di indicare se un prodotto è disponibile o esaurito.
* 🛒 **Lista della Spesa Automatica:** Gli alimenti contrassegnati come "esauriti" in dispensa finiscono automaticamente nel carrello virtuale. Spuntali mentre sei al supermercato per rimetterli istantaneamente in dispensa.
* 👨‍👩‍👧‍👦 **Profili Familiari & Calcolo Kcal:** Inserisci i dati dei membri della tua famiglia (età, peso, altezza, livello di attività). L'app calcola in automatico il fabbisogno calorico giornaliero (TDEE) di ciascuno.
* 🤖 **Chef IA (Powered by Gemini):** Genera al volo singole ricette o interi menù settimanali (pranzo e cena) basandosi **esclusivamente** sugli ingredienti che hai realmente a disposizione in casa. 
* ⚖️ **Porzionamento Matematico:** Addio "porzioni a occhio". L'app calcola i moltiplicatori esatti per ogni pasto, distribuendo le calorie in modo corretto tra atleti, adulti e bambini.
* 🎲 **Rimescola Pasto (Shuffle):** Non ti piace il pranzo proposto per mercoledì? Premi un tasto e l'IA rigenererà solo quel pasto, mantenendo intatto il resto del calendario.
* ⭐ **Ricettario & Valutazioni:** Salva le ricette migliori proposte dall'IA, consulta i passaggi di preparazione e votale da 1 a 5 stelle per costruire il tuo libro di cucina definitivo.
* 🖨️ **Stampa Menù A4:** Esporta il menù settimanale confermato in un formato pulito e printer-friendly, perfetto da appendere al frigorifero.

---

## 🛠️ Tecnologie Utilizzate

* **Frontend & Backend:** [NiceGUI](https://nicegui.io/) (Python) - Framework reattivo per interfacce web fluide.
* **Database:** [Supabase](https://supabase.com/) (PostgreSQL) - Per il salvataggio in cloud in tempo reale di ingredienti, profili e ricette.
* **Intelligenza Artificiale:** [Google Gemini 3.5 Flash](https://aistudio.google.com/) - Tramite SDK `google.generativeai` per la generazione rapida di ricette in formato JSON strutturato.

---

## 🚀 Installazione Locale

Se vuoi far girare il progetto sul tuo computer, segui questi passaggi:

### 1. Clona la repository
```bash
git clone [https://github.com/TUO-USERNAME/Centoricette.git](https://github.com/TUO-USERNAME/Centoricette.git)
cd Centoricette
