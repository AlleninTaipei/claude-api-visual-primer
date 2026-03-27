"""
client.py — Talks to YOUR server only. Has zero knowledge of Claude or the API Key.

This is what a browser, mobile app, or frontend would do.
"""

import urllib.request
import json

SERVER_URL = "http://localhost:5000/chat"
USER_INPUT = "In one sentence, what is tokenization?"

print("=== Client ===")
print(f"Sending to : {SERVER_URL}")
print(f"Message    : {USER_INPUT}")
print(f"API Key    : (none — client doesn't have it)\n")

# Send request to OUR server — not to Anthropic directly
payload = json.dumps({"message": USER_INPUT}).encode()
req = urllib.request.Request(
    SERVER_URL,
    data=payload,
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req) as res:
    data = json.loads(res.read())

print("=== Response from Server ===")
print(f"Reply        : {data['reply']}")
print(f"Stop Reason  : {data['stop_reason']}")
print(f"Input Tokens : {data['input_tokens']}")
print(f"Output Tokens: {data['output_tokens']}")
