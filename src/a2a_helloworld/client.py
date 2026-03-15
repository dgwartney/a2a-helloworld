"""A2A client with interactive chat REPL and single-shot modes.

Fetches the agent card and selects the transport binding (HTTP+JSON or
JSON-RPC) based on the agent's ``preferred_transport`` field.

The agent URL is read from the ``A2A_AGENT_URL`` environment variable
(defaults to ``http://localhost:9999``).

Usage::

    uv run client                              # interactive REPL
    uv run client --message "Hello"            # single-shot mode
    uv run client --agent-card-only            # fetch agent card only
    A2A_AGENT_URL=https://my.host uv run client  # custom URL
"""

import argparse
import asyncio
import logging
import os
import time
from collections.abc import AsyncGenerator
from typing import Union

from dotenv import load_dotenv
import httpx

load_dotenv()

from a2a_helloworld.formatter import ChatFormatter
from a2a_helloworld.log import DEFAULT_LOG_FORMAT

from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.client.helpers import create_text_message_object
from a2a.types import (
    AgentCard,
    Message,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatusUpdateEvent,
    TransportProtocol,
)
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
    EXTENDED_AGENT_CARD_PATH,
)
from a2a_helloworld.protocol import HTTP_TRANSPORTS, TRANSPORT_HTTP_JSON, TRANSPORT_JSONRPC


# Sentinel to detect whether --message was explicitly passed
_MESSAGE_SENTINEL = object()


class HelloWorldClient:
    """Client for communicating with an A2A Hello World agent."""

    def __init__(
        self,
        base_url: str,
        streaming: bool = True,
        transport: str | None = None,
    ) -> None:
        self.base_url = base_url
        self.streaming = streaming
        self.transport_override = transport
        self.logger = logging.getLogger(__name__)
        self.agent_card: AgentCard | None = None

    async def get_agent_card(self) -> AgentCard:
        """Fetch and cache the agent card."""
        if self.agent_card is not None:
            return self.agent_card

        async with httpx.AsyncClient() as httpx_client:
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=self.base_url,
            )
            try:
                self.logger.debug(
                    f'Attempting to fetch public agent card from: {self.base_url}{AGENT_CARD_WELL_KNOWN_PATH}')
                self.agent_card = await resolver.get_agent_card()
                self.logger.debug('Successfully fetched public agent card:')
                self.logger.debug(self.agent_card.model_dump_json(indent=2, exclude_none=True))
                self.logger.debug(
                    '\nUsing PUBLIC agent card for client initialization (default).')
            except Exception as e:
                self.logger.error(
                    f'Critical error fetching public agent card: {e}', exc_info=True
                )
                raise RuntimeError(
                    'Failed to fetch the public agent card. Cannot continue.'
                ) from e

        return self.agent_card

    async def send_message(self, text: str) -> AsyncGenerator:
        """Send a text message, yielding response events.

        Yields either ``Message`` objects (non-streaming) or
        ``(Task, update)`` tuples (streaming) for the caller to display.

        Args:
            text: The text message to send to the agent.

        Yields:
            SDK event objects from the agent response.
        """
        agent_card = await self.get_agent_card()

        transport_map = {
            TRANSPORT_HTTP_JSON.value: TRANSPORT_HTTP_JSON,
            TRANSPORT_JSONRPC.value: TRANSPORT_JSONRPC,
        }
        selected = self.transport_override or agent_card.preferred_transport
        transport_protocol = transport_map.get(selected)
        if transport_protocol is None:
            raise RuntimeError(
                f"Unsupported transport '{selected}'. "
                f"Supported: {', '.join(transport_map)}"
            )

        async with httpx.AsyncClient() as httpx_client:
            config = ClientConfig(
                streaming=self.streaming,
                supported_transports=[transport_protocol],
                httpx_client=httpx_client,
            )
            factory = ClientFactory(config)
            client = factory.create(agent_card)
            self.logger.debug(f'{selected} client initialized.')

            message = create_text_message_object(content=text)

            self.logger.debug(f'Sending message (streaming={self.streaming})...')
            async for event in client.send_message(message):
                yield event


