# Building with the Claude API

*Reference: [anthropic.com/learn](https://www.anthropic.com/learn)*

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

---

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

---

## Workflows and Agents

**Workflows** are a series of calls to Claude meant to solve a specific problem through a predetermined series of steps.

**Agents** are a setup where Claude is given a goal and tools, then figures out how to complete the goal.

### Real-World Workflow Examples

#### 1. Users drag and drop an image of a metal part, and the app creates a STEP file (an industry standard for 3D models)

The Evaluator-Optimizer Pattern

* Producer: Takes input and creates output (Claude using **CadQuery** to model and render)
* Grader: Evaluates the output against criteria
* Feedback loop: If the grader rejects the output, feedback goes back to the producer for improvement
* Acceptance: The cycle continues until the grader accepts the output

#### 2. Users upload images of parts and get recommendations for the best material to use

The Parallelization Pattern

* Split a single complex task into multiple specialized sub-tasks
  * One request analyzes suitability for metal
  * Another evaluates polymer options
  * A third considers ceramic materials
  * And so on for each material type
* Run the sub-tasks in parallel (simultaneously)
* Aggregate the results together in a final step

#### 3. Using Claude to write technical articles. You start with a simple prompt, but the output isn't quite right. Claude might mention it's an AI, use too many emojis, or write in a cringey tone

Instead of fighting this in one massive prompt, use a two-step chaining approach:

* First request: Send your original prompt with all constraints, accepting that you'll get an imperfect article

* Second request: Ask Claude to revise the article with specific, focused instructions
  * Revise the article provided below. Follow these steps to rewrite the article: 1. Identify any location where the text identifies the author as an AI and remove them 2. Find and remove all emojis 3. Locate any cringey writing and replace it with text that would be written by a technical writer

The Chaining Solution

* Split large tasks into smaller, non-parallelizable subtasks
* Optionally do non-LLM processing between each task
* Keep Claude focused on one aspect of the overall task

This approach becomes especially valuable when dealing with complex tasks or when Claude isn't consistently following all your constraints.

#### 4. Consider a social media marketing tool that generates video scripts from user topics

Routing workflow

* Categorization: Send the user's topic to Claude with a categorization prompt asking it to classify the content type.
* Specialized Processing: Based on Claude's categorization, use the appropriate specialized pipeline. Each pipeline has its own workflow, prompts, or tools to generate the actual content.

### Provide Reasonably Abstract Tools

When designing tools for agents, aim for tools that are broad enough to be reusable across different tasks, but specific enough that Claude can reliably understand what each one does. Tools that are too granular force Claude to chain many small steps together; tools that are too broad become unpredictable. The list below represents a well-balanced set for a general-purpose coding agent:

* bash - Run commands
* glob - Find files
* grep - Search file contents
* read - Read a file
* write - Create a file
* edit - Edit a file
* webfetch - Fetch a URL
* generate_image - Creates images from text prompts
* text_to_speech - Converts text to audio
* post_media - Publishes content to social media

### Real-World Agent Examples

#### 1. Install dependencies
  
* Agent reads project files to understand the configuration
* Then uses bash to run the appropriate installation commands

#### 2. Create and post a video on "Python programming"

Agent Verification and Inspection

* Agent can generate a sample image, show it to the user for approval
* Proceed with video creation
  * Use the bash tool to run whisper.cpp and generate caption files with timestamps to verify dialog placement
  * Use FFmpeg to extract screenshots from the video at regular intervals to confirm visual quality
  * Check file sizes and formats before attempting uploads
* Publish once confirmed

By building environment inspection into your agents, you create more reliable and self-correcting systems that can handle unexpected results gracefully.

Every action an agent takes should be followed by some form of verification or inspection to confirm the desired outcome was achieved.

### Choosing the Right Approach

**Prefer Workflows over Agents.**

While agents are really interesting from a technical perspective, remember that your primary goal as an engineer is to solve problems reliably. Users probably don't care that you've built a fancy agent - they want a product that works 100% of the time.

The general recommendation is to always focus on implementing workflows where possible, and only resort to agents when they are truly required. Workflows give you the predictability and reliability that most production applications need, while agents provide flexibility for scenarios where the exact solution path can't be predetermined.

---

## Introducing MCP

Model Context Protocol (MCP) is a communication layer that provides Claude with context and tools without requiring you to write a bunch of tedious integration code.

* Who Creates MCP Servers
  * Anyone can create an MCP Server implementation. Often, service providers themselves will create official MCP implementations. For example, Github might release their own official MCP Server with tools for their massive services.
  * With a pre-built MCP server, you don't have to manually write tool schemas for every capability — tools covering repositories, pull requests, issues, and more are already defined for you.

* How is using an MCP Server different from calling a service's API directly?
  * MCP Servers provide **tool schemas** and **functions** already defined for you. If you call an API directly, you'll be writing those tool definitions yourself. MCP saves you that implementation work.

* MCP Servers and tool use are complementary but different concepts.
  * MCP Servers provide pre-built tool schemas and functions, while tool use is about how Claude actually calls those tools. MCP is really about who does the work of creating and maintaining the tool implementations.

* MCP Inspector
  * The Python MCP SDK includes a built-in browser-based inspector that lets you debug and test your server in real-time.

* Real-world projects : You typically implement either an MCP client or an MCP server, not both. You might build:
  * Just an MCP server to expose your service's capabilities to AI models
  * Just an MCP client to connect to existing MCP servers built by other developers

### MCP Clients

The MCP client serves as the communication bridge between your application and external MCP servers.

The most common setup runs both the MCP client and server on the same machine, where they communicate through standard input/output.

MCP clients and servers can also connect over HTTP, WebSockets and Various other network protocols.

Here's a complete example showing how a user query flows through the entire system - from your server, through the MCP client, to external services like GitHub, and back to Claude.

Let's say a user asks "What repositories do I have?" Here's the step-by-step flow:

* User Query: The user submits their question to your server
* Tool Discovery: Your server needs to know what tools are available to send to Claude
* List Tools Exchange: Your server asks the MCP client for available tools
* MCP Communication: The MCP client sends a **ListToolsRequest** to the MCP server and receives a **ListToolsResult**
* Claude Request: Your server sends the user's query plus the available tools to Claude
* Tool Use Decision: Claude decides it needs to call a tool to answer the question
* Tool Execution Request: Your server asks the MCP client to run the tool Claude specified
* External API Call: The MCP client sends a **CallToolRequest** to the MCP server, which makes the actual GitHub API call
* Results Flow Back: GitHub responds with repository data, which flows back through the MCP server as a **CallToolResult**
* Tool Result to Claude: Your server sends the tool results back to Claude
* Final Response: Claude formulates a final answer using the repository data
* User Gets Answer: Your server delivers Claude's response back to the user

### Setting Up the MCP Server

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DocumentMCP", log_level="ERROR")
```

* No manual JSON schema writing required
* Type hints provide automatic parameter validation
* Field descriptions help Claude understand tool usage
* Error handling integrates naturally with Python exceptions
* Tool registration happens automatically through decorators

```python
@mcp.tool(
    name="read_doc_contents",
    description="Read the contents of a document and return it as a string.",
)
def read_document(
    doc_id: str = Field(description="Id of the document to read"),
) -> str:
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")

    return docs[doc_id]


@mcp.tool(
    name="edit_document",
    description="Edit a document by replacing a string in the documents content with a new string",
)
def edit_document(
    doc_id: str = Field(description="Id of the document that will be edited"),
    old_str: str = Field(
        description="The text to replace. Must match exactly, including whitespace"
    ),
    new_str: str = Field(
        description="The new text to insert in place of the old text"
    ),
) -> None:
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")

    docs[doc_id] = docs[doc_id].replace(old_str, new_str)


@mcp.resource("docs://documents", mime_type="application/json")
def list_docs() -> list[str]:
    return list(docs.keys())


@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
def fetch_doc(doc_id: str) -> str:
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    return docs[doc_id]


@mcp.prompt(
    name="format",
    description="Rewrites the contents of the document in Markdown format.",
)
def format_document(
    doc_id: str = Field(description="Id of the document to format"),
) -> list[base.Message]:
    prompt = f"""
    Your goal is to reformat a document to be written with markdown syntax.

    The id of the document you need to reformat is:
    <document_id>
    {doc_id}
    </document_id>

    Add in headers, bullet points, tables, etc as necessary. Feel free to add in extra text, but don't change the meaning of the report.
    Use the 'edit_document' tool to edit the document. After the document has been edited, respond with the final version of the doc. Don't explain your changes.
    """

    return [base.UserMessage(prompt)]

```

### Implementing a client

* MCP Client - A custom class we create to make using the session easier
* Client Session - The actual connection to the server (part of the MCP Python SDK)

```python
class MCPClient:
    def __init__(
        self,
        command: str,
        args: list[str],
        env: Optional[dict] = None,
    ):
        self._command = command
        self._args = args
        self._env = env
        self._session: Optional[ClientSession] = None
        self._exit_stack: AsyncExitStack = AsyncExitStack()

    async def connect(self):
        server_params = StdioServerParameters(
            command=self._command,
            args=self._args,
            env=self._env,
        )
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        _stdio, _write = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(_stdio, _write)
        )
        await self._session.initialize()

    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError(
                "Client session not initialized or cache not populated. Call connect_to_server first."
            )
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        result = await self.session().list_tools()
        return result.tools

    async def call_tool(
        self, tool_name: str, tool_input
    ) -> types.CallToolResult | None:
        return await self.session().call_tool(tool_name, tool_input)

    async def list_prompts(self) -> list[types.Prompt]:
        result = await self.session().list_prompts()
        return result.prompts

    async def get_prompt(self, prompt_name, args: dict[str, str]):
        result = await self.session().get_prompt(prompt_name, args)
        return result.messages

    async def read_resource(self, uri: str) -> Any:
        result = await self.session().read_resource(AnyUrl(uri))
        resource = result.contents[0]

        if isinstance(resource, types.TextResourceContents):
            if resource.mimeType == "application/json":
                return json.loads(resource.text)

            return resource.text

    async def cleanup(self):
        await self._exit_stack.aclose()
        self._session = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

