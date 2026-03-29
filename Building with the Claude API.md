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

## Tool Use

### How Tool Use Works

Tool use lets Claude call functions you define or that Anthropic provides. Claude decides when to call a tool based on the user's request and the tool's description, then returns a structured call that your application executes (client tools) or that Anthropic executes (server tools).

* Initial Request: You send Claude a question along with instructions on how to get extra data from external sources
* Tool Request: Claude analyzes the question and decides it needs additional information, then asks for specific details about what data it needs
* Data Retrieval: Your server runs code to fetch the requested information from external APIs or databases
* Final Response: You send the retrieved data back to Claude, which then generates a complete response using both the original question and the fresh data

### Whrite a Tool Function

**A tool function** is a plain Python function that gets executed automatically when Claude determines it needs extra information to complete a task.

* Use descriptive names: Both your function name and parameter names should clearly indicate their purpose
* Validate inputs: Always check that required parameters are present and valid
* Provide meaningful error messages: If Claude gets an error, it might try calling your function again with corrected parameters

### Create a Tool Schema

**A tool schema** is a JSON schema that tells Claude what arguments your function expects and how to use it. This schema acts as documentation that Claude reads to understand when and how to call your tools.

* name - The function name (like "get_current_datetime")
* description - What the tool does and when to use it
* input_schema - The actual JSON schema describing the arguments

### Writing Effective Descriptions

The combination of a well-written tool function and a detailed JSON schema **gives Claude everything it needs to understand** and properly use your tools in conversations.

* Explain what the tool does, when to use it, and what it returns
* Aim for 3-4 sentences
* Provide detailed descriptions for each argument as well
* Use a consistent naming pattern like **function_name_schema** to keep things organized
* For better type checking, import and use the ToolParam type from the Anthropic library

###　The Easy Way: Let Claude Write Your Schema

* 1. Copy your tool function
* 2. Go to Claude and ask it to "Write a valid JSON schema spec for the purposes of tool calling for this function. Follow the best practices listed in the attached documentation."

###　Handling message blocks

To enable Claude to use tools, you need to include a **tools** parameter in your API call.
The **tools** parameter takes a list of JSON schemas that describe the available functions Claude can call.

```python
messages = []
messages.append({
    "role": "user",
    "content": "What is the exact time, formatted as HH:MM:SS?"
})

response = client.messages.create(
    model=model,
    max_tokens=1000,
    messages=messages,
    tools=[get_current_datetime_schema],
)
```

#### Understanding Multi-Block Messages

* Text Block - Human-readable text explaining what Claude is doing (like "I can help you find out the current time. Let me find that information for you")
* ToolUse Block - Instructions for your code about which tool to call and what parameters to use
  * An ID for tracking the tool call
  * The name of the function to call (like "get_current_datetime")
  * Input parameters formatted according to your JSON schema
  * The type designation "tool_use"

#### The Complete Flow

The fundamental principle of maintaining complete message history remains the same.

Claude doesn't store conversation history, so you must manage it manually. When working with tool responses, you need to preserve the entire content structure, including all blocks.

* 1. Send user message with tool schema to Claude
* 2. Receive multi-block assistant message (text + tool use)
* 3. Extract tool call information and execute the function

```python
# Access the tool use block
tool_use_block = response.content[1]

# Get the input parameters
input_params = tool_use_block.input

# Call your function with the parameters
result = get_current_datetime(**input_params)
```

* 4. Send tool result back to Claude with complete message history
* 5. Receive final response from Claude

#### Complete Messages History After a Tool Exchange

After one complete tool use cycle, your messages array contains four entries. Two of them use complex content block structures instead of plain strings — this is the part most implementations get wrong:

```python
messages = [
    # 1. Original user request — plain string content
    { "role": "user",
      "content": "What is the exact time, formatted as HH:MM:SS?" },

    # 2. Claude's multi-block response — preserve the ENTIRE content list, never flatten it
    { "role": "assistant",
      "content": [
          { "type": "text",
            "text": "I can help you find the current time. Let me check that for you." },
          { "type": "tool_use",
            "id":    "toolu_01Abc123",
            "name":  "get_current_datetime",
            "input": { "format": "%H:%M:%S" } }
      ]},

    # 3. Tool result — role is "user"; tool_use_id must exactly match step 2
    { "role": "user",
      "content": [
          { "type":        "tool_result",
            "tool_use_id": "toolu_01Abc123",   # ← must match id above
            "content":     "14:32:07" }
      ]},

    # 4. Claude's final answer — plain text, stop_reason is now "end_turn"
    { "role": "assistant",
      "content": "The current time is 14:32:07." },
]
```

