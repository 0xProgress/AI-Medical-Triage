# test_token.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Try loading from different locations
env_paths = [
    Path("backend/.env"),
    Path(".env"),
    Path("../backend/.env"),
]

loaded = False
for path in env_paths:
    if path.exists():
        print(f"✅ Found .env at: {path}")
        load_dotenv(path)
        loaded = True
        break

if not loaded:
    print("❌ No .env file found!")
    print("Looking in:", [str(p) for p in env_paths])
    exit(1)

token = os.getenv("HF_API_TOKEN")
print(f"Token found: {'YES' if token else 'NO'}")
print(f"Token starts with: {token[:10] if token else 'None'}...")