#!/usr/bin/env python3
"""
Send the same prompt to Anthropic, OpenAI, and Google Gemini.
Confirms all three APIs are reachable and responding correctly.
Reads API keys from ~/.hermes/.env
"""

import ssl
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# macOS SSL fix
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# ── The shared test prompt ────────────────────────────────────────────────────
TEST_PROMPT = (
    "Reply in exactly one sentence: "
    "What is your model name and who made you?"
)
# ─────────────────────────────────────────────────────────────────────────────


def load_env(path="~/.hermes/.env"):
    env = {}
    p = Path(path).expanduser()
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def http_post(url, payload, headers):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
        except Exception:
            body = {"raw": e.reason}
        return e.code, body
    except Exception as ex:
        return None, {"error": str(ex)}


def call_anthropic(api_key):
    status, data = http_post(
        "https://api.anthropic.com/v1/messages",
        payload={
            "model": "claude-haiku-4-5",
            "max_tokens": 128,
            "messages": [{"role": "user", "content": TEST_PROMPT}],
        },
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    if status == 200:
        text = data["content"][0]["text"].strip()
        model = data.get("model", "?")
        tokens_in = data.get("usage", {}).get("input_tokens", "?")
        tokens_out = data.get("usage", {}).get("output_tokens", "?")
        return True, text, model, f"in={tokens_in} out={tokens_out}"
    else:
        err = data.get("error", {})
        msg = err.get("message", str(data)) if isinstance(err, dict) else str(err)
        return False, msg, None, None


def call_openai(api_key):
    status, data = http_post(
        "https://api.openai.com/v1/chat/completions",
        payload={
            "model": "gpt-4o-mini",
            "max_tokens": 128,
            "messages": [{"role": "user", "content": TEST_PROMPT}],
        },
        headers={
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        },
    )
    if status == 200:
        text = data["choices"][0]["message"]["content"].strip()
        model = data.get("model", "?")
        usage = data.get("usage", {})
        tokens_in = usage.get("prompt_tokens", "?")
        tokens_out = usage.get("completion_tokens", "?")
        return True, text, model, f"in={tokens_in} out={tokens_out}"
    else:
        err = data.get("error", {})
        msg = err.get("message", str(data)) if isinstance(err, dict) else str(err)
        return False, msg, None, None

'''
def call_google(api_key):
    model_name = "gemini-3-flash-preview"
    status, data = http_post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}",
        payload={
            "contents": [{"parts": [{"text": TEST_PROMPT}]}],
            "generationConfig": {"maxOutputTokens": 128},
        },
        headers={"content-type": "application/json"},
    )
    if status == 200:
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        usage = data.get("usageMetadata", {})
        tokens_in = usage.get("promptTokenCount", "?")
        tokens_out = usage.get("candidatesTokenCount", "?")
        return True, text, model_name, f"in={tokens_in} out={tokens_out}"
    else:
        err = data.get("error", {})
        msg = err.get("message", str(data)) if isinstance(err, dict) else str(err)
        return False, msg, None, None
'''

def call_google(api_key):
    # 使用最新的 Flash 3 預覽版
    model_name = "gemini-3-flash-preview"
    
    status, data = http_post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}",
        payload={
            "contents": [{"parts": [{"text": TEST_PROMPT}]}],
            "generationConfig": {"maxOutputTokens": 128},
        },
        headers={"content-type": "application/json"},
    )
    
    if status == 200:
        # 確保 data 結構存在，增加一點防禦性
        try:
            candidate = data["candidates"][0]
            text = candidate["content"]["parts"][0]["text"].strip()
            
            usage = data.get("usageMetadata", {})
            tokens_in = usage.get("promptTokenCount", "?")
            tokens_out = usage.get("candidatesTokenCount", "?")
            
            return True, text, model_name, f"in={tokens_in} out={tokens_out}"
        except (KeyError, IndexError):
            return False, "Malformed response content", model_name, None
            
    else:
        # 針對不同狀態碼提供更友善的錯誤訊息
        err = data.get("error", {})
        msg = err.get("message", "Unknown error occurred")
        
        if status == 429:
            msg = f"Rate Limit/Quota Exceeded (429): {msg}"
        elif status == 401 or status == 403:
            msg = f"Auth/Permission Error ({status}): Check your API Key"
            
        return False, msg, model_name, None

def run_check(name, key_name, api_key, call_fn):
    print(f"\n{'='*54}")
    print(f"  {name}  ({key_name})")
    print(f"{'='*54}")
    if not api_key:
        print(f"  [SKIP] {key_name} 未設定")
        return

    t0 = time.time()
    ok, reply, model, tokens = call_fn(api_key)
    elapsed = time.time() - t0

    if ok:
        print(f"  狀態  : OK  ({elapsed:.2f}s)")
        print(f"  模型  : {model}")
        print(f"  Tokens: {tokens}")
        print(f"  回覆  : {reply}")
    else:
        print(f"  狀態  : FAIL ({elapsed:.2f}s)")
        print(f"  錯誤  : {reply}")


def main():
    print("=" * 54)
    print("  API Health Check")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 54)
    print(f"\n  Prompt: \"{TEST_PROMPT}\"")

    env = load_env()

    run_check("Anthropic",       "ANTHROPIC_API_KEY", env.get("ANTHROPIC_API_KEY"), call_anthropic)
    run_check("OpenAI",          "OPENAI_API_KEY",    env.get("OPENAI_API_KEY"),    call_openai)
    run_check("Google (Gemini)", "GOOGLE_API_KEY",    env.get("GOOGLE_API_KEY"),    call_google)

    print(f"\n{'='*54}")
    print("  完成")
    print(f"{'='*54}\n")


if __name__ == "__main__":
    main()
