"""
MarkItDown TUI
===============

Interfaccia a riga di comando (TUI) per **Microsoft MarkItDown**, scritta con
**Textual**. Offre le stesse funzionalita' del progetto GUI *markItDownUI*
(CustomTkinter), ma gira in qualsiasi terminale Linux senza desktop grafico.

Funzionalita'
-------------
* Conversione di un singolo file in Markdown
* Conversione in batch: coda di file (percorsi o pattern glob), barra di
  progresso, stato per file, console di log colorata
* Formati supportati: .docx, .pptx, .xlsx, .pdf, .html/.htm, .txt, .csv,
  .xml, .json
* Tema scuro ispirato ad Obsidian

Esecuzione
----------
    pip install -r requirements.txt
    python main.py
"""
from __future__ import annotations

import glob
import os
import time
from typing import List, Tuple

from rich.markup import escape
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Log,
    ProgressBar,
    Static,
    Tab,
    Tabs,
)

from src.core.converter import BatchConversionWorker, MarkdownConverter
from src.core.helpers import format_size
from src.tui.styles import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_ACCENT_MUTED,
    BG_CARD,
    BG_CONSOLE,
    BG_INPUT,
    BG_MAIN,
    BORDER,
    TEXT_MUTED,
    TEXT_PRIMARY,
)


