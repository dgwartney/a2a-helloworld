"""A2A agent server entry point.

Builds an application that serves the Hello World agent over both HTTP-based
transport bindings (HTTP+JSON and JSON-RPC) simultaneously on a single port
and runs it with uvicorn.

Configuration is resolved with CLI arguments taking precedence over
environment variables, which take precedence over built-in defaults.

Environment variables::

    A2A_AGENT_URL          Agent card URL (default: http://localhost:9999)
    A2A_PROTOCOL_VERSION   Protocol version in X.Y format (default: 1.0)
    A2A_PREFERRED_TRANSPORT  Preferred transport binding (default: HTTP+JSON)

Usage::

    uv run agent                                          # local default
    uv run agent --protocol-version 0.3                    # specific version
    uv run agent --agent-url https://my.host               # custom URL
    uv run agent --preferred-transport JSONRPC              # custom transport
    A2A_AGENT_URL=https://my.host uv run agent            # URL via env var
    A2A_PROTOCOL_VERSION=0.3 uv run agent                 # version via env var
    A2A_PREFERRED_TRANSPORT=JSONRPC uv run agent            # transport via env var
"""

import argparse
import logging
import os

from dotenv import load_dotenv
import uvicorn

load_dotenv()

from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication
from a2a.server.apps.rest.fastapi_app import A2ARESTFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)
from starlette.routing import Mount

AGENT_NAME = 'Hello World Agent'
AGENT_DESCRIPTION = 'Just a hello world agent'
AGENT_VERSION = '1.0.0'
AGENT_INPUT_MODES = ['text']
AGENT_OUTPUT_MODES = ['text']

from a2a_helloworld.agent_executor import HelloWorldAgentExecutor
from a2a_helloworld.protocol import (
    HTTP_TRANSPORTS,
    KNOWN_A2A_PROTOCOL_VERSIONS,
    TRANSPORT_HTTP_JSON,
    TRANSPORT_JSONRPC,
)


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
        3. Build the application via ``A2ARESTFastAPIApplication`` (HTTP+JSON)
           or ``A2AStarletteApplication`` (JSON-RPC).
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
        choices=[t.value for t in HTTP_TRANSPORTS],
        default=os.environ.get('A2A_PREFERRED_TRANSPORT', TRANSPORT_HTTP_JSON.value),
        help="Preferred transport binding advertised in the agent card (env: A2A_PREFERRED_TRANSPORT, default: %(default)s)",
    )
    parser.add_argument(
        "--rest-prefix",
        default=os.environ.get('A2A_REST_PREFIX', ''),
        help="Path prefix for HTTP+JSON REST routes, e.g. /api (env: A2A_REST_PREFIX, default: none)",
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
    #
    # Determine the non-preferred transport so both can be listed.
    other_transport = (
        TRANSPORT_JSONRPC.value
        if args.preferred_transport == TRANSPORT_HTTP_JSON.value
        else TRANSPORT_HTTP_JSON.value
    )

    rest_url = f'{args.agent_url}{args.rest_prefix}'
    jsonrpc_url = args.agent_url

    # Build interface list with preferred transport first.
    interface_urls = {
        TRANSPORT_HTTP_JSON.value: rest_url,
        TRANSPORT_JSONRPC.value: jsonrpc_url,
    }

    public_agent_card = AgentCard(
        name=AGENT_NAME,
        description=AGENT_DESCRIPTION,
        url=args.agent_url,
        version=AGENT_VERSION,
        default_input_modes=AGENT_INPUT_MODES,
        default_output_modes=AGENT_OUTPUT_MODES,
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False, stateTransitionHistory=False, extendedAgentCard=False),
        skills=[skill],
        preferred_transport=args.preferred_transport,
        protocolVersion=args.protocol_version,
        additional_interfaces=[
            AgentInterface(transport=args.preferred_transport, url=interface_urls[args.preferred_transport]),
            AgentInterface(transport=other_transport, url=interface_urls[other_transport]),
        ],
    )

    # -- Request handler & server ---------------------------------------------
    request_handler = DefaultRequestHandler(
        agent_executor=HelloWorldAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # Build both transport apps and combine them into a single ASGI app.
    # The JSON-RPC Starlette app serves as the outer app (owns the agent card
    # at /.well-known/agent-card.json and POST /).  The REST FastAPI app is
    # mounted inside it, with its own agent card route suppressed to avoid a
    # duplicate.
    jsonrpc_server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )
    rest_server = A2ARESTFastAPIApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    app = jsonrpc_server.build()
    rest_app = rest_server.build(agent_card_url='/--skip--/agent-card.json', rpc_url=args.rest_prefix)
    app.routes.append(Mount('', app=rest_app))

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
    print(f"  Transport:         {public_agent_card.preferred_transport} (preferred)")
    print(f"  Also serving:      {other_transport}")
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
