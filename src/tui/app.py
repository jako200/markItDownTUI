"""
MarkItDown TUI
==============

Interfaccia a riga di comando (TUI) per Microsoft MarkItDown, realizzata con
Textual. Porting per terminale del progetto GUI markItDownUI (CustomTkinter),
ottimizzato per funzionare fluidamente su Linux, macOS e Windows senza desktop grafico.
"""
from __future__ import annotations

import glob
import os
import threading
import time
from typing import List, Optional, Tuple

from rich.markup import escape
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Log,
    ProgressBar,
    Static,
    TabbedContent,
    TabPane,
)

from src.core.converter import BatchConversionWorker, MarkdownConverter
from src.core.helpers import (
    SUPPORTED_EXTENSIONS,
    format_size,
    get_file_extension,
    get_file_type_description,
    is_supported_file,
)
from src.tui.styles import (
    BG_CARD,
    BG_CONSOLE,
    BG_INPUT,
    BG_MAIN,
    BORDER,
    BORDER_CARD,
    BORDER_CONSOLE,
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_ACCENT_MUTED,
    COLOR_ERROR,
    COLOR_ERROR_HOVER,
    COLOR_SUCCESS,
    COLOR_WARNING,
    TEXT_MUTED,
    TEXT_PRIMARY,
)


