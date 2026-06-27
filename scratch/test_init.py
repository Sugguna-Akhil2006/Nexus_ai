import traceback
from core.auth import AuthenticationAgent

try:
    a = AuthenticationAgent()
    a.initialize()
    print("State:", a.state)
    print("Status:", a.status)
except Exception as e:
    print("Error during direct init:")
    traceback.print_exc()
