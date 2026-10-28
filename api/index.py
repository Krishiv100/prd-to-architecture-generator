import sys
from pathlib import Path

# Add project root to sys.path so 'src' and modules are discoverable on Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.gui.server import ArchitectureGUIHandler

# Vercel Serverless Function entry point
class handler(ArchitectureGUIHandler):
    pass
