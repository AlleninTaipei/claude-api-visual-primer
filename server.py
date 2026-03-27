"""
server.py — The secure intermediary between client and Claude.

Only this process holds the API Key.
The client never sees it.
"""

from flask import Flask, request, jsonify
import os
from pathlib import Path
from dotenv import load_dotenv
import anthropic

# --- API Key lives HERE, on the server. Never in the client. ---
load_dotenv(Path(__file__).parent / "env.local")
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise EnvironmentError("ANTHROPIC_API_KEY not found in env.local.")

claude = anthropic.Anthropic(api_key=api_key)
app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")

    print(f"[Server] Received: '{user_input}'")
    print("[Server] Calling Claude API with secret key... (client never sees this)")

    response = claude.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": user_input}]
    )

    reply = {
        "reply":         response.content[0].text,
        "stop_reason":   response.stop_reason,
        "input_tokens":  response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    print(f"[Server] Returning response to client (no API key included)")
    return jsonify(reply)

if __name__ == "__main__":
    print("Server running at http://localhost:5000")
    print("API Key is loaded — client will never see it.\n")
    app.run(port=5000)
