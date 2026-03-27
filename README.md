# claude-api-visual-primer

A hands-on learning kit that transforms Claude API documentation into three complementary formats: a polished reference document, an interactive browser-based visualizer, and a runnable Python demo.

The goal is to make the abstract mechanics of a large language model — tokenization, embedding, contextualization, and generation — concrete and explorable.

---

## Contents

| File | Type | Purpose |
|---|---|---|
| `Building with the Claude API.md` | Reference | Structured notes covering the full API request lifecycle and Claude's internal text generation process |
| `Building with the Claude API.html` | Interactive | Self-contained browser app — step through the four generation stages with animations and controls |
| `demo_claude_api.py` | Phase 1 demo | Minimal Python script that calls the Anthropic API directly — single-tier baseline |
| `server.py` | Phase 1 server | Flask server that holds the API Key and proxies requests to Claude |
| `client.py` | Phase 1 client | HTTP client with no API Key — communicates with `server.py` only |
| `demo_api.py` | Phase 2 demo | Extended demo supporting Anthropic, Google, and OpenAI providers side-by-side |
| `server3.py` | Phase 2 server | Multi-provider Flask server — routes requests to Claude, Gemini, or GPT |
| `client3.py` | Phase 2 client | HTTP client that selects provider via `DEFAULT_PROVIDER` env var |
| `list_models.py` | Utility | Lists all available Google Gemini models via the genai SDK |
| `requirements.txt` | Config | Pinned dependency list for all Phase 1 and Phase 2 scripts |

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
pip install -r requirements.txt
```

### API Key Setup

Create `env.local` in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
OPENAI_API_KEY=sk-...
DEFAULT_PROVIDER=google

# Optional — override model names
# ANTHROPIC_MODEL=claude-haiku-4-5
# GOOGLE_MODEL=gemini-3-flash-preview
# OPENAI_MODEL=gpt-4o-mini
```

> `env.local` is listed in `.gitignore` — never commit API keys.

---

## Phase 1 — Single Provider (Anthropic only)

The goal here is to understand the API request lifecycle and why a server layer is needed.

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

## Phase 2 — Multi-Provider (Anthropic + Google + OpenAI)

The goal here is to compare request/response formats across providers and build a server that can route to any of them.

### Provider comparison: `demo_api.py`

Calls Claude, Gemini, or GPT based on `DEFAULT_PROVIDER` in `env.local`.

```bash
python3 demo_api.py
```

| | Anthropic | Google (genai) | OpenAI |
|---|---|---|---|
| Client init | `anthropic.Anthropic(api_key=...)` | `genai.Client(api_key=...)` | `OpenAI(api_key=...)` |
| Request call | `client.messages.create(model, max_tokens, messages)` | `client.models.generate_content(model, contents)` | `client.chat.completions.create(model, max_tokens, messages)` |
| Response text | `response.content[0].text` | `response.text` | `response.choices[0].message.content` |
| Token usage | `response.usage.input_tokens` | `response.usage_metadata.prompt_token_count` | `response.usage.prompt_tokens` |

### Multi-provider architecture: `server3.py` + `client3.py`

Same two-tier pattern as Phase 1, extended to route requests to any provider.

```
Client → Your Server → Claude API
         (holds keys) → Gemini API
                      → OpenAI API
```

**Terminal 1 — start the server:**

```bash
python3 server3.py
```

**Terminal 2 — run the client:**

```bash
python3 client3.py
```

The provider is resolved in this order: request param → `DEFAULT_PROVIDER` env var → `"google"`. Valid values: `anthropic`, `google`, `openai`.

### Discover available models: `list_models.py`

Lists all Gemini model names accessible under your API Key.

```bash
python3 list_models.py
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
