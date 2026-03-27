"""
Demo: API request lifecycle
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from google import genai
from openai import OpenAI

# --- Step 1: Configuration ---
load_dotenv(Path(__file__).parent / "env.local")

# Read provider from environment variable (defaults to "google")
PROVIDER = os.environ.get("DEFAULT_PROVIDER", "google").strip().lower()
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")
GOOGLE_MODEL = os.environ.get("GOOGLE_MODEL", "gemini-3-flash-preview")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

USER_INPUT = "In one sentence, what is tokenization?"

print(f"=== Request (Provider: {PROVIDER}) ===")

if PROVIDER == "anthropic":
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not found in env.local.")
    
    client = anthropic.Anthropic(api_key=api_key)
    model_name = ANTHROPIC_MODEL
    
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
    model_name = GOOGLE_MODEL
    
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

elif PROVIDER == "openai":
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY not found in env.local.")

    client = OpenAI(api_key=api_key)
    model_name = OPENAI_MODEL

    print(f"Model      : {model_name}")
    print(f"User Input : {USER_INPUT}\n")

    response = client.chat.completions.create(
        model=model_name,
        max_tokens=256,
        messages=[{"role": "user", "content": USER_INPUT}],
    )

    generated_text = response.choices[0].message.content or ""
    prompt_tokens = response.usage.prompt_tokens if response.usage else None
    output_tokens = response.usage.completion_tokens if response.usage else None

    print("=== Response ===")
    print(f"Generated Text : {generated_text}\n")
    print("=== Metadata ===")
    print(f"Prompt Tokens  : {prompt_tokens}")
    print(f"Output Tokens  : {output_tokens}")

else:
    raise ValueError(f"Unknown provider: {PROVIDER}")
