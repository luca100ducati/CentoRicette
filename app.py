from nicegui import ui
import json
from ai_chef import GeminiChef 
from utils.supabase_client import CentoricetteDB
from calcolatore import calcola_fabbisogno_giornaliero, calcola_moltiplicatori_porzioni

# Inizializzazioni
chef = GeminiChef()
try:
    db = CentoricetteDB()
except Exception as e:
    print(f"ATTENZIONE: Errore connessione Supabase. Controlla il file .env. Errore: {e}")

# ==========================================
# 1. PARAMETRI GLOBALI
# ==========================================
PAGE_CLASSES = 'w-full max-w-sm mx-auto p-4 bg-green-50 min-h-screen shadow-lg relative pb-40' 
TITLE_CLASSES = 'text-3xl font-extrabold text-green-900 mb-1'
SUBTITLE_CLASSES = 'text-green-700 text-sm mb-4 font-medium'
PANEL_CLASSES = 'w-full bg-white rounded-xl shadow-sm border border-green-200 p-3 mb-6'
TOGGLE_PROPS = 'color=primary size=lg left-label class="justify-between text-base text-gray-800 m-0"'
BUTTON_AI_CLASSES = 'w-full text-white font-bold py-4 shadow-lg transition hover:scale-105 text-lg'
INPUT_CLASSES = 'w-full mb-2'
INPUT_PROPS = 'outlined color=accent bg-color=white dense'
BUTTON_CLASSES = 'w-full text-white font-bold py-3 mt-1 shadow-md transition hover:scale-105'
BUTTON_PROPS = 'color=accent rounded-lg'

MAPPA_CATEGORIE = {'Freschi': 'freschi', 'Congelatore': 'congelatore', 'Scatolame': 'scatolame', 'Sempre Presenti': 'sempre_presenti'}
OPZIONI_SELECT_DISPENSA = {'freschi': '🍅 Freschi', 'congelatore': '🧊 Freezer', 'scatolame': '🥫 Dispensa', 'sempre_presenti': '🌾 Base'}

def non_validi(lista_valori): return any(v is None or v <= 0 for v in lista_valori)

# ==========================================
# 2. FUNZIONI DI TEMA E NAVIGAZIONE
# ==========================================
def applica_tema():
    ui.colors(primary='#4caf50', secondary='#81c784', accent='#2e7d32', positive='#66bb6a')
    ui.query('body').classes('p-0 m-0 bg-gray-100')
    with ui.footer().classes('bg-white border-t border-green-200 p-2 flex justify-around shadow-[0_-10px_15px_-3px_rgba(0,0,0,0.1)] z-50'):
        ui.button(icon='kitchen', on_click=lambda: ui.navigate.to('/')).props('flat color=primary size=sm')
        ui.button(icon='shopping_cart', on_click=lambda: ui.navigate.to('/spesa')).props('flat color=primary size=sm')
        ui.button(icon='group', on_click=lambda: ui.navigate.to('/famiglia')).props('flat color=primary size=sm')
        ui.button(icon='calendar_month', on_click=lambda: ui.navigate.to('/calendario')).props('flat color=primary size=sm')
        ui.button(icon='star', on_click=lambda: ui.navigate.to('/preferiti')).props('flat color=primary size=sm')# PAGINA 1: DISPENSA E RICETTA SINGOLA


