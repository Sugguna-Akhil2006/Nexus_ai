import sys
import os
import traceback
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.auth import AuthenticationAgent

try:
    a = AuthenticationAgent()
    a.initialize()
    print("State:", a.state)
    print("Status:", a.status)
except Exception as e:
    print("Error during direct init:")
    traceback.print_exc()
