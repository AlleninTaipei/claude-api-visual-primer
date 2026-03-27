"""
Demo: API request lifecycle
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from google import genai

# --- Step 1: Configuration ---
load_dotenv(Path(__file__).parent / "env.local")

# Read provider from environment variable (defaults to "google")
PROVIDER = os.environ.get("DEFAULT_PROVIDER", "google") 

USER_INPUT = "In one sentence, what is tokenization?"

print(f"=== Request (Provider: {PROVIDER}) ===")

if PROVIDER == "anthropic":
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not found in env.local.")
    
    client = anthropic.Anthropic(api_key=api_key)
    model_name = "claude-haiku-4-5"
    
    print(f"Model      : {model_name}")
    print(f"User Input : {USER_INPUT}\n")

    response = client.messages.create(
        model=model_name,
        max_tokens=256,
        messages=[{"role": "user", "content": USER_INPUT}]
    )

    print("=== Response ===")
    print(f"Generated Text : {response.content[0].text}\n")
    print("=== Metadata ===")
    print(f"Input Tokens   : {response.usage.input_tokens}")
    print(f"Output Tokens  : {response.usage.output_tokens}")

elif PROVIDER == "google":
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY not found in env.local.")
    
    # Use default settings — generally most stable for preview models
    client = genai.Client(api_key=api_key)
    model_name = "gemini-3-flash-preview" 
    
    print(f"Model      : {model_name}")
    print(f"User Input : {USER_INPUT}\n")

    response = client.models.generate_content(
        model=model_name,
        contents=USER_INPUT
    )

    print("=== Response ===")
    print(f"Generated Text : {response.text}\n")
    print("=== Metadata ===")
    # usage_metadata is the token usage field in the new google-genai SDK
    print(f"Prompt Tokens  : {response.usage_metadata.prompt_token_count}")
    print(f"Output Tokens  : {response.usage_metadata.candidates_token_count}")