# ==========================================
@ui.page('/')
def pagina_dispensa():
    applica_tema()
    with ui.column().classes(PAGE_CLASSES):
        ui.image('logo_100r.png').classes('w-full mb-3 drop-shadow-none')
        ui.label('Aggiungi gli alimenti alla dispensa e crea le ricette.').classes(SUBTITLE_CLASSES)
        
        @ui.refreshable
        def renderizza_dispensa():
            categoria_corrente = menu_categoria.value
            ingredienti = db.ottieni_ingredienti_per_categoria(categoria_corrente)
            with ui.column().classes('w-full gap-0').props('dense'):
                if not ingredienti:
                    ui.label("Nessun ingrediente.").classes("text-gray-400 italic py-4 text-center w-full")
                    return
                for ing in ingredienti:
                    with ui.row().classes('w-full items-center justify-between border-b border-gray-100 py-1 flex-nowrap').props('dense'):
                        ui.switch(ing['nome'].capitalize(), value=ing['in_casa'], on_change=lambda e, id_ing=ing['id']: db.toggle_disponibilita_ingrediente(id_ing, e.value)).props(TOGGLE_PROPS).classes('col-grow truncate')
                        ui.button(icon='delete', on_click=lambda id_ing=ing['id'], nome_ing=ing['nome']: (db.elimina_ingrediente(id_ing), renderizza_dispensa.refresh())).props('flat color=negative dense round').classes('flex-shrink-0 ml-1')

        menu_categoria = ui.select(OPZIONI_SELECT_DISPENSA, value='freschi', on_change=lambda: renderizza_dispensa.refresh()).classes('w-full mb-2 text-lg font-bold').props('outlined color=primary bg-color=white')
        with ui.card().classes(PANEL_CLASSES): renderizza_dispensa()

        ui.separator().classes('my-2 bg-green-200 w-full h-px')
        ui.label('➕ Aggiungi al volo').classes('text-xl font-extrabold text-green-900 mb-2')
        with ui.row().classes('w-full items-end gap-2'):
            with ui.column().classes('col-grow gap-0'):
                nuovo_ing = ui.input('Nome alimento').classes(INPUT_CLASSES).props(INPUT_PROPS)
                cat_scelta = ui.select(list(MAPPA_CATEGORIE.keys()), value='Freschi', label='Categoria').classes(INPUT_CLASSES).props(INPUT_PROPS)
            with ui.column().classes('w-24 pb-2'):
                ui.button('Salva', on_click=lambda: (db.aggiungi_nuovo_ingrediente_anagrafica(nuovo_ing.value, MAPPA_CATEGORIE[cat_scelta.value]), renderizza_dispensa.refresh(), nuovo_ing.set_value(''))).classes(BUTTON_CLASSES).props(BUTTON_PROPS)

        # --- SEZIONE RISULTATO RICETTA ---
        contenitore_ricetta = ui.column().classes('w-full gap-2 mt-4 pb-10')

        async def chiedi_all_ia(e):
            in_casa = db.ottieni_ingredienti_disponibili()
            if not in_casa: return ui.notify("Nessun ingrediente disponibile!", type="warning")
            ui.notify('Chef IA al lavoro...', type='info', position='top')
            e.sender.props('loading') 
            
            import asyncio
            loop = asyncio.get_running_loop()
            ricetta = await loop.run_in_executor(None, chef.genera_ricetta, in_casa)
            
            e.sender.props(remove='loading')
            contenitore_ricetta.clear()

            with contenitore_ricetta:
                if "titolo" in ricetta:
                    with ui.card().classes('w-full bg-white shadow-xl border-t-4 border-accent mb-6'):
                        ui.label(ricetta["titolo"]).classes('text-2xl font-bold text-gray-800 leading-tight')
                        ui.label(ricetta.get("descrizione", "")).classes('text-sm text-gray-500 italic mb-2')
                        
                        # Calcolo sicuro dei valori per evitare problemi al DB
                        tempo_sicuro = int(ricetta.get("tempo_preparazione_min", ricetta.get("tempo_min", 0)))
                        kcal_sicure = int(ricetta.get("kcal_totali", 0))

                        with ui.row().classes('w-full justify-between bg-green-50 p-2 rounded-lg mb-2'):
                            ui.label(f'⏱️ {tempo_sicuro} min').classes('font-bold text-accent')
                            ui.label(f'🔥 {kcal_sicure} Kcal').classes('font-bold text-accent')
                        
                        ui.label('Istruzioni:').classes('font-bold mt-2 text-gray-700')
                        istruzioni_lista = ricetta.get("istruzioni", "").split('. ')
                        for step in istruzioni_lista:
                            if step.strip(): ui.label(f"• {step.strip()}").classes('text-gray-800 text-base mb-1')
                        
                        # --- PREFERITI E VALUTAZIONE SICURA ---
                        with ui.row().classes('w-full items-center justify-between mt-4 bg-gray-50 border border-gray-200 p-2 rounded-lg flex-nowrap'):
                            cont_valutazione = ui.row().classes('items-center gap-2')
                            
                            def salva_in_db():
                                risultato = db.salva_ricetta(
                                    ricetta.get("titolo", "Ricetta senza titolo"), 
                                    ricetta.get("descrizione", "Generata da IA"), 
                                    ricetta.get("istruzioni", "Nessuna istruzione fornita."), 
                                    tempo_sicuro, 
                                    kcal_sicure
                                )
                                if risultato and "id" in risultato:
                                    ui.notify('Salvata nei preferiti!', type='positive')
                                    cont_valutazione.clear()
                                    with cont_valutazione:
                                        ui.label('Vota:').classes('text-sm font-bold text-gray-600')
                                        ui.rating(max=5).on_value_change(lambda ev: db.valuta_ricetta(risultato["id"], int(ev.value))).props('size=sm color=warning')
                            
                            with cont_valutazione:
                                ui.button('⭐ Preferiti', on_click=salva_in_db).props('flat color=warning dense')
                else:
                    ui.notify('Errore nella generazione.', type='negative')

        with ui.row().classes('fixed bottom-16 left-0 w-full justify-center p-4 bg-gradient-to-t from-transparent via-green-50 to-green-50 z-40'):
            ui.button('✨ Genera Ricetta', on_click=chiedi_all_ia).classes(BUTTON_AI_CLASSES).props('color=accent rounded-xl icon=auto_awesome')

