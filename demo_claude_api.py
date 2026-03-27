"""
Demo: Claude API request lifecycle
Corresponds to concepts in "Claude with AI.md"
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import anthropic

# --- Step 1: Never hardcode API keys. Load from env.local file. ---
load_dotenv(Path(__file__).parent / "env.local")
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise EnvironmentError("ANTHROPIC_API_KEY not found in env.local.")

# --- Step 2: Initialize client (your "server-side" intermediary) ---
client = anthropic.Anthropic(api_key=api_key)

# --- Step 3: Build the request ---
# Required fields: model, max_tokens, messages
USER_INPUT = "In one sentence, what is tokenization?"

print("=== Request ===")
print(f"Model      : claude-haiku-4-5")
print(f"Max Tokens : 256")
print(f"User Input : {USER_INPUT}\n")

# --- Step 4: Send request to Claude ---
response = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=256,
    messages=[
        {"role": "user", "content": USER_INPUT}
    ]
)

# --- Step 5: Inspect the response ---
print("=== Response ===")
for block in response.content:
    if block.type == "text":
        print(f"Generated Text : {block.text}\n")

print("=== Response Metadata ===")
print(f"Stop Reason    : {response.stop_reason}")
print(f"Input Tokens   : {response.usage.input_tokens}")
print(f"Output Tokens  : {response.usage.output_tokens}")