```

### MCP Server Primitives

#### Tools: Model-Controlled

Tools are controlled entirely by Claude. The AI model decides when to call these functions, and the results are used directly by Claude to accomplish tasks.

Use tools when you want to give Claude additional capabilities. For example, if you ask Claude to calculate the square root of 3 using JavaScript, Claude will automatically decide to use a JavaScript execution tool to provide an accurate answer.

#### Resources: App-Controlled

Resources are controlled by your application code. Your app decides when to fetch resource data and how to use it, typically for UI purposes or to add context to conversations.

Use resources when you need to get data into your app. Common examples include:

* Populating autocomplete options in your UI
* Adding context to messages before sending them to Claude
* Displaying lists of available documents or files

#### Prompts: User-Controlled

Prompts are triggered by user actions. Users decide when to run these predefined workflows through UI interactions like button clicks, menu selections, or slash commands.

Use prompts for workflows that users should be able to trigger on demand. These are perfect for:

* Predefined conversation starters
* Common task templates
* Specialized workflows optimized for specific use cases

#### Choosing the Right Primitive

* Need to extend Claude's capabilities? Use tools
* Need data for your app's UI or context? Use resources
* Want to offer predefined workflows to users? Use prompts

---

## Retrieval Augmented Generation

Large language models like Claude are trained on data up to a certain point in time and have no access to your private documents or real-time information. Retrieval-Augmented Generation (RAG) solves this by dynamically fetching relevant information from your own data sources and injecting it into the prompt before Claude generates a response. Instead of retraining the model, you bring the knowledge to it at query time.

A typical RAG system has three core components:

* Document preprocessing and chunking
* A search mechanism to find relevant chunks
* Intelligent selection of which chunks to include in prompts

### Text chunking strategies

* Chunk by a set number of characters

```python
def chunk_by_char(text, chunk_size=150, chunk_overlap=20):
    chunks = []
    start_idx = 0

    while start_idx < len(text):
        end_idx = min(start_idx + chunk_size, len(text))

        chunk_text = text[start_idx:end_idx]
        chunks.append(chunk_text)

        start_idx = (
            end_idx - chunk_overlap if end_idx < len(text) else len(text)
        )

    return chunks