# ==========================================
# PAGINA 2: NUCLEO FAMIGLIARE
# ==========================================
@ui.page('/famiglia')
def pagina_famiglia():
    applica_tema()
    with ui.column().classes(PAGE_CLASSES):
        ui.image('logo_100r.png').classes('w-full mb-3 drop-shadow-none')
        ui.label('Imposta i profili per calcolare le porzioni esatte.').classes(SUBTITLE_CLASSES)

        @ui.refreshable
        def renderizza_membri():
            membri = db.ottieni_membri()
            with ui.column().classes('w-full gap-3 mb-6'):
                if not membri: return ui.label("Nessun componente aggiunto.").classes("text-gray-400 italic text-center w-full")
                for m in membri:
                    with ui.card().classes('w-full bg-white shadow-sm border border-green-100 p-3'):
                        with ui.row().classes('w-full justify-between items-center'):
                            with ui.column().classes('gap-0'):
                                ui.label(m['nome']).classes('text-xl font-bold text-gray-800')
                                ui.label(f"Fabbisogno: {m['kcal_target']} Kcal/giorno").classes('text-sm text-accent font-medium')
                            ui.button(icon='delete', on_click=lambda id_m=m['id']: (db.elimina_membro(id_m), ui.notify('Rimosso', type='negative', position='top'), renderizza_membri.refresh())).props('flat color=negative dense round')
        renderizza_membri()

        ui.separator().classes('my-4 bg-green-200 w-full h-px')
        ui.label('➕ Aggiungi Persona').classes('text-xl font-extrabold text-green-900 mb-2')
        with ui.card().classes('w-full bg-white shadow-md p-4'):
            nome = ui.input('Nome').classes(INPUT_CLASSES).props(INPUT_PROPS)
            with ui.row().classes('w-full gap-2'):
                sesso = ui.select({'M': 'Uomo', 'F': 'Donna'}, value='M', label='Sesso').classes('col-grow').props(INPUT_PROPS)
                eta = ui.number('Età', format='%.0f').classes('w-20').props(INPUT_PROPS)
            with ui.row().classes('w-full gap-2 mt-2'):
                peso = ui.number('Peso (kg)', format='%.1f').classes('col-grow').props(INPUT_PROPS)
                altezza = ui.number('Altezza (cm)', format='%.0f').classes('col-grow').props(INPUT_PROPS)
            attivita = ui.select({1.2: 'Sedentario', 1.375: 'Leggero', 1.55: 'Moderato', 1.725: 'Agonistico'}, value=1.2, label='Livello di Attività').classes('w-full mt-2').props(INPUT_PROPS)
            
            def calcola_e_salva():
                if not nome.value or non_validi([eta.value, peso.value, altezza.value]): return ui.notify('Compila tutti i campi', type='warning', position='top')
                kcal = calcola_fabbisogno_giornaliero(sesso.value, peso.value, altezza.value, eta.value, attivita.value)
                if db.aggiungi_membro_famiglia(nome.value, sesso.value, int(eta.value), float(peso.value), float(altezza.value), float(attivita.value), kcal):
                    ui.notify(f'{nome.value} aggiunto!', type='positive', position='top')
                    renderizza_membri.refresh()
                    nome.value = '' 
            ui.button('Calcola e Salva', on_click=calcola_e_salva).classes('w-full text-white font-bold py-3 mt-4 shadow-md transition hover:scale-105').props('color=accent rounded-lg icon=save')

