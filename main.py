import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tui.app import MarkItDownTUI

if __name__ == "__main__":
    MarkItDownTUI().run()