```

* Chunk by sentence

```python
import re


def chunk_by_sentence(text, max_sentences_per_chunk=5, overlap_sentences=1):
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks = []
    start_idx = 0

    while start_idx < len(sentences):
        end_idx = min(start_idx + max_sentences_per_chunk, len(sentences))

        current_chunk = sentences[start_idx:end_idx]
        chunks.append(" ".join(current_chunk))

        start_idx += max_sentences_per_chunk - overlap_sentences

        if start_idx < 0:
            start_idx = 0

    return chunks
```

* Chunk by section

```python
def chunk_by_section(document_text):
    pattern = r"\n## "
    return re.split(pattern, document_text)
```

Remember that chunking is often an iterative process. Start with a simple approach, test it with your specific documents and use cases, then refine based on the results. The "best" chunking strategy is the one that works reliably for your particular data and requirements.

* Consistent document structure: Use structure-based chunking for the cleanest results
* Mixed document types: Sentence-based chunking often works well
* Code or technical content: Chunk by function or class boundaries when possible; character-based is a last resort as it can split code mid-function
* Unknown document formats: Character-based chunking is your safest bet

### Text embeddings | Semantic Search

* **Unlike traditional keyword-based search, semantic search uses text embeddings to understand the actual meaning of both the user's question and each text chunk. This allows the system to find conceptually related content even when the exact words don't match.**

* Embedding Generation

```python
import voyageai

