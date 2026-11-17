# MarkItDown TUI

Interfaccia a riga di comando (TUI) moderna per **Microsoft MarkItDown**, sviluppata in Python con [Textual](https://textual.textualize.io/).  
È la versione per terminale del progetto **markItDownUI** (CustomTkinter): offre le stesse funzionalità, pensata per girare in qualsiasi terminale (Linux, macOS, Windows) senza necessità di un server grafico desktop.

---

## Caratteristiche

* **Conversione Singola**:
  * Conversione di qualsiasi documento supportato in Markdown (`.md`)
  * Selezione del file di input e percorso di destinazione personalizzabile (opzionale)
  * Anteprima in tempo reale delle informazioni sul file (formato, dimensione)
  * Conversione asincrona in background (la TUI non si blocca mai)
  * Barra di avanzamento e log di operazione dedicati

* **Conversione Batch**:
  * Coda di file con percorsi multipli, cartelle intere o pattern glob (es. `~/docs/*.pdf`, `relazioni/*.docx`)
  * Controllo automatico dei formati supportati e prevenzione duplicati
  * Cartella di output personalizzabile (oppure salvataggio nella cartella di origine di ciascun file)
  * Elenco scorrevole con stato in tempo reale per ciascun file (`in coda`, `in corso`, `OK`, `errore`)
  * Barra di progresso con conteggio file convertiti
  * Possibilità di annullare la conversione batch in corso in modo cooperativo

* **Console di Log Integrata**:
  * Log cronologico con timestamp e colorazione per severità (Info, Success, Warning, Error)
  * Scorciatoia e pulsante dedicato per la pulizia della console

* **Design e Usabilità**:
  * Tema scuro coerente ispirato alla palette Obsidian
  * Layout a schede (`TabbedContent`) rapido e reattivo
  * Scorciatoie da tastiera intuitive mostrate nel footer

---

## Formati Supportati

Supporta tutti i formati gestiti da Microsoft MarkItDown:
* **Documenti Word** (`.docx`)
* **Presentazioni PowerPoint** (`.pptx`)
* **Fogli di calcolo Excel** (`.xlsx`)
* **Documenti PDF** (`.pdf`)
* **Pagine Web** (`.html`, `.htm`)
* **Testo semplice e formati strutturati** (`.txt`, `.csv`, `.xml`, `.json`)

---

## Requisiti e Installazione

Richiede **Python 3.8+**.

### 1. Clonazione del repository
```bash
git clone https://github.com/jako200/markItDownTUI.git
cd markItDownTUI
```

### 2. Creazione dell'ambiente virtuale (consigliato)

Su Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Su Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Esecuzione

```bash
python main.py
```

Oppure tramite gli script forniti:
* **Linux / macOS**: `./run.sh`
* **Windows**: `run.bat`

### Scorciatoie da tastiera
* `Ctrl + Q`: Esce dall'applicazione
* `Ctrl + T`: Passa rapidamente tra la scheda **Singolo** e la scheda **Batch**
* `Ctrl + L`: Pulisce la console dei log

---

## Architettura del Progetto

```
markItDownTUI/
├── main.py                 # Punto di ingresso dell'applicazione
├── requirements.txt        # Dipendenze Python (textual, markitdown[all])
├── run.sh                  # Launcher per Linux/macOS
├── run.bat                 # Launcher per Windows
├── src/
│   ├── core/               # Motore di conversione e utilità (indipendente dalla UI)
│   │   ├── converter.py    # Wrapper Microsoft MarkItDown e BatchConversionWorker
│   │   └── helpers.py      # Gestione formati, estensioni e formattazione dimensioni
│   └── tui/                # Interfaccia grafica da terminale (Textual)
│       ├── app.py          # Applicazione TUI, layout, schede, gestione eventi
│       └── styles.py       # Palette colori scura Obsidian
└── tests/                  # Suite completa di unit test
    ├── test_core.py        # Test del motore di conversione e helpers
    └── test_tui.py         # Test asincroni dell'interfaccia utente Textual
```

---

## Test

Per eseguire l'intera suite di test (18 test automatizzati per core e interfaccia TUI):

```bash
python -m unittest discover tests
```
