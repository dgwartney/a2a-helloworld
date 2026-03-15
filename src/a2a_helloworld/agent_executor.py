"""Agent executor that bridges the A2A request handler with the HelloWorldAgent.

This module contains two classes:

- ``HelloWorldAgent`` — the core agent logic (returns a static greeting).
- ``HelloWorldAgentExecutor`` — the A2A ``AgentExecutor`` implementation that
  the ``DefaultRequestHandler`` delegates to when a message arrives.
"""

import asyncio

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import TaskState, TaskStatus, TaskStatusUpdateEvent
from a2a.utils import new_agent_text_message


class HelloWorldAgent:
    """Minimal agent that always responds with a fixed greeting.

    This class is intentionally simple — it contains no state, no model calls,
    and no tool use.  It exists to demonstrate the smallest possible agent
    behind the A2A protocol.
    """

    async def invoke(self) -> str:
        """Return the greeting text.

        Returns:
            The string ``"Hello World"``.
        """
        return 'Hello World'


class HelloWorldAgentExecutor(AgentExecutor):
    """A2A executor that runs :class:`HelloWorldAgent` for every request.

    The ``DefaultRequestHandler`` calls :meth:`execute` once per incoming
    message.  This executor invokes the underlying agent and enqueues the
    result as a text message event so it is returned to the caller.
    """

    def __init__(self, streaming: bool = False) -> None:
        """Create the executor and its internal :class:`HelloWorldAgent`.

        Args:
            streaming: When True, emit a "working" status update before the
                final message so streaming clients see incremental progress.
        """
        self.agent = HelloWorldAgent()
        self.streaming = streaming

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Handle an incoming A2A message.

        Invokes the :class:`HelloWorldAgent` and places the text result onto
        the *event_queue* as an agent text message.  The request handler then
        serialises this event into the HTTP+JSON response (or SSE stream).

        Args:
            context: Metadata about the current request (task id, message, etc.).
            event_queue: Queue used to emit response events back to the caller.
        """
        if self.streaming:
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    taskId=context.task_id,
                    contextId=context.context_id,
                    status=TaskStatus(state=TaskState.working),
                    final=False,
                )
            )
            await asyncio.sleep(1)  # make streaming visually obvious

        result = await self.agent.invoke()
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Attempt to cancel a running request.

        This agent completes immediately, so cancellation is not meaningful.

        Args:
            context: Metadata about the request to cancel.
            event_queue: Queue used to emit cancellation events.

        Raises:
            Exception: Always, because cancellation is not supported.
        """
        raise Exception('cancel not supported')
