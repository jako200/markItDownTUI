import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tui.app import MarkItDownTUI


def main():
    try:
        app = MarkItDownTUI()
        app.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
