import logging

import httpx

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
    # Configure logging to show INFO level messages
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    base_url = 'http://localhost:9999'

    async with httpx.AsyncClient() as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )

        # Fetch Public Agent Card
        agentCard: AgentCard | None = None

        try:
            logger.info(
                f'Attempting to fetch public agent card from: {base_url}{AGENT_CARD_WELL_KNOWN_PATH}')
            agentCard = await resolver.get_agent_card()
            logger.info('Successfully fetched public agent card:')
            logger.info(agentCard.model_dump_json(indent=2, exclude_none=True))
            logger.info(
                '\nUsing PUBLIC agent card for client initialization (default).')

        except Exception as e:
            logger.error(
                f'Critical error fetching public agent card: {e}', exc_info=True
            )
            raise RuntimeError(
                'Failed to fetch the public agent card. Cannot continue.'
            ) from e

        # Create HTTP+JSON client via ClientFactory
        config = ClientConfig(
            supported_transports=[TransportProtocol.http_json],
            httpx_client=httpx_client,
        )
        factory = ClientFactory(config)
        client = factory.create(agentCard)
        logger.info('HTTP+JSON client initialized.')

        # Send a message
        message = create_text_message_object(
            content='how much is 10 USD in INR?')

        logger.info('Sending message...')
        async for event in client.send_message(message):
            if isinstance(event, Message):
                print(event.model_dump(mode='json', exclude_none=True))
            else:
                task, update = event
                print(task.model_dump(mode='json', exclude_none=True))


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