class BatchFileList(Widget):
    """Elenco scorrevole dei file in coda per la conversione in batch."""

    CSS = f"""
    BatchFileList {{
        background: {BG_CONSOLE};
        border: solid {BORDER};
        border-radius: 8;
        height: 1fr;
        padding: 0 1;
    }}
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.files: List[Tuple[str, str, str]] = []  # (path, status, color)

    def render(self) -> Text:
        if not self.files:
            return Text.from_markup(
                "[dim]Coda vuota - aggiungi un file o un pattern glob.[/]"
            )
        lines = []
        for path, status, color in self.files:
            size = format_size(os.path.getsize(path)) if os.path.exists(path) else "?"
            name = escape(os.path.basename(path))
            lines.append(f"[bold]{name}[/]  [dim]{size}[/]  [{color}]{status}[/]")
        return Text.from_markup("\n".join(lines))

    def add_file(self, path: str) -> bool:
        path = os.path.abspath(path)
        if any(existing == path for existing, _, _ in self.files):
            return False
        self.files.append((path, "in coda", "yellow"))
        self.refresh()
        return True

    def set_status(self, path: str, status: str, color: str) -> None:
        updated = []
        for p, s, c in self.files:
            updated.append((p, status, color) if p == path else (p, s, c))
        self.files = updated
        self.refresh()

    def reset_statuses(self) -> None:
        self.files = [(p, "in coda", "yellow") for p, _, _ in self.files]
        self.refresh()

    def clear(self) -> None:
        self.files = []
        self.refresh()

    def get_paths(self) -> List[str]:
        return [p for p, _, _ in self.files]


class MarkItDownTUI(App):
    """App TUI principale."""

    TITLE = "MarkItDown TUI"
    SUB_TITLE = "Convertitore in Markdown per il terminale"

    CSS = f"""
    Screen {{
        background: {BG_MAIN};
        color: {TEXT_PRIMARY};
    }}
    Header {{
        background: {BG_CARD};
        color: {TEXT_PRIMARY};
    }}
    Footer {{
        background: {BG_CARD};
        color: {TEXT_MUTED};
    }}
    Tabs {{
        height: 1fr;
    }}
    Tab {{
        color: {TEXT_MUTED};
    }}
    Tab.-active {{
        color: {TEXT_PRIMARY};
        text-style: bold;
    }}
    Log {{
        height: 20;
        background: {BG_CONSOLE};
        border: solid {BORDER};
    }}
    Input {{
        background: {BG_INPUT};
        border: solid {BORDER};
        color: {TEXT_PRIMARY};
    }}
    Button.primary {{
        background: {COLOR_ACCENT};
        color: white;
        text-style: bold;
    }}
    Button.primary:hover {{
        background: {COLOR_ACCENT_HOVER};
    }}
    Button.primary:disabled {{
        background: {COLOR_ACCENT_MUTED};
        color: {TEXT_MUTED};
    }}
    Button.default {{
        background: {BG_CARD};
        border: solid {BORDER};
        color: {TEXT_PRIMARY};
    }}
    Button.default:hover {{
        background: {COLOR_ACCENT_MUTED};
    }}
    ProgressBar {{
        border: solid {COLOR_ACCENT_MUTED};
    }}
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.converter: MarkdownConverter | None = None
        self.has_engine = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Tabs():
            with Tab("Single"):
                yield Vertical(
                    Input(
                        id="single-path",
                        placeholder="Percorso del file da convertire (.docx .pptx .xlsx .pdf .html .txt)",
                    ),
                    Static(id="single-status", markup="[dim]Nessun file selezionato.[/]"),
                    ProgressBar(id="single-progress"),
                    Button("Converti in Markdown", id="single-convert", variant="primary"),
                )
            with Tab("Batch"):
                yield Vertical(
                    Horizontal(
                        Input(
                            id="batch-path",
                            placeholder="Percorso o pattern glob (es. ~/docs/*.pdf)",
                        ),
                        Button("Aggiungi", id="batch-add", variant="primary"),
                        Button("Svuota", id="batch-clear", variant="default"),
                    ),
                    BatchFileList(id="batch-list"),
                    Static(id="batch-status", markup="[dim]Coda: 0 file.[/]"),
                    ProgressBar(id="batch-progress"),
                    Button("Converti tutti", id="batch-convert", variant="primary"),
                )
        yield Log(id="console")
        yield Footer()

    def on_mount(self) -> None:
        try:
            self.converter = MarkdownConverter()
            self.has_engine = self.converter.is_available()
        except Exception:  # pragma: no cover
            self.converter = None
            self.has_engine = False
        if self.has_engine:
            self._log("Info", "Motore Microsoft MarkItDown caricato correttamente.")
        else:
            self._log(
                "Error",
                "Motore MarkItDown non disponibile: pip install -r requirements.txt",
            )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def _log(self, level: str, message: str) -> None:
        color = {
            "Info": "dim",
            "Success": "green",
            "Error": "red",
            "Warning": "yellow",
        }[level]
        stamp = time.strftime("%H:%M:%S")
        self.query_one("#console", Log).write(
            f"[{color}] {stamp} - {escape(message)} [/]"
        )

    def _status(self, wid: str, markup: str) -> None:
        self.query_one(wid, Static).update(markup)

    def _set_progress(self, wid: str, value: float) -> None:
        self.query_one(wid, ProgressBar).progress = value

    def _update_batch_count(self) -> None:
        n = len(self.query_one("#batch-list", BatchFileList).get_paths())
        self._status("#batch-status", f"[dim]Coda: {n} file.[/]")

    def _set_batch_buttons(self, enabled: bool) -> None:
        for btn_id in ("#batch-add", "#batch-clear", "#batch-convert"):
            self.query_one(btn_id, Button).disabled = not enabled

    # ------------------------------------------------------------------
    # Single conversion
    # ------------------------------------------------------------------
    @on(Button.Pressed, "#single-convert")
    def _on_single_convert(self) -> None:
        path = self.query_one("#single-path", Input).value.strip()
        if not path:
            self._status("#single-status", "[red]Inserisci un percorso.[/]")
            return
        if not os.path.isfile(path):
            self._status(
                "#single-status", f"[red]File non trovato: {escape(path)}[/]"
            )
            return
        if not self.has_engine:
            self._status("#single-status", "[red]Motore MarkItDown non disponibile.[/]")
            return
        output = os.path.splitext(path)[0] + ".md"
        try:
            out = self.converter.convert(path, output)
            self._status("#single-status", f"[green]Salvato: {escape(out)}[/]")
            self._log("Success", f"OK {os.path.basename(out)}")
        except Exception as exc:
            self._status("#single-status", f"[red]Errore: {escape(str(exc))}[/]")
            self._log("Error", str(exc))
        self._set_progress("#single-progress", 0.0)

    # ------------------------------------------------------------------
    # Batch conversion
    # ------------------------------------------------------------------
    @on(Button.Pressed, "#batch-add")
    def _on_batch_add(self) -> None:
        pattern = self.query_one("#batch-path", Input).value.strip()
        if not pattern:
            self._log("Warning", "Nessun percorso o pattern inserito.")
            return
        expanded = sorted(glob.glob(os.path.expanduser(pattern)))
        files = [p for p in expanded if os.path.isfile(p)]
        if not files:
            self._log("Error", f"Nessun file corrisponde a: {pattern}")
            return
        queue = self.query_one("#batch-list", BatchFileList)
        added = 0
        for p in files:
            if queue.add_file(p):
                added += 1
        self._log("Info", f"Aggiunti {added} file alla coda.")
        self._update_batch_count()
        self.query_one("#batch-path", Input).value = ""

    @on(Button.Pressed, "#batch-clear")
    def _on_batch_clear(self) -> None:
        self.query_one("#batch-list", BatchFileList).clear()
        self._update_batch_count()

    @on(Button.Pressed, "#batch-convert")
    def _on_batch_convert(self) -> None:
        queue = self.query_one("#batch-list", BatchFileList)
        paths = queue.get_paths()
        if not paths:
            self._status("#batch-status", "[red]Coda vuota: aggiungi prima dei file.[/]")
            return
        if not self.has_engine:
            self._status("#batch-status", "[red]Motore MarkItDown non disponibile.[/]")
            return

        self._set_batch_buttons(False)
        queue.reset_statuses()
        self._status("#batch-status", f"[yellow]Converto {len(paths)} file...[/]")
        self._set_progress("#batch-progress", 0.0)

        def ui(func, *args):
            self.call_from_thread(func, *args)

        def on_file_start(path):
            ui(queue.set_status, path, "in corso", "cyan")

        def on_file_success(path, out_path):
            ui(queue.set_status, path, "OK", "green")
            ui(self._log, "Success", f"OK {os.path.basename(out_path)}")

        def on_file_error(path, msg):
            ui(queue.set_status, path, "errore", "red")
            ui(self._log, "Error", f"ERRORE {os.path.basename(path)}: {msg}")

        def on_progress(done, total):
            ui(self._set_progress, "#batch-progress", done / total if total else 0.0)

        def on_complete(success, failed, cancelled):
            ui(self._set_batch_buttons, True)
            ui(
                self._status,
                "#batch-status",
                f"[dim]Completato: {success} ok, {failed} errori"
                + (", annullato." if cancelled else "."),
            )
            ui(self._log, "Info", f"Batch completato: {success} ok, {failed} errori.")
            ui(self._set_progress, "#batch-progress", 0.0)

        worker = BatchConversionWorker(
            self.converter,
            paths,
            callbacks={
                "on_file_start": on_file_start,
                "on_file_success": on_file_success,
                "on_file_error": on_file_error,
                "on_progress": on_progress,
                "on_complete": on_complete,
            },
        )
        worker.start()