# ==========================================
# PAGINA 3: CALENDARIO SETTIMANALE E PORZIONAMENTO
# ==========================================
@ui.page('/calendario')
def pagina_calendario():
    applica_tema()
    stato = {'menu_bozza': {}}

    dialog_ricetta = ui.dialog()
    with dialog_ricetta, ui.card().classes('w-full max-w-sm p-4 rounded-xl'):
        dialog_titolo = ui.label('').classes('text-2xl font-bold text-gray-800')
        with ui.row().classes('w-full gap-4 mt-2 mb-4 text-accent font-bold'):
            dialog_tempo = ui.label('')
            dialog_kcal = ui.label('')
        ui.label('Preparazione:').classes('font-bold text-gray-700 text-lg')
        dialog_istruzioni = ui.label('').classes('text-gray-600 mt-2 whitespace-pre-wrap')
        ui.button('Chiudi', on_click=dialog_ricetta.close).classes('w-full mt-6').props('outline color=primary')

    def apri_dettaglio(pasto):
        dialog_titolo.set_text(pasto.get('titolo', ''))
        dialog_tempo.set_text(f"⏱️ {pasto.get('tempo_min', pasto.get('tempo_preparazione_min', 0))} min")
        dialog_kcal.set_text(f"🔥 {pasto.get('kcal_totali', 0)} Kcal")
        dialog_istruzioni.set_text(pasto.get('istruzioni', 'Nessuna istruzione. Aggiorna il prompt AI.'))
        dialog_ricetta.open()

        # Se le istruzioni mancano, forziamo una frase simpatica invece di un errore
        istruzioni = pasto.get('istruzioni')
        if not istruzioni or len(istruzioni) < 5:
            istruzioni = "Passaggi non generati. Clicca su Shuffle 🎲 per rigenerare questo pasto e avere le istruzioni complete!"
        dialog_istruzioni.set_text(istruzioni)

    with ui.column().classes(PAGE_CLASSES):
        ui.image('logo_100r.png').classes('w-full mx-auto mb-4 drop-shadow-md')
        #ui.label('📅 Piano Settimanale').classes(TITLE_CLASSES)
        
        @ui.refreshable
        def renderizza_gestione_calendario():
            menu_salvato = db.ottieni_menu_settimanale()
            
            def disegna_menu(dati_menu, modalita_bozza=False):
                membri = db.ottieni_membri()
                molt_pranzo = calcola_moltiplicatori_porzioni(membri, 'pranzo')
                molt_cena = calcola_moltiplicatori_porzioni(membri, 'cena')

                with ui.column().classes('w-full gap-2 pb-24'):
                    for giorno in ['lunedi', 'martedi', 'mercoledi', 'giovedi', 'venerdi', 'sabato', 'domenica']:
                        if giorno in dati_menu:
                            ui.label(giorno.upper()).classes('text-lg font-extrabold text-green-800 mt-4 border-b-2 border-green-300 w-full')
                            
                            for tipo in ['pranzo', 'cena']:
                                pasto = dati_menu[giorno][tipo]
                                moltiplicatori_attuali = molt_pranzo if tipo == 'pranzo' else molt_cena
                                
                                tempo_pasto = int(pasto.get('tempo_min', pasto.get('tempo_preparazione_min', 0)))
                                kcal_pasto = int(pasto.get('kcal_totali', 0))

                                with ui.card().classes('justify-between w-full bg-white border border-green-100 p-2 shadow-sm'):
                                    with ui.row().classes('w-full justify-between items-center flex-nowrap'):
                                      
                                        with ui.column().classes('col-grow gap-0 truncate'):
                                            ui.label(tipo.capitalize()).classes('font-bold text-gray-400 text-xs uppercase tracking-widest')
                                            ui.label(pasto.get('titolo', '')).classes('text-lg font-bold text-gray-800 leading-tight my-1 whitespace-normal')
                                            ui.label(f"⏱️ {tempo_pasto}m | 🔥 {kcal_pasto} Kcal").classes('text-xs text-accent font-bold')

                                    ui.separator().classes('my-2')
                                    with ui.row().classes('w-full gap-2 flex-wrap'):
                                        for m_nome, m_val in moltiplicatori_attuali.items():
                                            ui.label(f"{m_nome}: {m_val}x").classes('bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-md font-medium')

                                with ui.row().classes('justify-right-0 gap-1 bg-green-50 rounded-lg'):   
                                    ui.button(icon='menu_book', on_click=lambda p=pasto: apri_dettaglio(p)).props('flat color=secondary dense round').classes('justify-items-end')
                                    
                                    def salva_pref(e, p=pasto, t_calc=tempo_pasto, k_calc=kcal_pasto):
                                        if db.salva_ricetta(p.get('titolo','Ricetta'), "Dal calendario", p.get('istruzioni','Nessuna istruzione.'), t_calc, k_calc):
                                            ui.notify('Salvata nei preferiti! ⭐', type='positive')
                                            e.sender.props('icon=star color=warning')
                                    ui.button(icon='star_border', on_click=salva_pref).props('flat color=grey-5 dense round').classes('justify-items-end')
                                    
                                    async def esegui_shuffle(e, t=tipo, g=giorno, p=pasto):
                                        in_casa = db.ottieni_ingredienti_disponibili()
                                        e.sender.props('loading')
                                        import asyncio
                                        nuovo = await asyncio.get_running_loop().run_in_executor(None, chef.rimescola_pasto, in_casa, t, 60, p.get('titolo', ''))
                                        e.sender.props(remove='loading')
                                        if nuovo:
                                            if modalita_bozza:
                                                stato['menu_bozza'][g][t] = nuovo
                                            else:
                                                menu_salvato = db.ottieni_menu_settimanale()
                                                menu_salvato[g][t] = nuovo
                                                db.salva_menu_settimanale(menu_salvato)
                                            renderizza_gestione_calendario.refresh()
                                    ui.button(icon='shuffle', on_click=esegui_shuffle).props('flat color=primary dense round').classes('justify-items-end')


            if menu_salvato:
                ui.label('Menu in corso').classes('text-green-800 font-bold mb-2')
                disegna_menu(menu_salvato, modalita_bozza=False)
                # Nuovo bottone per aprire la stampa in una nuova scheda
                ui.button('🖨️ Stampa Menu (PDF)', on_click=lambda: ui.run_javascript("window.open('/stampa', '_blank')")).classes('w-full mt-6 text-white font-bold py-3 shadow-md').props('color=primary rounded-lg')
                ui.button('🗑️ Azzera Settimana', on_click=lambda: (db.elimina_menu_settimanale(), renderizza_gestione_calendario.refresh())).props('color=negative outline').classes('w-full mt-4')
            elif stato['menu_bozza']:
                ui.label('Modifica e Conferma').classes('text-orange-600 font-bold mb-2')
                disegna_menu(stato['menu_bozza'], modalita_bozza=True)
                def conferma_salvataggio():
                    if db.salva_menu_settimanale(stato['menu_bozza']):
                        ui.notify('Calendario salvato!', type='positive')
                        stato['menu_bozza'] = {} 
                        renderizza_gestione_calendario.refresh()
                with ui.row().classes('fixed bottom-16 left-0 w-full justify-center p-4 z-40 gap-2'):
                    ui.button('💾 Salva Definitivo', on_click=conferma_salvataggio).classes('col-grow text-white font-bold py-4 shadow-lg text-lg').props('color=positive rounded-xl')
                    ui.button(icon='delete', on_click=lambda: (stato.update({'menu_bozza': {}}), renderizza_gestione_calendario.refresh())).classes('py-4 shadow-lg').props('color=negative rounded-xl')
            else:
                with ui.row().classes('w-full gap-2 mb-4'):
                    tempo_pranzo = ui.select({15: '15 min', 30: '30 min', 60: '60 min'}, value=30, label='Max Pranzo').classes('col-grow').props(INPUT_PROPS)
                    tempo_cena = ui.select({30: '30 min', 60: '60 min', 90: '90 min', 120: '120 min'}, value=60, label='Max Cena').classes('col-grow').props(INPUT_PROPS)

                async def genera_tutto(e):
                    in_casa = db.ottieni_ingredienti_disponibili()
                    if not in_casa: return ui.notify("Segna qualche ingrediente come disponibile!", type="warning")
                    if not db.ottieni_membri(): return ui.notify("Aggiungi prima la famiglia!", type="warning")
                    e.sender.props('loading') 
                    import asyncio
                    menu_generato = await asyncio.get_running_loop().run_in_executor(None, chef.genera_settimana, in_casa, tempo_pranzo.value, tempo_cena.value)
                    e.sender.props(remove='loading')
                    if menu_generato:
                        stato['menu_bozza'] = menu_generato
                        renderizza_gestione_calendario.refresh()
                with ui.row().classes('fixed bottom-16 left-0 w-full justify-center p-4 bg-gradient-to-t from-transparent via-green-50 to-green-50 z-40'):
                    ui.button('✨ Genera Settimana', on_click=genera_tutto).classes(BUTTON_AI_CLASSES).props('color=accent rounded-xl icon=auto_awesome')

        renderizza_gestione_calendario()