class BatchFileList(VerticalScroll):
    """Elenco scorrevole dei file in coda per la conversione in batch."""

    DEFAULT_CSS = f"""
    BatchFileList {{
        background: {BG_CONSOLE};
        border: solid {BORDER};
        height: 1fr;
        min-height: 5;
        padding: 0 1;
    }}
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.files: List[Tuple[str, str, str]] = []  # (path, status, color)

    def compose(self) -> ComposeResult:
        yield Static(id="batch-list-content")

    def on_mount(self) -> None:
        self._refresh_content()

    def _render_text(self) -> Text:
        if not self.files:
            return Text.from_markup(
                "[dim]Coda vuota - inserisci un file, cartella o pattern glob (es. *.pdf).[/]"
            )
        lines = []
        for path, status, color in self.files:
            size = format_size(os.path.getsize(path)) if os.path.exists(path) else "?"
            ext_desc = get_file_type_description(path)
            name = escape(os.path.basename(path))
            lines.append(
                f"[bold]{name}[/]  [dim]({ext_desc}, {size})[/]  [{color}][{status}][/]"
            )
        return Text.from_markup("\n".join(lines))

    def _refresh_content(self) -> None:
        try:
            content = self.query_one("#batch-list-content", Static)
            content.update(self._render_text())
        except Exception:
            pass

    def add_file(self, path: str) -> bool:
        path = os.path.abspath(path)
        if any(existing == path for existing, _, _ in self.files):
            return False
        self.files.append((path, "in coda", "yellow"))
        self._refresh_content()
        return True

    def set_status(self, path: str, status: str, color: str) -> None:
        updated = []
        for p, s, c in self.files:
            updated.append((p, status, color) if p == path else (p, s, c))
        self.files = updated
        self._refresh_content()

    def reset_statuses(self) -> None:
        self.files = [(p, "in coda", "yellow") for p, _, _ in self.files]
        self._refresh_content()

    def clear(self) -> None:
        self.files = []
        self._refresh_content()

    def get_paths(self) -> List[str]:
        return [p for p, _, _ in self.files]


class MarkItDownTUI(App):
    """App TUI principale."""

    TITLE = "MarkItDown TUI"
    SUB_TITLE = "Convertitore universale in Markdown per il terminale"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Esci", show=True, priority=True),
        Binding("ctrl+t", "toggle_tab", "Cambia Scheda", show=True),
        Binding("ctrl+l", "clear_log", "Pulisci Log", show=True),
    ]

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
    TabbedContent {{
        height: 1fr;
    }}
    TabPane {{
        padding: 1;
        height: 1fr;
    }}
    .field-label {{
        color: {TEXT_PRIMARY};
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
    }}
    .status-line {{
        margin: 1 0;
    }}
    .button-row {{
        height: auto;
        margin-top: 1;
        margin-bottom: 1;
    }}
    .button-row Button {{
        margin-right: 1;
    }}
    .input-row {{
        height: auto;
        margin-bottom: 1;
    }}
    .input-row Input {{
        width: 1fr;
        margin-right: 1;
    }}
    .input-row Button {{
        margin-right: 1;
    }}
    .log-box {{
        height: 8;
        min-height: 5;
        max-height: 12;
        background: {BG_CONSOLE};
        border: solid {BORDER_CONSOLE};
        padding: 0 1;
    }}
    .log-header {{
        height: auto;
        padding: 0 1;
        margin-top: 1;
    }}
    .log-title {{
        color: {TEXT_MUTED};
        text-style: bold;
        width: 1fr;
    }}
    Input {{
        background: {BG_INPUT};
        border: solid {BORDER};
        color: {TEXT_PRIMARY};
        margin-bottom: 1;
    }}
    Input:focus {{
        border: solid {COLOR_ACCENT};
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
    Button.error {{
        background: {COLOR_ERROR};
        color: white;
        text-style: bold;
    }}
    Button.error:hover {{
        background: {COLOR_ERROR_HOVER};
    }}
    ProgressBar {{
        margin: 1 0;
        border: solid {COLOR_ACCENT_MUTED};
    }}
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.converter: Optional[MarkdownConverter] = None
        self.has_engine = False
        self.current_batch_worker: Optional[BatchConversionWorker] = None
        self.is_single_converting = False

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="single-tab"):
            with TabPane("Singolo", id="single-tab"):
                yield Vertical(
                    Static("File di input:", classes="field-label"),
                    Input(
                        id="single-path",
                        placeholder="Percorso file (.docx, .pptx, .xlsx, .pdf, .html, .txt, .csv...)",
                    ),
                    Static("Destinazione Markdown (opzionale):", classes="field-label"),
                    Input(
                        id="single-output-path",
                        placeholder="Lascia vuoto per salvare nella stessa cartella (.md)",
                    ),
                    Static(
                        "[dim]Nessun file selezionato.[/]",
                        id="single-status",
                        classes="status-line",
                    ),
                    ProgressBar(id="single-progress", show_percentage=True),
                    Horizontal(
                        Button("Converti in Markdown", id="single-convert", variant="primary"),
                        classes="button-row",
                    ),
                )
            with TabPane("Batch", id="batch-tab"):
                yield Vertical(
                    Static("Aggiungi file, cartella o pattern glob:", classes="field-label"),
                    Horizontal(
                        Input(
                            id="batch-path",
                            placeholder="Percorso o pattern (es. *.pdf, docs/*.docx)",
                        ),
                        Button("Aggiungi", id="batch-add", variant="primary"),
                        Button("Svuota", id="batch-clear", variant="default"),
                        classes="input-row",
                    ),
                    Static("Cartella di destinazione (opzionale):", classes="field-label"),
                    Input(
                        id="batch-output-dir",
                        placeholder="Lascia vuoto per salvare nella cartella di origine di ciascun file",
                    ),
                    Static("Coda di conversione:", classes="field-label"),
                    BatchFileList(id="batch-list"),
                    Static(
                        "[dim]Coda: 0 file.[/]",
                        id="batch-status",
                        classes="status-line",
                    ),
                    ProgressBar(id="batch-progress", show_percentage=True),
                    Horizontal(
                        Button("Converti tutti", id="batch-convert", variant="primary"),
                        Button("Annulla", id="batch-cancel", variant="error", disabled=True),
                        classes="button-row",
                    ),
                )
        yield Horizontal(
            Static("Log Operazioni", classes="log-title"),
            Button("Pulisci log", id="log-clear", variant="default"),
            classes="log-header",
        )
        yield Log(id="console", classes="log-box")
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
                "Motore MarkItDown non disponibile: installare con 'pip install markitdown[all]'",
            )

    # ------------------------------------------------------------------
    # Actions & Utility
    # ------------------------------------------------------------------
    def action_toggle_tab(self) -> None:
        tabbed = self.query_one(TabbedContent)
        tabbed.active = "batch-tab" if tabbed.active == "single-tab" else "single-tab"

    def action_clear_log(self) -> None:
        self.query_one("#console", Log).clear()

    @on(Button.Pressed, "#log-clear")
    def _on_log_clear(self) -> None:
        self.action_clear_log()

    def _log(self, level: str, message: str) -> None:
        color = {
            "Info": "dim",
            "Success": "green",
            "Error": "red",
            "Warning": "yellow",
        }.get(level, "dim")
        stamp = time.strftime("%H:%M:%S")
        try:
            self.query_one("#console", Log).write(
                f"[{color}] {stamp} - {escape(message)} [/]"
            )
        except Exception:
            pass

    def _status(self, wid: str, markup: str) -> None:
        try:
            self.query_one(wid, Static).update(markup)
        except Exception:
            pass

    def _set_progress(self, wid: str, done: float, total: Optional[float] = 100.0) -> None:
        try:
            self.query_one(wid, ProgressBar).update(total=total, progress=done)
        except Exception:
            pass

    def _update_batch_count(self) -> None:
        n = len(self.query_one("#batch-list", BatchFileList).get_paths())
        self._status("#batch-status", f"[dim]Coda: {n} file.[/]")

    def _set_batch_buttons(self, converting: bool) -> None:
        try:
            self.query_one("#batch-add", Button).disabled = converting
            self.query_one("#batch-clear", Button).disabled = converting
            self.query_one("#batch-convert", Button).disabled = converting
            self.query_one("#batch-cancel", Button).disabled = not converting
        except Exception:
            pass

    def _set_single_button(self, converting: bool) -> None:
        try:
            btn = self.query_one("#single-convert", Button)
            btn.disabled = converting
            btn.label = "Conversione in corso..." if converting else "Converti in Markdown"
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Single conversion
    # ------------------------------------------------------------------
    @on(Input.Changed, "#single-path")
    def _on_single_path_changed(self) -> None:
        raw = self.query_one("#single-path", Input).value.strip().strip('"').strip("'")
        if not raw:
            self._status("#single-status", "[dim]Nessun file selezionato.[/]")
            return

        path = os.path.abspath(os.path.expanduser(raw))
        if os.path.isfile(path):
            size_str = format_size(os.path.getsize(path))
            desc = get_file_type_description(path)
            self._status(
                "#single-status",
                f"[dim]File pronto: {escape(os.path.basename(path))} ({desc}, {size_str})[/]",
            )
            out_input = self.query_one("#single-output-path", Input)
            if not out_input.value.strip():
                base, _ = os.path.splitext(path)
                out_input.placeholder = f"Default: {os.path.basename(base)}.md"
        else:
            self._status("#single-status", f"[yellow]File non ancora esistente: {escape(raw)}[/]")

    @on(Button.Pressed, "#single-convert")
    @on(Input.Submitted, "#single-path")
    def _on_single_convert(self) -> None:
        if self.is_single_converting:
            return

        raw_path = self.query_one("#single-path", Input).value.strip().strip('"').strip("'")
        if not raw_path:
            self._status("#single-status", "[red]Inserisci un percorso di file valido.[/]")
            return

        path = os.path.abspath(os.path.expanduser(raw_path))
        if not os.path.isfile(path):
            self._status("#single-status", f"[red]File non trovato: {escape(raw_path)}[/]")
            self._log("Error", f"File non trovato: {path}")
            return

        if not self.has_engine or not self.converter:
            self._status(
                "#single-status",
                "[red]Motore MarkItDown non disponibile. Installa con: pip install markitdown[all][/]",
            )
            self._log("Error", "Conversione fallita: libreria MarkItDown non caricata.")
            return

        custom_out = self.query_one("#single-output-path", Input).value.strip().strip('"').strip("'")
        if custom_out:
            out_path = os.path.abspath(os.path.expanduser(custom_out))
            if os.path.isdir(out_path):
                base_name = os.path.splitext(os.path.basename(path))[0]
                out_path = os.path.join(out_path, f"{base_name}.md")
        else:
            base_name = os.path.splitext(path)[0]
            out_path = f"{base_name}.md"

        self.is_single_converting = True
        self._set_single_button(converting=True)
        self._status("#single-status", f"[yellow]Conversione in corso: {escape(os.path.basename(path))}...[/]")
        self.query_one("#single-progress", ProgressBar).update(total=None)
        self._log("Info", f"Avvio conversione: {os.path.basename(path)} -> {os.path.basename(out_path)}")

        def _worker():
            try:
                res = self.converter.convert(path, out_path)
                self.call_from_thread(self._on_single_success, res)
            except Exception as exc:
                self.call_from_thread(self._on_single_error, str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_single_success(self, out_path: str) -> None:
        self.is_single_converting = False
        self._set_single_button(converting=False)
        self.query_one("#single-progress", ProgressBar).update(total=100, progress=100)
        self._status("#single-status", f"[green]Convertito con successo: {escape(out_path)}[/]")
        self._log("Success", f"OK {os.path.basename(out_path)}")

    def _on_single_error(self, err_msg: str) -> None:
        self.is_single_converting = False
        self._set_single_button(converting=False)
        self.query_one("#single-progress", ProgressBar).update(total=100, progress=0)
        self._status("#single-status", f"[red]Errore: {escape(err_msg)}[/]")
        self._log("Error", f"Errore conversione: {err_msg}")

    # ------------------------------------------------------------------
    # Batch conversion
    # ------------------------------------------------------------------
    @on(Button.Pressed, "#batch-add")
    @on(Input.Submitted, "#batch-path")
    def _on_batch_add(self) -> None:
        raw = self.query_one("#batch-path", Input).value.strip().strip('"').strip("'")
        if not raw:
            self._log("Warning", "Nessun percorso o pattern inserito.")
            return

        expanded = os.path.expanduser(raw)
        files = []
        if os.path.isdir(expanded):
            # Scandisce i file supportati nella cartella
            for item in os.listdir(expanded):
                full = os.path.join(expanded, item)
                if os.path.isfile(full) and is_supported_file(full):
                    files.append(full)
        else:
            matched = sorted(glob.glob(expanded))
            files = [p for p in matched if os.path.isfile(p)]
            if not files and os.path.isfile(expanded):
                files = [expanded]

        if not files:
            self._log("Error", f"Nessun file trovato corrispondente a: {raw}")
            return

        queue = self.query_one("#batch-list", BatchFileList)
        added = 0
        for p in files:
            if queue.add_file(p):
                added += 1

        if added > 0:
            self._log("Info", f"Aggiunti {added} file alla coda batch.")
        else:
            self._log("Warning", "Tutti i file selezionati sono già presenti nella coda.")

        self._update_batch_count()
        self.query_one("#batch-path", Input).value = ""

    @on(Button.Pressed, "#batch-clear")
    def _on_batch_clear(self) -> None:
        self.query_one("#batch-list", BatchFileList).clear()
        self._update_batch_count()
        self._status("#batch-status", "[dim]Coda: 0 file.[/]")
        self.query_one("#batch-progress", ProgressBar).update(total=100, progress=0)
        self._log("Info", "Coda batch svuotata.")

    @on(Button.Pressed, "#batch-cancel")
    def _on_batch_cancel(self) -> None:
        if self.current_batch_worker:
            self.current_batch_worker.cancel()
            self._log("Warning", "Richiesto annullamento conversione batch...")
            self.query_one("#batch-cancel", Button).disabled = True

    @on(Button.Pressed, "#batch-convert")
    def _on_batch_convert(self) -> None:
        queue = self.query_one("#batch-list", BatchFileList)
        paths = queue.get_paths()
        if not paths:
            self._status("#batch-status", "[red]Coda vuota: aggiungi prima dei file.[/]")
            return
        if not self.has_engine or not self.converter:
            self._status("#batch-status", "[red]Motore MarkItDown non disponibile.[/]")
            self._log("Error", "Conversione batch impossibile: MarkItDown non inizializzato.")
            return

        raw_out_dir = self.query_one("#batch-output-dir", Input).value.strip().strip('"').strip("'")
        output_dir = os.path.abspath(os.path.expanduser(raw_out_dir)) if raw_out_dir else None

        self._set_batch_buttons(converting=True)
        queue.reset_statuses()
        total_files = len(paths)
        self._status("#batch-status", f"[yellow]Conversione di {total_files} file in corso...[/]")
        self.query_one("#batch-progress", ProgressBar).update(total=total_files, progress=0)
        self._log(
            "Info",
            f"Avvio batch di {total_files} file"
            + (f" verso {output_dir}" if output_dir else " (nelle rispettive cartelle)"),
        )

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
            ui(self._on_batch_progress, done, total)

        def on_complete(success, failed, cancelled):
            ui(self._on_batch_complete, success, failed, cancelled)

        self.current_batch_worker = BatchConversionWorker(
            self.converter,
            paths,
            output_dir=output_dir,
            callbacks={
                "on_file_start": on_file_start,
                "on_file_success": on_file_success,
                "on_file_error": on_file_error,
                "on_progress": on_progress,
                "on_complete": on_complete,
            },
        )
        self.current_batch_worker.start()

    def _on_batch_progress(self, done: int, total: int) -> None:
        self.query_one("#batch-progress", ProgressBar).update(total=total, progress=done)
        self._status("#batch-status", f"[yellow]Convertiti {done}/{total} file...[/]")

    def _on_batch_complete(self, success: int, failed: int, cancelled: bool) -> None:
        self.current_batch_worker = None
        self._set_batch_buttons(converting=False)
        tag = ", operazione annullata" if cancelled else ""
        self._status(
            "#batch-status",
            f"[dim]Completato: {success} riusciti, {failed} errori{tag}.[/]",
        )
        self._log("Info", f"Batch completato: {success} riusciti, {failed} errori{tag}.")
