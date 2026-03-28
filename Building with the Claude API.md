# Building with the Claude API

## Accessing the API

When building applications with Claude, understanding the complete request lifecycle helps you architect better systems and debug issues more effectively. Let's walk through what happens when a user sends a message to your AI-powered chat application.

### The Complete Request Flow

The journey from user input to AI response involves five distinct steps: Request to Server, Request to AI, Model Processing, Response to Server, and Response to Client. Each step plays a crucial role in delivering that "magical" response users expect.

### Why You Need a Server

Never make API requests directly from client-side code. Here's why:

* API requests require secret credentials that must stay secure
* Exposing credentials in client code makes them visible to anyone
* Your server acts as a secure intermediary between your app and AI
* Always route requests through your own server that you control and secure.

### Making the API Request

Your server communicates with Claude using Anthropic's official SDKs (Python, TypeScript, Go, and Ruby) or Google's official Vertex AI SDKs.

Every request must include these key fields:

* API Key - Identifies your request to Anthropic
* Model - Name of the specific model to use
* Messages - List containing the user's input text
* Max Tokens - Limits how many tokens the model can generate

The user's input gets placed inside a "user" message, which then goes into a list of messages sent to the API.

### Inside Claude: Text Generation Process

Once Claude receives your request, it processes it through four stages: Tokenization, Embedding, Contextualization, and Generation.

#### Tokenization

Claude first breaks down the input text into smaller chunks called tokens. These can be whole words, parts of words, spaces, or symbols. For simplicity, think of each word as one token.

#### Embedding

Each token gets converted into an embedding - a long list of numbers that represents all possible meanings of that word. Think of embeddings as number-based definitions.

#### Contextualization

Since words can have multiple meanings, Claude uses context to determine the right interpretation. The word "quantum" could refer to physics, computing, or just mean "very small" - context from surrounding words clarifies the intended meaning.

During contextualization, each embedding gets adjusted based on its neighbors, highlighting the meaning that makes most sense given the context.

#### Generation

The contextualized embeddings pass through an output layer that produces probabilities for each possible next word. Claude doesn't always pick the highest probability word - it uses a mix of probability and randomness to create more natural, varied responses.

After selecting a word, Claude adds it to the sequence and repeats the entire process for the next word.

#### When Generation Stops

After generating each token, Claude checks several conditions to decide whether to continue:

* Max tokens reached - Has it hit the limit you specified?
* Natural ending - Did it generate an end-of-sequence token?
* Stop sequence - Did it encounter a predefined stop phrase?

The end-of-sequence token is a special signal (not visible text) that Claude uses to indicate it has reached a natural conclusion.

#### The Response

Once generation completes, Claude sends a response back to your server containing:

* Message - The generated text
* Usage - Count of input and output tokens
* Stop Reason - Why the model stopped generating

Your server then forwards the generated text to your client application, where it appears in the chat interface.

#### The Complete Picture

This entire process - from user input through tokenization, embedding, contextualization, generation, and back to the user - happens in seconds. Understanding this flow helps you build more robust applications and troubleshoot issues when they arise.

*The key takeaway*: always use a server as an intermediary, understand that text generation is an iterative process, and pay attention to the response metadata to monitor usage and understand model behavior.

---

### Multi-turn conversations

Claude doesn't store any of your conversation history. Each request you make is completely independent, with no memory of previous exchanges. This means if you want to have a multi-turn conversation where Claude remembers context from earlier messages, you need to handle the conversation state yourself.

To maintain conversation context, you need to do two things:

* Manually maintain a list of all messages in your code
* Send the complete message history with every request

#### System prompts

System prompts are a powerful way to customize how Claude responds to user input. Instead of getting generic answers, you can shape Claude's tone, style, and approach to match your specific use case.

```python
def add_user_message(messages, text):
    user_message = {"role": "user", "content": text}
    messages.append(user_message)

def add_assistant_message(messages, text):
    assistant_message = {"role": "assistant", "content": text}
    messages.append(assistant_message)

def chat(messages, system=None, temperature=1.0, stop_sequences=None):
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "temperature": temperature
    }

    if stop_sequences:
        params["stop_sequences"] = stop_sequences

    if system:
        params["system"] = system
    
    message = client.messages.create(**params)
    return message.content[0].text
```

```python
# Example : Send the entire conversation history to Claude

# Make an initial list of messages
messages = []

# Use a 'while True' loop to run the chatbot forever
while True:

    user_input = input("> ")
    print(">", user_input)
    
    # Send your initial user message to Claude
    add_user_message(messages, user_input)
    # Take Claude's response and add it to your message list as an assistant message
    answer = chat(messages)
    # Add your follow-up question as another user message
    add_assistant_message(messages, answer)

    print(answer)
```

### Temperature

