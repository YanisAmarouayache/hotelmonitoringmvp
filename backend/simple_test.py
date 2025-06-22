#!/usr/bin/env python3
import sys
import os

print("Python version:", sys.version)
print("Current directory:", os.getcwd())

try:
    import playwright
    print("✅ Playwright importé avec succès")
except ImportError as e:
    print(f"❌ Erreur import Playwright: {e}")

try:
    import asyncio
    print("✅ Asyncio importé avec succès")
except ImportError as e:
    print(f"❌ Erreur import asyncio: {e}")

print("Test terminé!") 