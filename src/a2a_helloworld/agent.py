"""A2A agent server entry point.

Builds a FastAPI application that serves the Hello World agent over the
HTTP+JSON transport binding and runs it with uvicorn.

Configuration is resolved with CLI arguments taking precedence over
environment variables, which take precedence over built-in defaults.

Environment variables::

    A2A_AGENT_URL          Agent card URL (default: http://localhost:9999)
    A2A_PROTOCOL_VERSION   Protocol version in X.Y format (default: 1.0)
    A2A_PREFERRED_TRANSPORT  Preferred transport binding (default: HTTP+JSON)

Usage::

    uv run a2a-agent                                          # local default
    uv run a2a-agent --protocol-version 0.3                    # specific version
    uv run a2a-agent --agent-url https://my.host               # custom URL
    uv run a2a-agent --preferred-transport gRPC                # custom transport
    A2A_AGENT_URL=https://my.host uv run a2a-agent            # URL via env var
    A2A_PROTOCOL_VERSION=0.3 uv run a2a-agent                 # version via env var
    A2A_PREFERRED_TRANSPORT=gRPC uv run a2a-agent              # transport via env var
"""

import argparse
import logging
import os

from dotenv import load_dotenv
import uvicorn

load_dotenv()

from a2a.server.apps.rest.fastapi_app import A2ARESTFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from a2a_helloworld.agent_executor import HelloWorldAgentExecutor

KNOWN_A2A_PROTOCOL_VERSIONS = {'0.1', '0.2', '0.3', '1.0'}
SUPPORTED_TRANSPORTS = ['HTTP+JSON', 'gRPC', 'JSON-RPC']


def _validate_protocol_version(value: str) -> str:
    """Validate that the protocol version is in X.Y format (not X.Y.Z).

    Raises argparse.ArgumentTypeError if the format is invalid.
    Logs a warning if the version is valid but not a known release.
    """
    parts = value.split('.')
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        raise argparse.ArgumentTypeError(
            f"invalid version '{value}': must be in X.Y format (e.g. 1.0, 0.3)"
        )
    if value not in KNOWN_A2A_PROTOCOL_VERSIONS:
        logging.warning(
            f"A2A protocol version '{value}' is not a known release "
            f"(known: {', '.join(sorted(KNOWN_A2A_PROTOCOL_VERSIONS))}). "
            f"Proceeding anyway."
        )
    return value


def main() -> None:
    """Configure and start the A2A agent server.

    Steps:
        1. Define the agent's skills and public agent card.
        2. Create a ``DefaultRequestHandler`` backed by
           :class:`~a2a_helloworld.agent_executor.HelloWorldAgentExecutor`
           and an in-memory task store.
        3. Build a FastAPI application via ``A2ARESTFastAPIApplication``.
        4. Print registered routes for debugging, then start uvicorn on
           ``0.0.0.0:9999``.
    """
    parser = argparse.ArgumentParser(
        description="A2A Hello World agent server",
    )
    parser.add_argument(
        "--agent-url",
        default=os.environ.get('A2A_AGENT_URL', 'http://localhost:9999'),
        help="URL advertised in the agent card (env: A2A_AGENT_URL, default: %(default)s)",
    )
    parser.add_argument(
        "--protocol-version",
        type=_validate_protocol_version,
        default=os.environ.get('A2A_PROTOCOL_VERSION', '1.0'),
        help="A2A protocol version advertised in the agent card in X.Y format (env: A2A_PROTOCOL_VERSION, default: %(default)s)",
    )
    parser.add_argument(
        "--preferred-transport",
        choices=SUPPORTED_TRANSPORTS,
        default=os.environ.get('A2A_PREFERRED_TRANSPORT', 'HTTP+JSON'),
        help="Preferred transport binding advertised in the agent card (env: A2A_PREFERRED_TRANSPORT, default: %(default)s)",
    )
    args = parser.parse_args()

    # -- Skills ---------------------------------------------------------------
    skill = AgentSkill(
        id='hello_world',
        name='Returns hello world',
        description='just returns hello world',
        tags=['hello world'],
        examples=['hi', 'hello world'],
    )

    # -- Agent Card -----------------------------------------------------------
    # The URL advertised in the card tells clients where to send requests.
    # It must *not* include the ``/v1`` prefix — the REST transport adds that
    # automatically to every endpoint path.
    public_agent_card = AgentCard(
        name='Hello World Agent',
        description='Just a hello world agent',
        url=args.agent_url,
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False, stateTransitionHistory=False, extendedAgentCard=False),
        skills=[skill],
        preferred_transport=args.preferred_transport,
        protocolVersion=args.protocol_version,
    )

    # -- Request handler & server ---------------------------------------------
    request_handler = DefaultRequestHandler(
        agent_executor=HelloWorldAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2ARESTFastAPIApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    app = server.build()

    # -- Startup configuration summary ----------------------------------------
    host = '0.0.0.0'
    port = 9999
    print("=" * 60)
    print("A2A Hello World Agent")
    print("=" * 60)
    print(f"  Name:              {public_agent_card.name}")
    print(f"  Version:           {public_agent_card.version}")
    print(f"  Protocol version:  {public_agent_card.protocol_version}")
    print(f"  URL:               {public_agent_card.url}")
    print(f"  Transport:         {public_agent_card.preferred_transport}")
    print(f"  Host:              {host}")
    print(f"  Port:              {port}")
    print(f"  Input modes:       {', '.join(public_agent_card.default_input_modes)}")
    print(f"  Output modes:      {', '.join(public_agent_card.default_output_modes)}")
    print(f"  Streaming:         {public_agent_card.capabilities.streaming}")
    print(f"  Push notifications:{' '}{public_agent_card.capabilities.push_notifications}")
    print(f"  Skills:            {', '.join(s.name for s in public_agent_card.skills)}")
    print("=" * 60)

    # Log all registered routes so operators can verify the endpoint layout.
    for route in app.routes:
        print(
            f"  {getattr(route, 'methods', 'N/A')} {getattr(route, 'path', 'N/A')}")

    uvicorn.run(app, host=host, port=port, log_level="debug")


if __name__ == '__main__':
    main()
