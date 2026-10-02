import os
import sys
from pathlib import Path

# Add project root to sys.path so 'app' can be found
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.main import app

# Vercel serverless entrypoint
handler = app