Temperature is a decimal value between 0 and 1 that directly influences these selection probabilities. It's like adjusting the "creativity dial" on Claude's responses.

#### Low Temperature (0.0 - 0.3)

* Factual responses
* Coding assistance
* Data extraction
* Content moderation

#### Medium Temperature (0.4 - 0.7)

* Summarization
* Educational content
* Problem-solving
* Creative writing with constraints

#### High Temperature (0.8 - 1.0)

* Brainstorming
* Creative writing
* Marketing content
* Joke generation

### Response streaming

In a typical chat setup, your server sends a user message to Claude and waits for the complete response before sending anything back to the client. This creates an awkward delay where users have no feedback that anything is happening.

With streaming enabled, Claude immediately sends back an initial response indicating it has received your request and is starting to generate text. Then you receive a series of events, each containing a small piece of the overall response.

Your server can forward these text chunks to your client application as they arrive, allowing users to see the response building up word by word. All of these events are part of a single request to Claude.

When you enable streaming, Claude sends back several types of events:

* MessageStart - A new message is being sent
* ContentBlockStart - Start of a new block containing text, tool use, or other content
* ContentBlockDelta - Chunks of the actual generated text
* ContentBlockStop - The current content block has been completed
* MessageDelta - The current message is complete
* MessageStop - End of information about the current message

#### Practical Considerations

Each text chunk in the stream can contain multiple words or even complete sentences - you're not guaranteed to receive exactly one word per event. The chunk size depends on how quickly Claude generates each portion of text.

In production applications, you'll typically forward these text chunks immediately to your client application through WebSockets or Server-Sent Events, allowing users to see responses appear in real-time while maintaining the complete conversation history on your server.

```python
with client.messages.stream(
    model=model,
    max_tokens=1000,
    messages=messages
) as stream:
    for text in stream.text_stream:
        print(text, end="")
```

This approach automatically filters out everything except the actual text content, which is usually what you need for displaying responses to users.

```python
with client.messages.stream(
    model=model,
    max_tokens=1000,
    messages=messages
) as stream:
    for text in stream.text_stream:
        pass  # Send to client in real application
    
    final_message = stream.get_final_message()
```

This gives you both the streaming capability for user experience and the complete message object for database storage or conversation history.

### Prefilled Assistant Messages

Message prefilling lets you provide the beginning of Claude's response, which it will then continue from that starting point. This technique is incredibly useful for steering Claude in a specific direction.

```python
messages = []
add_user_message(messages, "Is tea or coffee better at breakfast?")
add_assistant_message(messages, "Coffee is better because")
answer = chat(messages)
```

You can steer Claude in any direction using this technique:

* Favor coffee: "Coffee is better because"
* Favor tea: "Tea is better because"
* Take a contrarian stance: "Neither is very good because"

### Stop Sequences

Stop sequences force Claude to end its response as soon as it generates a specific string of characters. This is perfect for controlling the length or endpoint of responses.

```python
add_user_message(messages, "Count from 1 to 10")
answer = chat(messages, stop_sequences=[", 5"])
```

This returns: "1, 2, 3, 4" - stopping right before the "5" is included in the output.

### Structured data

* Combining Stop Sequences with Assistant Message Prefilling
* Cleaning Up the Output

```python
import json

messages = []

add_user_message(messages, "Generate a very short event bridge rule as json")
add_assistant_message(messages, "```json")

text = chat(messages, stop_sequences=["```"])
parsed_json = json.loads(text.strip())
```

---

### Provider Portability and Local Models

When app developers move computation to local open-source models — Ollama, LM Studio, vLLM, llama.cpp — a practical question arises: does the code need to be rewritten?

The answer depends entirely on which SDK was used to build the app.

#### OpenAI SDK: change `base_url`, nothing else

The OpenAI API format has become the de facto standard for local model servers. Most local inference engines implement an OpenAI-compatible endpoint.

```python
# Cloud (OpenAI)
client = OpenAI(api_key="sk-...")

# Local — two-line change, all other code unchanged
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="local"
)
```

`client.chat.completions.create(...)` calls, message format, and response parsing all stay the same. The SDK simply points at a different server.

#### Anthropic and Google SDKs: rewrite required

These SDKs communicate in their own protocol. Local model servers do not implement the Anthropic Messages API or Google genai format. Switching requires either:

* Rewriting to the OpenAI SDK
* Introducing a proxy layer that translates (e.g., LiteLLM)

#### SDK lock-in summary

| SDK | Local model portability |
|---|---|
| OpenAI SDK | Change `base_url` only |
| Anthropic SDK | Rewrite required |
| Google genai SDK | Rewrite required |

#### Architectural implication

If your application needs to remain portable across cloud providers and local compute, build against the OpenAI SDK format from the start — even when routing to Claude or Gemini via a proxy. This keeps the cost of changing compute providers as low as possible.