# ==========================================
# PAGINA PREFERITI (RICETTARIO)
# ==========================================
@ui.page('/preferiti')
def pagina_preferiti():
    applica_tema()
    
    with ui.column().classes(PAGE_CLASSES):
        ui.image('logo_100r.png').classes('w-full mx-auto mb-4 drop-shadow-md')
        ui.label('Le vostre ricette preferite.').classes(SUBTITLE_CLASSES)
        
        @ui.refreshable
        def renderizza_preferiti():
            preferiti = db.ottieni_tutte_le_ricette()
            
            if not preferiti:
                ui.label("Nessuna ricetta salvata.").classes("text-gray-400 italic mt-10 w-full text-center")
                return

            for r in preferiti:
                with ui.card().classes('w-full bg-white mb-4 p-4 shadow-sm'):
                    # Riga superiore con Titolo e Cestino
                    with ui.row().classes('w-full items-start justify-between flex-nowrap mb-1'):
                        with ui.column().classes('col-grow gap-0'):
                            ui.label(r.get('titolo', '')).classes('text-xl font-bold leading-tight')
                            ui.label(f"⏱️ {r.get('tempo_preparazione_min', 0)} min | 🔥 {r.get('kcal_totali', 0)} Kcal").classes('text-accent text-xs font-bold')
                        
                    # Bottone Elimina
                    def elimina_pref(id_ric=r['id'], nome_ric=r.get('titolo', '')):
                        db.elimina_ricetta(id_ric)
                        ui.notify(f'{nome_ric} rimossa dai preferiti', type='negative')
                        renderizza_preferiti.refresh()
                        
                    ui.button(icon='delete', on_click=elimina_pref).props('flat color=negative dense round').classes('flex-shrink-0')
                        
                    # Istruzioni
                    ui.label(r.get('istruzioni', '')).classes('text-gray-600 text-sm mt-2 whitespace-pre-wrap')
                        
                    # Valutazione in fondo
                    with ui.row().classes('w-full items-center justify-between mt-4 border-t border-gray-100 pt-2'):
                        ui.label('Valutazione:').classes('text-xs font-bold text-gray-500')
                        ui.rating(max=5, value=r.get('valutazione', 0)).on_value_change(lambda ev, id=r['id']: db.valuta_ricetta(id, int(ev.value))).props('size=sm color=warning')

        renderizza_preferiti()


