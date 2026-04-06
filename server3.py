"""
server3.py — The secure intermediary between client and Server.

Only this process holds the API Key.
The client never sees it.
"""

from flask import Flask, request, jsonify
import os
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from google import genai
from openai import OpenAI

# --- API Key lives HERE, on the server. ---
load_dotenv(Path(__file__).parent / "env.local")

# Initialize clients if keys exist
anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
google_key = os.environ.get("GOOGLE_API_KEY")
openai_key = os.environ.get("OPENAI_API_KEY")
anthropic_model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")
google_model = os.environ.get("GOOGLE_MODEL", "gemini-3-flash-preview")
openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
lmstudio_model = os.environ.get("LMSTUDIO_MODEL", "meta-llama-3-8b-instruct")
ollama_model = os.environ.get("OLLAMA_MODEL", "gemma3:1b")

claude_client = anthropic.Anthropic(api_key=anthropic_key) if anthropic_key else None
# New google-genai Client
gemini_client = genai.Client(api_key=google_key) if google_key else None
openai_client = OpenAI(api_key=openai_key) if openai_key else None
lmstudio_client = OpenAI(base_url="http://localhost:1234/v1", api_key="local")
ollama_client = OpenAI(base_url="http://localhost:11434/v1", api_key="local")

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")
    
    # Priority: request param > env var (DEFAULT_PROVIDER) > hardcoded default ("google")
    env_default = os.environ.get("DEFAULT_PROVIDER", "google")
    provider = (data.get("provider") or env_default).strip().lower()

    print(f"[Server] Received: '{user_input}' (Provider: {provider})")

    if provider == "anthropic":
        if not claude_client:
            return jsonify({"error": "Anthropic API key not configured"}), 500
        
        response = claude_client.messages.create(
            model=anthropic_model,
            max_tokens=256,
            messages=[{"role": "user", "content": user_input}]
        )
        reply = {
            "reply":         response.content[0].text,
            "provider":      "anthropic",
            "input_tokens":  response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
    
    elif provider == "google":
        if not gemini_client:
            return jsonify({"error": "Google API key not configured"}), 500
        
        # New call pattern for google-genai
        response = gemini_client.models.generate_content(
            model=google_model,
            contents=user_input
        )
        reply = {
            "reply":         response.text,
            "provider":      "google",
            "input_tokens":  response.usage_metadata.prompt_token_count,
            "output_tokens": response.usage_metadata.candidates_token_count,
        }
    elif provider == "openai":
        if not openai_client:
            return jsonify({"error": "OpenAI API key not configured"}), 500

        response = openai_client.chat.completions.create(
            model=openai_model,
            max_tokens=256,
            messages=[{"role": "user", "content": user_input}],
        )
        reply = {
            "reply":         response.choices[0].message.content or "",
            "provider":      "openai",
            "input_tokens":  response.usage.prompt_tokens if response.usage else None,
            "output_tokens": response.usage.completion_tokens if response.usage else None,
        }
    elif provider == "lmstudio":
        response = lmstudio_client.chat.completions.create(
            model=lmstudio_model,
            max_tokens=256,
            messages=[{"role": "user", "content": user_input}],
        )
        reply = {
            "reply":         response.choices[0].message.content or "",
            "provider":      "lmstudio",
            "input_tokens":  response.usage.prompt_tokens if response.usage else None,
            "output_tokens": response.usage.completion_tokens if response.usage else None,
        }
    elif provider == "ollama":
        response = ollama_client.chat.completions.create(
            model=ollama_model,
            max_tokens=256,
            messages=[{"role": "user", "content": user_input}],
        )
        reply = {
            "reply":         response.choices[0].message.content or "",
            "provider":      "ollama",
            "input_tokens":  response.usage.prompt_tokens if response.usage else None,
            "output_tokens": response.usage.completion_tokens if response.usage else None,
        }
    else:
        return jsonify({"error": "Unknown provider"}), 400

    print(f"[Server] Returning response from {provider}")
    return jsonify(reply)

if __name__ == "__main__":
    print("Server running at http://localhost:5000")
    app.run(port=5000)
