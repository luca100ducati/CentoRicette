def calcola_porzioni(membri_attivi: list, kcal_totali_ricetta: int) -> dict:
    # 1. Calcola il target totale della famiglia per quel pasto
    kcal_target_totali = sum(membro['kcal_target'] for membro in membri_attivi)
    
    porzioni_calcolate = {}
    
    # 2. Crea il rapporto per ciascuno
    for membro in membri_attivi:
        percentuale = membro['kcal_target'] / kcal_target_totali
        kcal_assegnate = kcal_totali_ricetta * percentuale
        
        # Traduciamo le Kcal in una frazione visiva rispetto alla media
        # Se 1 è la porzione "media", calcoliamo quanto mangia rispetto alla media
        moltiplicatore = (membro['kcal_target'] / (kcal_target_totali / len(membri_attivi)))
        
        porzioni_calcolate[membro['nome']] = round(moltiplicatore, 1)
        
    return porzioni_calcolate


def calcola_fabbisogno_giornaliero(sesso: str, peso: float, altezza: float, eta: int, fattore_attivita: float) -> int:
    """Calcola le Kcal giornaliere usando la formula Mifflin-St Jeor."""
    
    # Gestione semplificata per i bambini piccoli (fabbisogni standard pediatrici)
    if eta <= 3:
        return 1200
    elif eta <= 10:
        return 1600
    
    # Formula per adulti e adolescenti
    if sesso.upper() == 'M':
        metabolismo_basale = (10 * peso) + (6.25 * altezza) - (5 * eta) + 5
    else:
        metabolismo_basale = (10 * peso) + (6.25 * altezza) - (5 * eta) - 161
        
    tdee = metabolismo_basale * fattore_attivita
    return int(tdee)

def ottieni_kcal_pasto(fabbisogno_giornaliero: int, tipo_pasto: str) -> int:
    """Divide il fabbisogno giornaliero nel pasto specifico."""
    # Una ripartizione classica ed equilibrata
    ripartizione = {
        'colazione': 0.20, # 20%
        'pranzo': 0.40,    # 40%
        'cena': 0.40       # 40%
    }
    
    percentuale = ripartizione.get(tipo_pasto.lower(), 0.33)
    return int(fabbisogno_giornaliero * percentuale)

def calcola_moltiplicatori_porzioni(membri_attivi: list, tipo_pasto: str) -> dict:
    """Restituisce quanto deve mangiare ogni persona rispetto alla porzione media (1.0)."""
    kcal_pasto_membri = {}
    totale_kcal_pasto = 0
    
    # Calcoliamo le Kcal per il pasto di ciascuno
    for membro in membri_attivi:
        kcal_giornaliere = calcola_fabbisogno_giornaliero(
            membro['sesso'], membro['peso_kg'], membro['altezza_cm'], 
            membro['eta'], membro['fattore_attivita']
        )
        kcal_pasto = ottieni_kcal_pasto(kcal_giornaliere, tipo_pasto)
        kcal_pasto_membri[membro['nome']] = kcal_pasto
        totale_kcal_pasto += kcal_pasto
        
    # Calcoliamo la media matematica del pasto
    media_kcal = totale_kcal_pasto / len(membri_attivi)
    
    # Creiamo i moltiplicatori
    moltiplicatori = {}
    for nome, kcal in kcal_pasto_membri.items():
        # Arrotondiamo a 1 decimale (es. 1.2x, 0.8x)
        moltiplicatori[nome] = round(kcal / media_kcal, 1)
        
    return moltiplicatori