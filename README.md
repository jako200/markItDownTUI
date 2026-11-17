# MarkItDown TUI

Interfaccia a riga di comando (TUI) per **Microsoft MarkItDown**, scritta in
Python con [Textual](https://textual.textualize.io/). E' la versione
terminal del progetto **markItDownUI** (GUI CustomTkinter): stesse
funzionalita', pensata per girare in qualsiasi terminale Linux senza
desktop grafico.

## Funzionalita'

* Conversione di un singolo file in Markdown
* Conversione in batch: coda di file (percorsi singoli o pattern glob come
  `~/docs/*.pdf`), barra di progresso, stato per file, console di log
  colorata
* Formati supportati: `.docx`, `.pptx`, `.xlsx`, `.pdf`, `.html`/`.htm`,
  `.txt`, `.csv`, `.xml`, `.json`
* Tema scuro ispirato ad Obsidian

## Architettura

* `src/core/` - motore di conversione (riuso diretto da *markItDownUI*,
  indipendente dalla piattaforma: solo `os`, `threading` e l'API
  MarkItDown)
* `src/tui/` - interfaccia TUI (Textual)
* `tests/` - test del motore di conversione

## Installazione (Linux)

```bash
git clone <url-del-repository>
cd markItDownTUI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Esecuzione

```bash
python main.py
```

Comandi utili in app: `Ctrl+Q` per uscire, `Tab` per passare da una scheda
all'altra.

## Test

```bash
python tests/test_core.py
```
