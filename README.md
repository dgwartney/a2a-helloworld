# A2A Hello World

A minimal [Agent-to-Agent (A2A)](https://google.github.io/A2A/) protocol example using the `a2a-sdk` Python package. The agent accepts any text message and responds with "Hello World". Both the server and client use the **HTTP+JSON** transport binding.

## Project Structure

```
├── src/a2a_helloworld/
│   ├── agent.py              # Server entry point (FastAPI + uvicorn)
│   ├── agent_executor.py     # Agent logic (returns "Hello World")
│   └── client.py             # Test client using HTTP+JSON transport
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
   git clone <repo-url>
   cd a2a-helloworld
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   uv sync
   ```

   This reads `pyproject.toml` and `uv.lock` to install all required packages including:

   - `a2a-sdk` — A2A protocol SDK (server, client, types)
   - `httpx` — Async HTTP client
   - `uvicorn` — ASGI server
   - `starlette` / `sse-starlette` — Web framework and Server-Sent Events support
   - `pydantic` — Data validation

## Running

### Start the agent server

```bash
uv run a2a-agent
```

The server starts on `http://0.0.0.0:9999` and exposes the following REST endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/.well-known/a2a/card.json` | Public agent card |
| POST | `/v1/message:send` | Send a message (non-streaming) |
| POST | `/v1/message:stream` | Send a message (streaming via SSE) |
| GET | `/v1/tasks/{id}` | Get task status |
| POST | `/v1/tasks/{id}:cancel` | Cancel a task |

### Run the test client

In a separate terminal:

```bash
uv run a2a-client
```

The client fetches the agent card from the well-known path, creates an HTTP+JSON client via `ClientFactory`, sends a message, and prints the response.

## Container Build

Build and run using [Podman](https://podman.io/) or Docker:

```bash
podman build -f Containerfile -t helloworld-a2a-server .
podman run -p 9999:9999 helloworld-a2a-server
```

## How It Works

1. **Agent Executor** (`agent_executor.py`) — Implements the `AgentExecutor` interface. On each request it invokes `HelloWorldAgent.invoke()` which returns `"Hello World"`, then enqueues it as a text message event.

2. **Server** (`agent.py`) — Builds an `A2ARESTFastAPIApplication` with the agent card and request handler, then serves it with uvicorn on port 9999. The agent card advertises `HTTP+JSON` as the preferred transport.

3. **Client** (`client.py`) — Uses `A2ACardResolver` to fetch the agent card, then creates a client via `ClientFactory` configured with `TransportProtocol.http_json`. Messages are sent as `Message` objects and responses are consumed as an async iterator of events.

## Disclaimer

The sample code is for demonstration purposes and illustrates the mechanics of the A2A protocol. When building production applications, treat any agent operating outside of your direct control as a potentially untrusted entity. All data received from an external agent should be handled as untrusted input and properly validated before use.