# ==========================================
# PAGINA 5: LISTA DELLA SPESA
# ==========================================
@ui.page('/spesa')
def pagina_spesa():
    applica_tema()
    
    with ui.column().classes(PAGE_CLASSES):
        ui.image('logo_100r.png').classes('w-full mx-auto mb-4 drop-shadow-md')
        ui.label('Alimenti esauriti da ricomprare.').classes(SUBTITLE_CLASSES)
        
        @ui.refreshable
        def renderizza_spesa():
            da_comprare = db.ottieni_ingredienti_esauriti()
            
            if not da_comprare:
                ui.label("Tutto pieno! Non ti manca nulla in dispensa.").classes("text-gray-400 italic mt-10 w-full text-center")
                return
            
            with ui.column().classes('w-full gap-2'):
                for ing in da_comprare:
                    with ui.card().classes('w-full bg-white shadow-sm border border-green-100 p-2'):
                        with ui.row().classes('w-full items-center justify-between flex-nowrap'):
                            with ui.column().classes('col-grow gap-0 truncate'):
                                ui.label(ing['nome'].capitalize()).classes('text-lg font-bold text-gray-800')
                                ui.label(ing['categoria'].replace('_', ' ').capitalize()).classes('text-xs text-gray-400 uppercase font-medium')
                            
                            with ui.row().classes('gap-1 flex-shrink-0 items-center bg-gray-50 rounded-lg p-1'):
                                
                                # Tasto di spunta verde: Hai comprato l'alimento
                                def segna_comprato(id_ing=ing['id'], nome_ing=ing['nome']):
                                    db.toggle_disponibilita_ingrediente(id_ing, True)
                                    ui.notify(f'{nome_ing.capitalize()} rimesso in dispensa!', type='positive')
                                    renderizza_spesa.refresh()
                                
                                ui.button(icon='check_circle', on_click=segna_comprato).props('flat color=positive dense round')
                                
                                # Tasto cestino: Elimina definitivamente dal database
                                def elimina_definitivo(id_ing=ing['id'], nome_ing=ing['nome']):
                                    db.elimina_ingrediente(id_ing)
                                    ui.notify(f'{nome_ing.capitalize()} eliminato per sempre.', type='negative')
                                    renderizza_spesa.refresh()
                                    
                                ui.button(icon='delete', on_click=elimina_definitivo).props('flat color=negative dense round')
        
        renderizza_spesa()

