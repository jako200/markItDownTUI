"""
Test per l'interfaccia utente Textual (MarkItDownTUI).
"""
import os
import shutil
import sys
import tempfile
import types
import unittest

from textual.widgets import Button, Input, Log, ProgressBar, Static, TabbedContent


class _FakeResult:
    def __init__(self, text):
        self.text_content = text


class _FakeEngine:
    def __init__(self):
        self.calls = []

    def convert(self, path):
        self.calls.append(path)
        return _FakeResult(f"# Converted: {os.path.basename(path)}\n")


def _inject_fake():
    mod = types.ModuleType("markitdown")
    mod.MarkItDown = _FakeEngine
    sys.modules["markitdown"] = mod


_inject_fake()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tui.app import BatchFileList, MarkItDownTUI  # noqa: E402


class TestMarkItDownTUI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.dir = tempfile.mkdtemp()
        self.doc1 = os.path.join(self.dir, "doc1.docx")
        self.doc2 = os.path.join(self.dir, "doc2.pdf")
        with open(self.doc1, "w", encoding="utf-8") as f:
            f.write("test doc 1")
        with open(self.doc2, "w", encoding="utf-8") as f:
            f.write("test doc 2")

    async def asyncTearDown(self):
        if hasattr(self, "dir") and os.path.exists(self.dir):
            shutil.rmtree(self.dir, ignore_errors=True)

    async def test_app_mount_and_tabs(self):
        app = MarkItDownTUI()
        async with app.run_test(size=(100, 30)) as pilot:
            self.assertEqual(pilot.app.title, "MarkItDown TUI")
            self.assertTrue(pilot.app.has_engine)
            tabbed = pilot.app.query_one(TabbedContent)
            self.assertEqual(tabbed.active, "single-tab")

            pilot.app.action_toggle_tab()
            await pilot.pause()
            self.assertEqual(tabbed.active, "batch-tab")

            pilot.app.action_toggle_tab()
            await pilot.pause()
            self.assertEqual(tabbed.active, "single-tab")

    async def test_log_and_clear(self):
        app = MarkItDownTUI()
        async with app.run_test(size=(100, 30)) as pilot:
            log_widget = pilot.app.query_one("#console", Log)
            pilot.app._log("Info", "Test message 123")
            await pilot.pause()
            last_line = log_widget.lines[-1]
            last_text = last_line.text if hasattr(last_line, "text") else str(last_line)
            self.assertIn("Test message 123", last_text)

            pilot.app.action_clear_log()
            await pilot.pause()
            self.assertEqual(len(log_widget.lines), 0)

    async def test_single_convert_empty_path(self):
        app = MarkItDownTUI()
        async with app.run_test(size=(100, 30)) as pilot:
            btn = pilot.app.query_one("#single-convert", Button)
            status = pilot.app.query_one("#single-status", Static)
            btn.press()
            await pilot.pause()
            self.assertIn("Inserisci un percorso", str(status.render()))

    async def test_single_convert_missing_file(self):
        app = MarkItDownTUI()
        async with app.run_test(size=(100, 30)) as pilot:
            inp = pilot.app.query_one("#single-path", Input)
            inp.value = os.path.join(self.dir, "nonexistent.docx")
            await pilot.pause()
            btn = pilot.app.query_one("#single-convert", Button)
            status = pilot.app.query_one("#single-status", Static)
            btn.press()
            await pilot.pause()
            self.assertIn("File non trovato", str(status.render()))

    async def test_single_convert_success(self):
        app = MarkItDownTUI()
        async with app.run_test(size=(100, 30)) as pilot:
            inp = pilot.app.query_one("#single-path", Input)
            inp.value = self.doc1
            await pilot.pause()

            status = pilot.app.query_one("#single-status", Static)
            self.assertIn("File pronto", str(status.render()))

            btn = pilot.app.query_one("#single-convert", Button)
            btn.press()

            for _ in range(50):
                await pilot.pause(0.05)
                if "Convertito con successo" in str(status.render()):
                    break

            self.assertIn("Convertito con successo", str(status.render()))
            expected_out = os.path.join(self.dir, "doc1.md")
            self.assertTrue(os.path.exists(expected_out))

    async def test_single_convert_custom_output(self):
        app = MarkItDownTUI()
        async with app.run_test(size=(100, 30)) as pilot:
            pilot.app.query_one("#single-path", Input).value = self.doc1
            custom_out = os.path.join(self.dir, "custom_named.md")
            pilot.app.query_one("#single-output-path", Input).value = custom_out

            btn = pilot.app.query_one("#single-convert", Button)
            btn.press()

            for _ in range(50):
                await pilot.pause(0.05)
                if os.path.exists(custom_out):
                    break

            self.assertTrue(os.path.exists(custom_out))

    async def test_batch_add_and_clear(self):
        app = MarkItDownTUI()
        async with app.run_test(size=(100, 30)) as pilot:
            pilot.app.action_toggle_tab()
            await pilot.pause()

            batch_inp = pilot.app.query_one("#batch-path", Input)
            batch_inp.value = os.path.join(self.dir, "*.docx")
            add_btn = pilot.app.query_one("#batch-add", Button)
            add_btn.press()
            await pilot.pause()

            b_list = pilot.app.query_one("#batch-list", BatchFileList)
            self.assertEqual(len(b_list.get_paths()), 1)

            # Test directory add
            batch_inp.value = self.dir
            add_btn.press()
            await pilot.pause()
            # doc2 should be added as well
            self.assertEqual(len(b_list.get_paths()), 2)

            # Test clear
            clear_btn = pilot.app.query_one("#batch-clear", Button)
            clear_btn.press()
            await pilot.pause()
            self.assertEqual(len(b_list.get_paths()), 0)

    async def test_batch_convert_success(self):
        app = MarkItDownTUI()
        async with app.run_test(size=(100, 30)) as pilot:
            pilot.app.action_toggle_tab()
            await pilot.pause()

            b_list = pilot.app.query_one("#batch-list", BatchFileList)
            b_list.add_file(self.doc1)
            b_list.add_file(self.doc2)
            pilot.app._update_batch_count()

            out_dir = os.path.join(self.dir, "out_batch")
            pilot.app.query_one("#batch-output-dir", Input).value = out_dir

            btn_convert = pilot.app.query_one("#batch-convert", Button)
            btn_convert.press()

            status = pilot.app.query_one("#batch-status", Static)
            for _ in range(50):
                await pilot.pause(0.05)
                if "Completato" in str(status.render()):
                    break

            self.assertIn("Completato", str(status.render()))
            self.assertTrue(os.path.exists(os.path.join(out_dir, "doc1.md")))
            self.assertTrue(os.path.exists(os.path.join(out_dir, "doc2.md")))


if __name__ == "__main__":
    unittest.main()
