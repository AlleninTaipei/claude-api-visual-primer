"""
client3.py — Talks to YOUR server only.

This is what a browser, mobile app, or frontend would do.
"""

import urllib.request
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# --- Step 1: Configuration ---
load_dotenv(Path(__file__).parent / "env.local")

SERVER_URL = "http://localhost:5000/chat"
USER_INPUT = "In one sentence, what is tokenization?"

# Read the default provider from env; fall back to "google" if not set
PROVIDER = os.environ.get("DEFAULT_PROVIDER", "google").strip().lower()

print(f"=== Client (Provider: {PROVIDER}) ===")
print(f"Sending to : {SERVER_URL}")
print(f"Message    : {USER_INPUT}\n")

# Send request to OUR server
payload = json.dumps({
    "message": USER_INPUT,
    "provider": PROVIDER
}).encode()

req = urllib.request.Request(
    SERVER_URL,
    data=payload,
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read())

    print("=== Response from Server ===")
    print(f"Provider     : {data.get('provider')}")
    print(f"Reply        : {data['reply']}")
    print(f"Input Tokens : {data['input_tokens']}")
    print(f"Output Tokens: {data['output_tokens']}")
except Exception as e:
    print(f"Error: {e}")