# ==========================================
# PAGINA NASCOSTA: STAMPA MENU A4
# ==========================================
@ui.page('/stampa')
def pagina_stampa():
    # Sfondo bianco puro, testo nero, niente barra di navigazione
    ui.query('body').classes('bg-white text-black p-6 font-sans max-w-4xl mx-auto')
    
    menu_salvato = db.ottieni_menu_settimanale()
    membri = db.ottieni_membri()
    
    if not menu_salvato:
        ui.label('Nessun menu salvato da stampare.').classes('text-xl font-bold')
        return

    molt_pranzo = calcola_moltiplicatori_porzioni(membri, 'pranzo')
    molt_cena = calcola_moltiplicatori_porzioni(membri, 'cena')

    # Intestazione del foglio
    ui.label('🍽️ Menu della Settimana').classes('text-4xl font-extrabold mb-8 text-center w-full border-b-4 border-black pb-4')

    with ui.column().classes('w-full gap-6'):
        for giorno in ['lunedi', 'martedi', 'mercoledi', 'giovedi', 'venerdi', 'sabato', 'domenica']:
            if giorno in menu_salvato:
                with ui.row().classes('w-full border-b border-gray-300 pb-4 items-start flex-nowrap'):
                    # Colonna Giorno
                    ui.label(giorno.upper()).classes('w-1/4 text-xl font-black text-gray-800 uppercase tracking-widest pt-1')
                    
                    # Colonne Pranzo e Cena affiancate
                    with ui.row().classes('w-3/4 gap-4 flex-nowrap'):
                        # Blocco Pranzo
                        pasto_p = menu_salvato[giorno].get('pranzo', {})
                        str_porzioni_p = " | ".join([f"{k}: {v}x" for k, v in molt_pranzo.items()])
                        with ui.column().classes('w-1/2 gap-0 pr-4 border-r border-gray-200'):
                            ui.label('PRANZO').classes('text-xs text-gray-500 font-bold uppercase')
                            ui.label(pasto_p.get('titolo', '')).classes('text-lg font-bold leading-tight my-1')
                            ui.label(f"⏱️ {pasto_p.get('tempo_min', pasto_p.get('tempo_preparazione_min', 0))}m | 🔥 {pasto_p.get('kcal_totali', 0)} Kcal").classes('text-xs text-gray-600')
                            ui.label(str_porzioni_p).classes('text-xs text-gray-500 italic mt-1')

                        # Blocco Cena
                        pasto_c = menu_salvato[giorno].get('cena', {})
                        str_porzioni_c = " | ".join([f"{k}: {v}x" for k, v in molt_cena.items()])
                        with ui.column().classes('w-1/2 gap-0'):
                            ui.label('CENA').classes('text-xs text-gray-500 font-bold uppercase')
                            ui.label(pasto_c.get('titolo', '')).classes('text-lg font-bold leading-tight my-1')
                            ui.label(f"⏱️ {pasto_c.get('tempo_min', pasto_c.get('tempo_preparazione_min', 0))}m | 🔥 {pasto_c.get('kcal_totali', 0)} Kcal").classes('text-xs text-gray-600')
                            ui.label(str_porzioni_c).classes('text-xs text-gray-500 italic mt-1')

    # Fa scattare in automatico la finestra di stampa del browser dopo mezzo secondo
    ui.timer(0.5, lambda: ui.run_javascript('window.print()'), once=True)


ui.run(title="CentoRicette", port=8080, favicon="restaurant-16.ico", viewport='width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no')