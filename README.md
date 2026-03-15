# A2A Hello World

A minimal [Agent-to-Agent (A2A)](https://google.github.io/A2A/) protocol example using the `a2a-sdk` Python package. The agent accepts any text message and responds with "Hello World". Both **HTTP+JSON** and **JSON-RPC** transport bindings are supported, selectable at runtime.

## Project Structure

```
├── src/a2a_helloworld/
│   ├── agent.py              # Server entry point (uvicorn)
│   ├── agent_executor.py     # Agent logic (returns "Hello World")
│   ├── client.py             # Test client (auto-selects transport)
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

### Run the test client

In a separate terminal:

```bash
uv run client
```

The client automatically:
1. Fetches the agent card from the well-known path (`/.well-known/agent-card.json`)
2. Reads the `preferredTransport` field from the agent card
3. Creates a client with the matching transport protocol
4. Sends a message and prints the response

The client supports `HTTP+JSON` and `JSONRPC` transport values as defined by the A2A specification.

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

4. **Client** (`client.py`) -- Uses `A2ACardResolver` to fetch the agent card, reads the `preferredTransport` field, and creates a client via `ClientFactory` with the matching `TransportProtocol`. Messages are sent as `Message` objects and responses are consumed as an async iterator of events.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Author

David Gwartney ([david.gwartney@gmail.com](mailto:david.gwartney@gmail.com))

GitHub: [https://github.com/dgwartney/a2a-helloworld](https://github.com/dgwartney/a2a-helloworld)

## Disclaimer

The sample code is for demonstration purposes and illustrates the mechanics of the A2A protocol. When building production applications, treat any agent operating outside of your direct control as a potentially untrusted entity. All data received from an external agent should be handled as untrusted input and properly validated before use.