vo = voyageai.Client()

def generate_embedding(text):
    response = vo.embed([text], model="voyage-3")
    return response.embeddings[0]
```

* You feed text into an embedding model
* The model outputs a long list of numbers (the embedding)
* The individual dimension values are not constrained to a fixed range — it is the **cosine similarity** computed between two unit-normalized embeddings that falls between -1 and +1
* These numbers collectively represent different qualities or features of the input text

Embeddings are incredibly powerful because they capture semantic meaning in a way that allows for mathematical comparison between different pieces of text.

### RAG pipeline step by step in a real implementation

#### Step 1: Chunk Your Source Text

For this example, we'll use two simple text sections:

* Section 1: Medical Research - "This year saw significant strides in our understanding of XDR-47, a 'bug' we have not seen before."
* Section 2: Software Engineering - "This division dedicated significant effort to studying various infection vectors in our distributed systems"

#### Step 2: Generate embeddings for each chunk

To make this easier to understand, let's imagine we have a perfect embedding model that always returns exactly two numbers, and we know what each number represents:

* First number: How much the text talks about medicine
* Second number: How much the text talks about software engineering

So our medical research section gets [0.97, 0.34] - very medical, somewhat software-related due to the word "bug". The software engineering section gets [0.30, 0.97] - very software-focused, but "infection vectors" has medical connotations.

* Normalization

Before storing these embeddings, they go through a normalization process that scales each vector to have a magnitude of 1.0. This is typically handled automatically by your embedding API, but it's important to understand it happens.

After normalization, our embeddings become [0.944, 0.331] and [0.295, 0.955]. We can visualize these on a unit circle where both points lie exactly on the circle's edge.

#### Step 3: Create a vector store and add each embedding to it

The normalized embeddings get stored in a vector database - a specialized database optimized for storing, comparing, and searching through long lists of numbers like our embeddings.

#### Step 4: Process User Query and Build the Final Prompt

When a user asks a question like "I'm curious about the company. In particular, what did the software engineering dept do this year?", **we run their query through the same embedding model**.

This query gets embedded as [0.1, 0.89] - low medical score, high software engineering score. After normalization, it becomes [0.112, 0.993].

Now we ask the vector database: "Find the stored embedding that's closest to this user query embedding." The database returns the software engineering section because it's the most similar.

* How does the database determine "closest"?
  * Cosine Similarity - The vector database calculates the cosine of the angle between vectors to measure similarity. This gives us a number between -1 and 1:
    * 1.0 = vectors point in exactly the same direction (very similar)
    * 0.0 = vectors are perpendicular (unrelated)
    * -1.0 = vectors point in opposite directions (very different)

* In our example:
  * User query vs Software Engineering: cosine similarity = 0.983 (very similar!)
  * User query vs Medical Research: cosine similarity = 0.434 (less similar)

* Cosine Distance
  * You'll often see "cosine distance" in vector database documentation. This is simply 1 - cosine similarity, which flips the scale so that smaller numbers mean more similar:
    * 0.0 = very similar
    * 1.0 = perpendicular
    * 2.0 = completely opposite

Finally, we take the user's question and the most relevant text chunk (software engineering section) and combine them into a prompt for Claude:

```bash
"Answer the user's question about the company annual report."

