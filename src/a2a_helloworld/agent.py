"""A2A agent server entry point.

Builds a FastAPI application that serves the Hello World agent over the
HTTP+JSON transport binding and runs it with uvicorn.

The agent card URL is read from the ``A2A_AGENT_URL`` environment variable
(defaults to ``http://localhost:9999``).

Usage::

    uv run a2a-agent                          # local default
    A2A_AGENT_URL=https://my.host uv run a2a-agent  # custom URL
"""

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
        url=os.environ.get('A2A_AGENT_URL', 'http://localhost:9999'),
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False, stateTransitionHistory=False, extendedAgentCard=False),
        skills=[skill],
        preferred_transport='HTTP+JSON',
        protocolVersion = "1.0"
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

    # Log all registered routes so operators can verify the endpoint layout.
    for route in app.routes:
        print(
            f"  {getattr(route, 'methods', 'N/A')} {getattr(route, 'path', 'N/A')}")

    uvicorn.run(app, host='0.0.0.0', port=9999, log_level="debug")


if __name__ == '__main__':
    main()
