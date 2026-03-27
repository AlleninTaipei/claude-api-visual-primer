# claude-api-visual-primer

A hands-on learning kit that transforms Claude API documentation into three complementary formats: a polished reference document, an interactive browser-based visualizer, and a runnable Python demo.

The goal is to make the abstract mechanics of a large language model — tokenization, embedding, contextualization, and generation — concrete and explorable.

---

## Contents

| File | Type | Purpose |
|---|---|---|
| `Building with the Claude API.md` | Reference | Structured notes covering the full API request lifecycle and Claude's internal text generation process |
| `Building with the Claude API.html` | Interactive | Self-contained browser app — step through the four generation stages with animations and controls |
| `demo_claude_api.py` | Runnable demo | Minimal Python script that calls the real Claude API directly — a single-tier baseline |
| `server.py` | Server layer | Flask server that holds the API Key and proxies requests to Claude |
| `client.py` | Client layer | HTTP client with no API Key — communicates with `server.py` only |

---

## Interactive Visualizer

Open `Building with the Claude API.html` directly in any browser — no server required.

The demo walks through Claude's four internal stages for the input `"What is quantum computing?"`:

1. **Tokenization** — watch the input split into labelled tokens
2. **Embedding** — each token expands into its numeric vector representation
3. **Contextualization** — click any token to see how surrounding words resolve its meaning
4. **Generation** — step word-by-word through the output, with live next-word probability bars

Each stage pauses after its animation so you can review before advancing.

---

## Python Demos

### Prerequisites

```bash
pip install anthropic python-dotenv flask
```

### API Key Setup

Create `env.local` in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
```

> `env.local` is listed in `.gitignore` — never commit API keys.

---

### Single-tier baseline: `demo_claude_api.py`

Calls Claude directly. Simple and useful for exploration, but has no security boundary.

```bash
python3 demo_claude_api.py
```

```
=== Request ===
Model      : claude-haiku-4-5
Max Tokens : 256
User Input : In one sentence, what is tokenization?

=== Response ===
Generated Text : Tokenization is the process of breaking down text...

=== Response Metadata ===
Stop Reason    : end_turn
Input Tokens   : 16
Output Tokens  : 35
```

---

### Two-tier architecture: `server.py` + `client.py`

Demonstrates **why you need a server**. The API Key exists only in `server.py`. The client has no credentials — it only talks to your server.

```
Client → Your Server → Claude API
         (holds key)
```

**Terminal 1 — start the server:**

```bash
python3 server.py
```

```
Server running at http://localhost:5000
API Key is loaded — client will never see it.
```

**Terminal 2 — run the client:**

```bash
python3 client.py
```

```
=== Client ===
Sending to : http://localhost:5000/chat
Message    : In one sentence, what is tokenization?
API Key    : (none — client doesn't have it)

=== Response from Server ===
Reply        : Tokenization is the process of breaking down text into smaller units...
Stop Reason  : end_turn
Input Tokens : 16
Output Tokens: 36
```

---

## Concepts Covered

**API architecture**
- The five-step API request lifecycle (client → server → Claude → server → client)
- Why API keys must stay server-side
- Required fields for every Claude API request (`model`, `messages`, `max_tokens`)

**Text generation internals**
- Tokenization, embedding, contextualization, and iterative generation
- Stop conditions: `max_tokens`, `end_turn`, stop sequences
- Response metadata: generated text, stop reason, token usage

**Conversation control**
- Multi-turn conversations — maintaining message history across turns
- System prompts — shaping Claude's persona, tone, and constraints
- Temperature — from deterministic (0.0) to creative (1.0), with use-case guidance
- Response streaming — event types, forwarding chunks via WebSockets / SSE
- Prefilled assistant messages — steering response direction from the first word
- Stop sequences — halting generation at a specific string
- Structured data — combining prefilling + stop sequences to extract clean JSON

---

## Applicability

The methodology here — breaking a complex process into scaffolded, interactive steps — applies broadly to any domain where hidden or abstract mechanisms need to be taught: medical procedures, legal workflows, financial models, biological processes, or engineering systems.

---

## License

MIT

---

## Data Source

Learning materials are based on [Anthropic Academy](https://www.anthropic.com/learn).