class HelloWorldChat:
    """Interactive chat interface for the A2A Hello World agent.

    Supports two modes:
    - **REPL mode** (default): interactive loop where you type messages
      and see formatted agent responses.
    - **Single-shot mode** (``--message``): send one message, display
      the response, and exit.
    """

    COMMANDS = {
        '/quit': 'Exit the chat',
        '/exit': 'Exit the chat',
        '/help': 'Show available commands',
    }

    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(description='A2A Hello World chat client')
        self.formatter = ChatFormatter()
        self.client: HelloWorldClient | None = None
        self._add_arguments()

    def _add_arguments(self) -> None:
        """Define all CLI arguments."""
        self.parser.add_argument(
            '--agent-card-only',
            action='store_true',
            help='Fetch and print the agent card, then exit',
        )
        self.parser.add_argument(
            '--message',
            default=_MESSAGE_SENTINEL,
            help='Text message to send (single-shot mode). Omit for interactive REPL (env: A2A_MESSAGE)',
        )
        self.parser.add_argument(
            '--transport',
            choices=[t.value for t in HTTP_TRANSPORTS],
            default=os.environ.get('A2A_TRANSPORT'),
            help='Transport to use; overrides agent card preference (env: A2A_TRANSPORT)',
        )
        self.parser.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default=os.environ.get('A2A_LOG_LEVEL', 'INFO'),
            help='Python logging level (env: A2A_LOG_LEVEL, default: %(default)s)',
        )
        self.parser.add_argument(
            '--log-format',
            default=os.environ.get('A2A_LOG_FORMAT', DEFAULT_LOG_FORMAT),
            help='Python logging format string (env: A2A_LOG_FORMAT, default: %(default)s)',
        )
        self.parser.add_argument(
            '--log-file',
            default=os.environ.get('A2A_LOG_FILE'),
            help='Path to log file; when set, logs go to this file instead of stderr (env: A2A_LOG_FILE)',
        )
        self.parser.add_argument(
            '--streaming',
            action=argparse.BooleanOptionalAction,
            default=False,
            help='Use streaming mode (default: False, use --streaming to enable)',
        )

    def parse(self) -> argparse.Namespace:
        """Parse command-line arguments."""
        return self.parser.parse_args()

    def configure_logging(self, args: argparse.Namespace) -> None:
        """Configure logging from parsed arguments.

        When ``--log-file`` is provided, log output goes to the specified
        file instead of stderr, keeping the terminal clean for the chat UI.
        """
        handlers: list[logging.Handler] = []
        if args.log_file:
            handlers.append(logging.FileHandler(args.log_file))
        else:
            handlers.append(logging.StreamHandler())
        logging.basicConfig(
            level=getattr(logging, args.log_level),
            format=args.log_format,
            handlers=handlers,
        )

    async def _display_response(self, text: str) -> None:
        """Send a message and display the formatted response.

        Handles both streaming and non-streaming response events from
        the agent, formatting them via :attr:`formatter`.

        Args:
            text: The text message to send.
        """
        start_time = time.monotonic()
        async for event in self.client.send_message(text):
            if isinstance(event, Message):
                self.formatter.agent_response(
                    self.formatter.extract_text(event.parts)
                )
            else:
                task, update = event
                if isinstance(update, TaskStatusUpdateEvent):
                    if update.status.state == TaskState.working:
                        self.formatter.streaming_typing()
                    elif update.status.state == TaskState.completed:
                        elapsed = time.monotonic() - start_time
                        self.formatter.streaming_done(elapsed)
                elif isinstance(update, TaskArtifactUpdateEvent):
                    response_text = self.formatter.extract_text(
                        update.artifact.parts
                    )
                    self.formatter.streaming_response(response_text)

    async def _run_single_shot(self, text: str) -> None:
        """Send one message and display the response.

        Args:
            text: The text message to send.
        """
        self.formatter.user_message(text)
        await self._display_response(text)

    async def _run_repl(self) -> None:
        """Run the interactive chat REPL."""
        loop = asyncio.get_event_loop()

        agent_card = await self.client.get_agent_card()
        agent_name = agent_card.name or 'Agent'
        self.formatter.banner(agent_name)

        while True:
            try:
                user_input = await loop.run_in_executor(
                    None, lambda: input(self.formatter.prompt())
                )
            except (EOFError, KeyboardInterrupt):
                print()
                self.formatter.goodbye()
                break

            text = user_input.strip()
            if not text:
                continue

            if text.startswith('/'):
                cmd = text.lower()
                if cmd in ('/quit', '/exit'):
                    self.formatter.goodbye()
                    break
                elif cmd == '/help':
                    self.formatter.help(self.COMMANDS)
                    continue
                else:
                    self.formatter.error(
                        f'Unknown command: {text}. Type /help for commands.'
                    )
                    continue

            try:
                await self._display_response(text)
            except Exception as e:
                self.formatter.error(f'Error: {e}')

    async def run(self) -> None:
        """Parse arguments, configure logging, and execute the client."""
        args = self.parse()
        self.configure_logging(args)

        base_url = os.environ.get('A2A_AGENT_URL', 'http://localhost:9999')

        self.client = HelloWorldClient(
            base_url=base_url,
            streaming=args.streaming,
            transport=args.transport,
        )

        if args.agent_card_only:
            agent_card = await self.client.get_agent_card()
            print(agent_card.model_dump_json(indent=2, exclude_none=True))
            return

        if args.message is not _MESSAGE_SENTINEL:
            await self._run_single_shot(args.message)
        else:
            await self._run_repl()


def cli() -> None:
    """CLI entry point registered as ``client`` in pyproject.toml."""
    asyncio.run(HelloWorldChat().run())


if __name__ == '__main__':
    cli()