Two critical rules:
* The assistant message that contains tool calls must be stored with its complete `content` list — never extract just the text and discard the tool_use blocks. Claude needs the full history to understand the context.
* The `tool_use_id` in the tool_result must exactly match the `id` Claude assigned in the tool_use block. Claude uses this pairing to correlate results with requests, especially when multiple tools are called in one turn.

#### Handling Multiple Tool Calls

Claude can request multiple tool calls in a single response.

Each tool use block gets a unique ID, and you must match these IDs when sending back results. This ID system ensures Claude can correctly match each result with its corresponding request, even if the results arrive in a different order.

**Example — calculating a date then setting a reminder:**

```
User: "Set a reminder for my doctor's appointment. It's 177 days after Jan 1st, 2050."

Claude turn 1 (stop_reason: "tool_use"):
  content[0]: text       → "Let me calculate that date and set the reminder."
  content[1]: tool_use   → add_duration_to_datetime(base="2050-01-01", days=177)  [id: "toolu_01"]
  content[2]: tool_use   → set_reminder(title="Doctor's appointment", date=???)   [id: "toolu_02"]
                                                 ↑ Claude may use a placeholder if it needs
                                                   the result of the first tool to fill this in

Your code:
  → run both tools in sequence (or parallel if independent)
  → return one user message with two tool_result blocks, IDs matching "toolu_01" and "toolu_02"

Claude turn 2 (stop_reason: "end_turn"):
  content[0]: text → "I've set a reminder for your doctor's appointment on June 27, 2050."
```

When Claude returns multiple `tool_use` blocks, your `run_tools()` function processes all of them and packages the results as a single `user` message containing a list of `tool_result` blocks — one per call, each matched by its unique ID.

```python
def add_user_message(messages, message):
    user_message = {
        "role": "user",
        "content": message.content if isinstance(message, Message) else message,
    }
    messages.append(user_message)


def add_assistant_message(messages, message):
    assistant_message = {
        "role": "assistant",
        "content": message.content if isinstance(message, Message) else message,
    }
    messages.append(assistant_message)


def chat(messages, system=None, temperature=1.0, stop_sequences=[], tools=None):
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "temperature": temperature,
        "stop_sequences": stop_sequences,
    }

    if tools:
        params["tools"] = tools

    if system:
        params["system"] = system

    message = client.messages.create(**params)
    return message


def text_from_message(message):
    return "\n".join(
        [block.text for block in message.content if block.type == "text"]
    )


def run_tool(tool_name, tool_input):
    if tool_name == "get_current_datetime":
        return get_current_datetime(**tool_input)
    elif tool_name == "add_duration_to_datetime":
        return add_duration_to_datetime(**tool_input)
    elif tool_name == "set_reminder":
        return set_reminder(**tool_input)


def run_tools(message):
    tool_requests = [
        block for block in message.content if block.type == "tool_use"
    ]
    tool_result_blocks = []

    for tool_request in tool_requests:
        try:
            tool_output = run_tool(tool_request.name, tool_request.input)
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": json.dumps(tool_output),
                "is_error": False,
            }
        except Exception as e:
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": f"Error: {e}",
                "is_error": True,
            }

        tool_result_blocks.append(tool_result_block)

    return tool_result_blocks


def run_conversation(messages):
    while True:
        response = chat(
            messages,
            tools=[
                get_current_datetime_schema,
                add_duration_to_datetime_schema,
                set_reminder_schema,
            ],
        )

        add_assistant_message(messages, response)
        print(text_from_message(response))

        if response.stop_reason != "tool_use":
            break

        tool_results = run_tools(response)
        add_user_message(messages, tool_results)

    return messages

messages = []
add_user_message(
    messages,
    "Set a reminder for my doctors appointment. Its 177 days after Jan 1st, 2050.",
)
run_conversation(messages)    

```

### The batch tool

* You define a batch tool schema that tells Claude it can run multiple other tools in parallel
* Instead of calling tools directly, Claude calls the batch tool with a list of tool invocations
* Your code processes this list and executes each tool call
* You return the combined results back to Claude

The batch tool pattern is an effective way to encourage Claude to think about operations that can be parallelized and execute them more efficiently.