<user_question>
What did the software engineering department do this year?
</user_question>

<report>
## Section 2: Software Engineering
This division dedicated significant effort to studying various infection vectors in our distributed systems
</report>
```

This process happens automatically every time a user submits a query, **allowing Claude to answer questions based on your specific documents rather than just its general training knowledge**.

### A Deep Dive into Implementation Strategies

#### Hybrid Search Strategy

BM25 (Best Match 25) is a popular algorithm for lexical search in RAG pipelines.

This hybrid approach gives you the best of both worlds - the contextual understanding of semantic search combined with the precision of exact term matching from lexical search.

#### Retriever

Both search systems use similar APIs, making it straightforward to query both in parallel and combine their results into a single, more comprehensive result set.

This consistency makes it straightforward to wrap them in a single **Retriever** class.

Vector search returns cosine similarity scores, while BM25 returns relevance scores - you can't simply combine these numbers directly. Instead, we use a technique called **Reciprocal Rank Fusion (RRF)**. This method focuses on the rank position of results rather than their raw scores. The merge logic tracks document ranks across all search results, calculates RRF scores, and returns the top-k documents sorted by their combined scores.

```python
# Retriever implementation

from typing import Any, List, Dict, Tuple, Protocol, Callable, Optional
import random
import string


class SearchIndex(Protocol):
    def add_document(self, document: Dict[str, Any]) -> None: ...

    # Added the 'add_documents' method to avoid rate limiting errors from VoyageAI
    def add_documents(self, documents: List[Dict[str, Any]]) -> None: ...

    def search(
        self, query: Any, k: int = 1
    ) -> List[Tuple[Dict[str, Any], float]]: ...


class Retriever:
    def __init__(
        self,
        *indexes: SearchIndex,
        reranker_fn: Optional[
            Callable[[List[Dict[str, Any]], str, int], List[str]]
        ] = None,
    ):
        if len(indexes) == 0:
            raise ValueError("At least one index must be provided")
        self._indexes = list(indexes)
        self._reranker_fn = reranker_fn

    def add_document(self, document: Dict[str, Any]):
        if "id" not in document:
            document["id"] = "".join(
                random.choices(string.ascii_letters + string.digits, k=4)
            )

        for index in self._indexes:
            index.add_document(document)

    # Added the 'add_documents' method to avoid rate limiting errors from VoyageAI
    def add_documents(self, documents: List[Dict[str, Any]]):
        for index in self._indexes:
            index.add_documents(documents)

    def search(
        self, query_text: str, k: int = 1, k_rrf: int = 60
    ) -> List[Tuple[Dict[str, Any], float]]:
        if not isinstance(query_text, str):
            raise TypeError("Query text must be a string.")
        if k <= 0:
            raise ValueError("k must be a positive integer.")
        if k_rrf < 0:
            raise ValueError("k_rrf must be non-negative.")

        all_results = [
            index.search(query_text, k=k * 5) for index in self._indexes
        ]

        doc_ranks = {}
        for idx, results in enumerate(all_results):
            for rank, (doc, _) in enumerate(results):
                doc_id = id(doc)
                if doc_id not in doc_ranks:
                    doc_ranks[doc_id] = {
                        "doc_obj": doc,
                        "ranks": [float("inf")] * len(self._indexes),
                    }
                doc_ranks[doc_id]["ranks"][idx] = rank + 1

        def calc_rrf_score(ranks: List[float]) -> float:
            return sum(1.0 / (k_rrf + r) for r in ranks if r != float("inf"))

        scored_docs: List[Tuple[Dict[str, Any], float]] = [
            (ranks["doc_obj"], calc_rrf_score(ranks["ranks"]))
            for ranks in doc_ranks.values()
        ]

        filtered_docs = [
            (doc, score) for doc, score in scored_docs if score > 0
        ]
        filtered_docs.sort(key=lambda x: x[1], reverse=True)

        result = filtered_docs[:k]

        if self._reranker_fn is not None:
            docs_only = [doc for doc, _ in result]

            for doc in docs_only:
                if "id" not in doc:
                    doc["id"] = "".join(
                        random.choices(
                            string.ascii_letters + string.digits, k=4
                        )
                    )

            doc_lookup = {doc["id"]: doc for doc in docs_only}
            reranked_ids = self._reranker_fn(docs_only, query_text, k)

            new_result = []
            original_scores = {id(doc): score for doc, score in result}

            for doc_id in reranked_ids:
                if doc_id in doc_lookup:
                    doc = doc_lookup[doc_id]
                    score = original_scores.get(id(doc), 0.0)
                    new_result.append((doc, score))

            result = new_result

        return result
