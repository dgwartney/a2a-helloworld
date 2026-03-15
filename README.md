# A2A Hello World

A minimal [Agent-to-Agent (A2A)](https://google.github.io/A2A/) protocol example using the `a2a-sdk` Python package. The agent accepts any text message and responds with "Hello World". Both **HTTP+JSON** and **JSON-RPC** transport bindings are supported, selectable at runtime.

## Project Structure

```
├── src/a2a_helloworld/
│   ├── agent.py              # Server entry point (uvicorn)
│   ├── agent_executor.py     # Agent logic (returns "Hello World")
│   ├── client.py             # Interactive chat client (REPL + single-shot)
│   ├── formatter.py          # ANSI terminal formatter for chat output
│   ├── log.py                # Shared logging configuration
│   └── protocol.py           # Shared protocol constants
├── Containerfile             # Container build (UBI8 + uv)
├── pyproject.toml            # Project metadata and dependencies
└── uv.lock                   # Locked dependency versions
```

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager

### Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

## Setup

1. Clone the repository and change into the project directory:

   ```bash
   git clone https://github.com/dgwartney/a2a-helloworld.git
   cd a2a-helloworld
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   uv sync
   ```

   This reads `pyproject.toml` and `uv.lock` to install all required packages including:

   - `a2a-sdk` -- A2A protocol SDK (server, client, types)
   - `httpx` -- Async HTTP client
   - `uvicorn` -- ASGI server
   - `starlette` / `sse-starlette` -- Web framework and Server-Sent Events support
   - `pydantic` -- Data validation

## Configuration

Configuration is resolved with CLI arguments taking precedence over environment variables, which take precedence over built-in defaults.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `A2A_AGENT_URL` | URL advertised in the agent card | `http://localhost:9999` |
| `A2A_PROTOCOL_VERSION` | A2A protocol version (X.Y format) | `1.0` |
| `A2A_PREFERRED_TRANSPORT` | Preferred transport binding | `HTTP+JSON` |

### CLI Arguments

| Argument | Description |
|----------|-------------|
| `--agent-url` | URL advertised in the agent card |
| `--protocol-version` | A2A protocol version in X.Y format |
| `--preferred-transport` | Transport binding: `HTTP+JSON`, `JSONRPC`, or `GRPC` |

## Running

### Start the agent server

```bash
# Default (HTTP+JSON transport, protocol version 1.0)
uv run agent

# With JSON-RPC transport
uv run agent --preferred-transport JSONRPC

# With a specific protocol version
uv run agent --protocol-version 0.3

# With a custom agent URL
uv run agent --agent-url https://my.host

# Using environment variables
A2A_PREFERRED_TRANSPORT=JSONRPC uv run agent
```

At startup the agent prints a configuration summary:

```
============================================================
A2A Hello World Agent
============================================================
  Name:              Hello World Agent
  Version:           1.0.0
  Protocol version:  1.0
  URL:               http://localhost:9999
  Transport:         HTTP+JSON
  Host:              0.0.0.0
  Port:              9999
  Input modes:       text
  Output modes:      text
  Streaming:         False
  Push notifications: False
  Skills:            Returns hello world
============================================================
```

#### HTTP+JSON Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/.well-known/agent-card.json` | Public agent card |
| POST | `/v1/message:send` | Send a message (non-streaming) |
| POST | `/v1/message:stream` | Send a message (streaming via SSE) |
| GET | `/v1/tasks/{id}` | Get task status |
| POST | `/v1/tasks/{id}:cancel` | Cancel a task |

#### JSON-RPC Endpoints

When started with `--preferred-transport JSONRPC`, the agent uses `A2AStarletteApplication` and exposes JSON-RPC methods over a single endpoint.

### Run the client

In a separate terminal:

```bash
# Interactive REPL (default)
uv run client

# Single-shot mode
uv run client --message "Hello"

# Fetch agent card only
uv run client --agent-card-only

# Enable streaming (SSE)
uv run client --streaming

# Override transport
uv run client --transport JSONRPC

# Log to file (keeps terminal clean for chat UI)
uv run client --log-file /tmp/a2a.log --log-level DEBUG
```

The client automatically fetches the agent card from `/.well-known/agent-card.json`, reads the `preferredTransport` field, and creates a client with the matching transport protocol. It supports `HTTP+JSON` and `JSONRPC` transport values as defined by the A2A specification.

#### Client Modes

**Interactive REPL** (default when `--message` is omitted):

```
A2A Chat — connected to Hello World Agent
Type /help for commands, /quit to exit.

You: Hello
Agent: Hello World
You: /quit
Goodbye!
```

REPL commands: `/help`, `/quit`, `/exit`. Press Ctrl+C or Ctrl+D to exit.

**Single-shot** (`--message`): sends one message, prints the formatted response, and exits.

#### Streaming vs Non-Streaming

By default the client uses non-streaming mode, calling the `message:send` endpoint. Pass `--streaming` to use the `message:stream` SSE endpoint instead:

```
You: Hello
Agent: ● typing...
Agent: Hello World
       ✓ done (0.8s)
```

#### Client CLI Arguments

| Argument | Env Variable | Default | Description |
|----------|-------------|---------|-------------|
| `--message` | | _(REPL)_ | Text to send (single-shot mode) |
| `--streaming` / `--no-streaming` | | `False` | Use SSE streaming endpoint |
| `--transport` | `A2A_TRANSPORT` | _(from agent card)_ | Override transport: `HTTP+JSON` or `JSONRPC` |
| `--agent-card-only` | | `False` | Print agent card JSON and exit |
| `--log-level` | `A2A_LOG_LEVEL` | `INFO` | Python logging level |
| `--log-format` | `A2A_LOG_FORMAT` | _(timestamp + level)_ | Python logging format string |
| `--log-file` | `A2A_LOG_FILE` | _(stderr)_ | Log to file instead of stderr |

#### Client Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `A2A_AGENT_URL` | Base URL of the agent to connect to | `http://localhost:9999` |
| `A2A_TRANSPORT` | Transport override | _(from agent card)_ |
| `A2A_LOG_LEVEL` | Logging level | `INFO` |
| `A2A_LOG_FORMAT` | Logging format string | `%(asctime)s %(levelname)s: %(message)s` |
| `A2A_LOG_FILE` | Path to log file | _(stderr)_ |

## Container Build

Build and run using [Podman](https://podman.io/) or Docker:

```bash
podman build -f Containerfile -t helloworld-a2a-server .
podman run -p 9999:9999 helloworld-a2a-server
```

## How It Works

1. **Protocol Constants** (`protocol.py`) -- Shared constants for known protocol versions and supported transport bindings, derived from the `a2a-sdk` `TransportProtocol` enum.

2. **Agent Executor** (`agent_executor.py`) -- Implements the `AgentExecutor` interface. On each request it invokes `HelloWorldAgent.invoke()` which returns `"Hello World"`, then enqueues it as a text message event.

3. **Server** (`agent.py`) -- Selects the server implementation based on the preferred transport: `A2ARESTFastAPIApplication` for HTTP+JSON or `A2AStarletteApplication` for JSON-RPC. Serves the application with uvicorn on port 9999.

4. **Formatter** (`formatter.py`) -- `ChatFormatter` class that renders chat-style output with ANSI escape codes. Handles user messages, agent responses, streaming typing indicators, error display, and the REPL welcome banner. Uses plain ANSI sequences with no external dependencies.

5. **Client** (`client.py`) -- `HelloWorldClient` fetches the agent card and sends messages as an async generator of SDK events. `HelloWorldChat` provides the CLI interface with interactive REPL and single-shot modes, consuming events from the client and formatting output via `ChatFormatter`.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Author

David Gwartney ([david.gwartney@gmail.com](mailto:david.gwartney@gmail.com))

GitHub: [https://github.com/dgwartney/a2a-helloworld](https://github.com/dgwartney/a2a-helloworld)

## Disclaimer

The sample code is for demonstration purposes and illustrates the mechanics of the A2A protocol. When building production applications, treat any agent operating outside of your direct control as a potentially untrusted entity. All data received from an external agent should be handled as untrusted input and properly validated before use.
