import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).parent / "env.local")
api_key = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=api_key)

print("--- Available Models ---")
try:
    # Iterate over model objects and inspect their attributes
    for model in client.models.list():
        # In the new SDK the identifier is exposed as the "name" attribute
        print(f"Name: {model.name}")
except Exception as e:
    print(f"Error: {e}")
