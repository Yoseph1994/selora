"""
Root entry point for Selora Prints.
Delegates to the 'bot' directory so root-level deployments (e.g. Render)
continue to work seamlessly without configuration changes.
"""
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BOT_DIR = ROOT_DIR / "bot"

os.chdir(BOT_DIR)
sys.path.insert(0, str(BOT_DIR))

if __name__ == "__main__":
    import runpy
    runpy.run_path(str(BOT_DIR / "main.py"), run_name="__main__")
