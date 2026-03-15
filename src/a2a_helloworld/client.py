"""A2A test client that sends a message to the Hello World agent.

Demonstrates the HTTP+JSON transport binding using the ``ClientFactory``
from the ``a2a-sdk``.  The agent URL is read from the ``A2A_AGENT_URL``
environment variable (defaults to ``http://localhost:9999``).

Usage::

    uv run a2a-client                          # local default
    A2A_AGENT_URL=https://my.host uv run a2a-client  # custom URL
"""

import logging
import os

from dotenv import load_dotenv
import httpx

load_dotenv()

from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.client.helpers import create_text_message_object
from a2a.types import (
    AgentCard,
    Message,
    TransportProtocol,
)
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
    EXTENDED_AGENT_CARD_PATH,
)


async def main() -> None:
    """Run the test client.

    The client performs the following steps:

    1. **Resolve the agent card** — fetches the public agent card from the
       well-known path (``/.well-known/agent-card.json``) so it knows the
       agent's capabilities and preferred transport.
    2. **Create an HTTP+JSON client** — uses ``ClientFactory`` configured with
       ``TransportProtocol.http_json`` to build a client that matches the
       server's advertised transport.
    3. **Send a message** — sends a simple text message and iterates over the
       response events, printing each one as JSON.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    base_url = os.environ.get('A2A_AGENT_URL', 'http://localhost:9999')

    async with httpx.AsyncClient() as httpx_client:
        # -- Step 1: Resolve the agent card -----------------------------------
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )

        agent_card: AgentCard | None = None

        try:
            logger.info(
                f'Attempting to fetch public agent card from: {base_url}{AGENT_CARD_WELL_KNOWN_PATH}')
            agent_card = await resolver.get_agent_card()
            logger.info('Successfully fetched public agent card:')
            logger.info(agent_card.model_dump_json(indent=2, exclude_none=True))
            logger.info(
                '\nUsing PUBLIC agent card for client initialization (default).')

        except Exception as e:
            logger.error(
                f'Critical error fetching public agent card: {e}', exc_info=True
            )
            raise RuntimeError(
                'Failed to fetch the public agent card. Cannot continue.'
            ) from e

        # -- Step 2: Create HTTP+JSON client ----------------------------------
        config = ClientConfig(
            supported_transports=[TransportProtocol.http_json],
            httpx_client=httpx_client,
        )
        factory = ClientFactory(config)
        client = factory.create(agent_card)
        logger.info('HTTP+JSON client initialized.')

        # -- Step 3: Send a message and print the response --------------------
        message = create_text_message_object(
            content='how much is 10 USD in INR?')

        logger.info('Sending message...')
        async for event in client.send_message(message):
            if isinstance(event, Message):
                # The agent responded with a direct Message (no task wrapper).
                print(event.model_dump(mode='json', exclude_none=True))
            else:
                # The response is a (Task, UpdateEvent | None) tuple.
                task, update = event
                print(task.model_dump(mode='json', exclude_none=True))


def cli() -> None:
    """CLI entry point registered as ``a2a-client`` in pyproject.toml."""
    import asyncio

    asyncio.run(main())


if __name__ == '__main__':
    cli()