```

#### Reranking results

Re-ranking adds an extra step after your hybrid search process. Instead of just returning the merged results from your vector and BM25 indexes, you pass those results through an LLM for intelligent reordering.

* Run your existing hybrid search (vector + BM25)
* Merge the results as before
* Send the merged results to Claude with a re-ranking prompt
* Get back a reordered list of the most relevant documents
  * If you asked Claude to return the complete text of each relevant document, you'd waste time waiting for it to copy large amounts of text. Instead, assign each text chunk a unique ID ahead of time, then ask Claude to return just those IDs in the preferred order. This makes the re-ranking process much faster while still giving you the reordered results you need.

```python
# Reranker function
def reranker_fn(docs, query_text, k):
    joined_docs = "\n".join(
        [
            f"""
        <document>
        <document_id>{doc["id"]}</document_id>
        <document_content>{doc["content"]}</document_content>
        </document>
        """
            for doc in docs
        ]
    )

    prompt = f"""
    You are about to be given a set of documents, along with an id of each.
    Your task is to select and sort the {k} most relevant documents to answer the user's question.

    Here is the user's question:
    <question>
    {query_text}
    </question>
    
    Here are the documents to select from:
    <documents>
    {joined_docs}
    </documents>

    Respond in the following format:
    ```json
    {{
        "document_ids": str[] # List document ids, {k} elements long, sorted in order of decreasing relevance to the user's query. The most relevant documents should be listed first.
    }}
    ```
    """

    messages = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, "```json")

    result = chat(messages, stop_sequences=["```"])

    # Note: updated to use 'text_from_message' helper fn
    return json.loads(text_from_message(result))["document_ids"]
    
```

You can integrate this into your retriever by passing the re-ranker function as a parameter:

```python
retriever = Retriever(bm25_index, vector_index, reranker_fn=reranker_fn)
```

#### Trade-offs

* Increased latency: You now need to wait for an additional LLM call to complete
* Improved accuracy: The LLM can understand context and intent better than pure similarity scores
* Cost considerations: Each search now requires an LLM API call

#### Contextual retrieval

When you split a document into chunks, each chunk loses its connection to the broader document context.

* Take each individual chunk and the original source document
* Send both to Claude with a specific prompt asking it to add context
* Claude generates a short snippet that "situates" the chunk within the larger document
* Combine this context with the original chunk to create a "contextualized chunk"
* Use the contextualized chunk in your vector and BM25 indexes

```python
def add_context(text_chunk, source_text):
    prompt = f"""
    Write a short and succinct snippet of text to situate this chunk within the 
    overall source document for the purposes of improving search retrieval of the chunk. 

    Here is the original source document:
    <document> 
    {source_text}
    </document> 

    Here is the chunk we want to situate within the whole document:
    <chunk> 
    {text_chunk}
    </chunk>
    
    Answer only with the succinct context and nothing else. 
    """

    messages = []

    add_user_message(messages, prompt)
    result = chat(messages)

    # Note: updated to use 'text_from_message' helper fn
    return text_from_message(result) + "\n" + text_chunk
```

For large documents, you can implement a strategy that selects relevant context chunks:


```python
# Add context to each chunk, then add to the retriever
num_start_chunks = 2
num_prev_chunks = 2

for i, chunk in enumerate(chunks):
    context_parts = []
    
    # Initial set of chunks from the start of the doc
    context_parts.extend(chunks[: min(num_start_chunks, len(chunks))])
    
    # Additional chunks ahead of the current chunk we're contextualizing
    start_idx = max(0, i - num_prev_chunks)
    context_parts.extend(chunks[start_idx:i])
    
    context = "\n".join(context_parts)
    
    contextualized_chunk = add_context(chunk, context)
    retriever.add_document({"content": contextualized_chunk})
```

This technique is most valuable when:

* Your documents have complex internal relationships between sections
* Chunks reference concepts defined elsewhere in the document
* Understanding the document structure is important for accurate retrieval
* You're working with technical documents, reports, or academic papers