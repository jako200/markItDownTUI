"""
Test per il motore di conversione e helpers di MarkItDown TUI.

Eseguiti senza il pacchetto obbligatorio `markitdown` iniettando un motore simulato
per verificare il funzionamento completo della logica di conversione e del worker batch.
"""
import os
import shutil
import sys
import tempfile
import types
import unittest


class _FakeResult:
    def __init__(self, text):
        self.text_content = text


class _FakeEngine:
    def __init__(self):
        self.calls = []

    def convert(self, path):
        self.calls.append(path)
        return _FakeResult(f"# {os.path.basename(path)}\n")


def _inject_fake():
    mod = types.ModuleType("markitdown")
    mod.MarkItDown = _FakeEngine
    sys.modules["markitdown"] = mod


_inject_fake()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.converter import BatchConversionWorker, MarkdownConverter  # noqa: E402
from src.core.helpers import (  # noqa: E402
    SUPPORTED_EXTENSIONS,
    format_size,
    get_file_extension,
    get_file_type_description,
    is_supported_file,
)


class TestCore(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.src = os.path.join(self.dir, "orig.docx")
        with open(self.src, "wb") as f:
            f.write(b"dummy")

    def tearDown(self):
        if hasattr(self, "dir") and os.path.exists(self.dir):
            shutil.rmtree(self.dir, ignore_errors=True)

    def test_convert_writes_md(self):
        conv = MarkdownConverter()
        out = os.path.join(self.dir, "orig.md")
        result = conv.convert(self.src, out)
        self.assertEqual(result, os.path.abspath(out))
        self.assertTrue(os.path.exists(out))
        with open(out, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("# orig.docx", content)

    def test_convert_nested_output_dir(self):
        conv = MarkdownConverter()
        out = os.path.join(self.dir, "nested", "sub", "output.md")
        result = conv.convert(self.src, out)
        self.assertTrue(os.path.exists(result))

    def test_convert_missing_file_raises(self):
        conv = MarkdownConverter()
        with self.assertRaises(FileNotFoundError):
            conv.convert(self.src + ".missing", os.path.join(self.dir, "x.md"))

    def test_converter_is_available(self):
        conv = MarkdownConverter()
        self.assertTrue(conv.is_available())

    def test_converter_unavailable_raises(self):
        conv = MarkdownConverter()
        conv.md_engine = None
        self.assertFalse(conv.is_available())
        with self.assertRaises(RuntimeError):
            conv.convert(self.src, os.path.join(self.dir, "x.md"))

    def test_format_size(self):
        self.assertEqual(format_size(None), "N/A")
        self.assertEqual(format_size(-5), "N/A")
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(1536), "1.5 KB")
        self.assertEqual(format_size(1024 * 1024 * 10), "10.0 MB")
        self.assertEqual(format_size(1024 * 1024 * 1024 * 5), "5.0 GB")
        # Extremely large size should not IndexError
        self.assertIn("PB", format_size(1024 ** 6))

    def test_extension_helpers(self):
        self.assertEqual(get_file_extension("document.DOCX"), ".docx")
        self.assertEqual(get_file_extension("archive.tar.gz"), ".gz")
        self.assertTrue(is_supported_file("file.pdf"))
        self.assertTrue(is_supported_file("data.xlsx"))
        self.assertFalse(is_supported_file("image.png"))
        self.assertEqual(get_file_type_description("file.docx"), "Word Document")
        self.assertEqual(get_file_type_description("file.unknown"), "Unknown File")
        self.assertIn(".docx", SUPPORTED_EXTENSIONS)
        self.assertIn(".pdf", SUPPORTED_EXTENSIONS)

    def test_batch_worker(self):
        conv = MarkdownConverter()
        b = os.path.join(self.dir, "b.txt")
        with open(b, "w", encoding="utf-8") as f:
            f.write("hi")

        progress_calls = []
        worker = BatchConversionWorker(
            conv,
            [self.src, b],
            callbacks={
                "on_progress": lambda d, t: progress_calls.append((d, t)),
                "on_file_success": lambda inp, outp: None,
                "on_file_error": lambda inp, msg: None,
                "on_complete": lambda s, f, c: None,
            },
        )
        worker.start()
        worker.thread.join(timeout=5)
        self.assertEqual(len(conv.md_engine.calls), 2)
        self.assertEqual(progress_calls, [(1, 2), (2, 2)])

    def test_batch_worker_with_output_dir(self):
        conv = MarkdownConverter()
        custom_out_dir = os.path.join(self.dir, "batch_out")
        worker = BatchConversionWorker(
            conv,
            [self.src],
            output_dir=custom_out_dir,
        )
        worker.start()
        worker.thread.join(timeout=5)
        expected_md = os.path.join(custom_out_dir, "orig.md")
        self.assertTrue(os.path.exists(expected_md))

    def test_batch_worker_cancel(self):
        conv = MarkdownConverter()
        files = [os.path.join(self.dir, f"file_{i}.txt") for i in range(5)]
        for f in files:
            with open(f, "w", encoding="utf-8") as fp:
                fp.write("content")

        completed_data = {}

        def on_complete(s, f, c):
            completed_data["cancelled"] = c

        worker = BatchConversionWorker(
            conv,
            files,
            callbacks={"on_complete": on_complete},
        )
        worker.cancel()
        worker.start()
        worker.thread.join(timeout=5)
        self.assertTrue(completed_data.get("cancelled", False))


if __name__ == "__main__":
    unittest.main()
