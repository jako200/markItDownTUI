"""
Test di base per il motore di conversione (portabile).

Eseguiti senza il vero pacchetto `markitdown` iniettando un motore finto,
cosi da dimostrare che la logica di base (converter + worker batch) funziona.
"""
import os
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

from src.core.converter import MarkdownConverter, BatchConversionWorker  # noqa: E402
from src.core.helpers import SUPPORTED_EXTENSIONS, format_size  # noqa: E402


class TestCore(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.src = os.path.join(self.dir, "orig.docx")
        with open(self.src, "wb") as f:
            f.write(b"dummy")

    def test_convert_writes_md(self):
        conv = MarkdownConverter()
        out = os.path.join(self.dir, "orig.md")
        result = conv.convert(self.src, out)
        self.assertEqual(result, os.path.abspath(out))
        self.assertTrue(os.path.exists(out))
        self.assertIn("# orig.docx", open(out, encoding="utf-8").read())

    def test_convert_missing_file_raises(self):
        conv = MarkdownConverter()
        with self.assertRaises(FileNotFoundError):
            conv.convert(self.src + ".missing", os.path.join(self.dir, "x.md"))

    def test_format_size(self):
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(1536), "1.5 KB")

    def test_supported_extensions(self):
        self.assertIn(".docx", SUPPORTED_EXTENSIONS)
        self.assertIn(".pdf", SUPPORTED_EXTENSIONS)

    def test_batch_worker(self):
        conv = MarkdownConverter()
        b = os.path.join(self.dir, "b.txt")
        with open(b, "w", encoding="utf-8") as f:
            f.write("hi")
        worker = BatchConversionWorker(
            conv, [self.src, b],
            callbacks={
                "on_progress": lambda d, t: None,
                "on_file_success": lambda inp, outp: None,
                "on_file_error": lambda inp, msg: None,
                "on_complete": lambda s, f, c: None,
            },
        )
        worker.start()
        worker.thread.join(timeout=5)
        self.assertEqual(len(conv.md_engine.calls), 2)


if __name__ == "__main__":
    unittest.main()
