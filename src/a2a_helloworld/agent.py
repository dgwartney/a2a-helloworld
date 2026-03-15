import os

import uvicorn

from a2a.server.apps.rest.fastapi_app import A2ARESTFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from a2a_helloworld.agent_executor import HelloWorldAgentExecutor


def main():
    skill = AgentSkill(
        id='hello_world',
        name='Returns hello world',
        description='just returns hello world',
        tags=['hello world'],
        examples=['hi', 'hello world'],
    )

    extended_skill = AgentSkill(
        id='super_hello_world',
        name='Returns a SUPER Hello World',
        description='A more enthusiastic greeting, only for authenticated users.',
        tags=['hello world', 'super', 'extended'],
        examples=['super hi', 'give me a super hello'],
    )

    public_agent_card = AgentCard(
        name='Hello World Agent',
        description='Just a hello world agent',
        url=os.environ.get('A2A_AGENT_URL', 'http://localhost:9999'),
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],  # Only the basic skill for the public card
        supports_authenticated_extended_card=False,
        preferred_transport='HTTP+JSON',
    )

    request_handler = DefaultRequestHandler(
        agent_executor=HelloWorldAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2ARESTFastAPIApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    app = server.build()

    for route in app.routes:
        print(
            f"  {getattr(route, 'methods', 'N/A')} {getattr(route, 'path', 'N/A')}")

    uvicorn.run(app, host='0.0.0.0', port=9999, log_level="debug")


if __name__ == '__main__':
    main()
