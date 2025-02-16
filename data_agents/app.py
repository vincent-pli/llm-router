from autogen_ext.models.openai import AzureOpenAIChatCompletionClient, OpenAIChatCompletionClient
import asyncio
from rich.console import Console
from autogen_core.tools import FunctionTool, Tool
from autogen_core.tool_agent import ToolAgent
from typing import List, Any, AsyncGenerator, Optional, Callable
from autogen_core import (
    SingleThreadedAgentRuntime,
    TopicId,
    TypeSubscription,
    AgentId,
    CancellationToken,
)
from autogen_core.models import (
    UserMessage,
)
from data_agents.messages import GroupChatMessage, TerminateMessage
from data_agents.utils.tools.hr import hr_rules_and_regulations, employee_info
from data_agents.utils.tools.generic import weather


from data_agents.user_agent import UserAgent
from data_agents.groupchat_manager import GroupChatManager
from data_agents.agents.hr_agent import HRAssistant
from data_agents.agents.generic_assitant_agent import GenericAssistant
import uuid
from autogen_core.base.intervention import DefaultInterventionHandler
from data_agents.persistence.localfile import LocalFilePersistence
import os
import pathlib
from data_agents.constants import WORKSPACE_DEFAULT


class TerminationHandler(DefaultInterventionHandler):
    def __init__(self):
        self.terminateMessage: TerminateMessage | None = None

    async def on_publish(self, message: Any, *, sender: AgentId | None) -> Any:
        if isinstance(message, TerminateMessage):
            self.terminateMessage = message
        return message

    @property
    def is_terminated(self) -> bool:
        return self.terminateMessage is not None

    @property
    def termination_msg(self) -> str | None:
        if self.terminateMessage is None:
            return None
        return self.terminateMessage.content


async def run_stream(
        user_id: str,
        user_name: str,
        user_token: str,
        task: str,
        cancellation_token: CancellationToken | None = None,
        input_func: Optional[Callable] = None
) -> AsyncGenerator[UserMessage | TerminateMessage, None]:

    state_persister = LocalFilePersistence()
    user_info = user_id + "~" + user_name + "~" + user_token
    session_id = state_persister.get_uuid(user_info)
    if not session_id:
        session_id = user_info + "~" + str(uuid.uuid4())

    # create temp workspace
    base_dir = pathlib.Path().resolve()
    workspace_path = os.path.join(base_dir, WORKSPACE_DEFAULT, session_id)
    if not os.path.exists(workspace_path):
        os.makedirs(workspace_path)

    output_message_queue: asyncio.Queue[UserMessage | None] = asyncio.Queue()
    termination_handler = TerminationHandler()
    # Create an local embedded runtime.
    runtime = SingleThreadedAgentRuntime(
        intervention_handlers=[termination_handler])

    group_chat_topic_type = "group_chat"
    user_topic_type = "User"
    hr_onpremise_topic_type = "HR_onpre"
    hr_public_topic_type = "HR_public"
    generic_assistant_onpremise_topic_type = "generic_assistant_onpre"
    generic_assistant_public_topic_type = "generic_assistant_public"

    user_description = "User for providing final approval or further requirement, if question already be resolved, pick the role for final approve or further question"
    hr_onpremise_description = "A agent to answer HR-related questions, including general rules and regulations, as well as potentially sensitive employee information. label: on-premise"
    hr_public_description = "A agent to answer HR-related questions, including general rules and regulations, as well as potentially sensitive employee information. label: public"
    generic_assistant_onpremise_description = "Assistant for Handling General Inquiries. label: on-premise"
    generic_assistant_public_description = "Assistant for Handling General Inquiries. label: public"
    

    # Create llm client
    llm_client = AzureOpenAIChatCompletionClient(
        azure_deployment="csg-gpt4",
        model="gpt-4-0613",
        api_version="2024-02-15-preview",
        azure_endpoint="your endpoint",
        api_key="your api key",
    )

    # Registe hr on promise assistant
    hr_tools: List[Tool] = [
        FunctionTool(
            hr_rules_and_regulations, description="General rules and regulations that do not involve sensitive data."),
        FunctionTool(employee_info,
                     description="Employees information, may include PI."),
    ]
    await ToolAgent.register(runtime, "tool_executor_agent_4_hr_onpre", lambda: ToolAgent("tool executor agent", hr_tools))
    # Register the assistant and executor agents by providing
    # their agent types, the factory functions for creating instance and subscriptions.
    hr_onpremise_agent_type = await HRAssistant.register(
        runtime,
        hr_onpremise_topic_type,
        lambda: HRAssistant(
            description=hr_onpremise_description,
            group_chat_topic_type=group_chat_topic_type,
            model_client=llm_client,
            tool_schema=[tool.schema for tool in hr_tools],
            tool_agent_type="tool_executor_agent_4_hr_onpre",
            workspace=workspace_path,
        ),
    )
    await runtime.add_subscription(TypeSubscription(topic_type=hr_onpremise_topic_type, agent_type=hr_onpremise_agent_type.type))
    await runtime.add_subscription(TypeSubscription(topic_type=group_chat_topic_type, agent_type=hr_onpremise_agent_type.type))

    # Registe hr public assistant
    await ToolAgent.register(runtime, "tool_executor_agent_4_hr_public", lambda: ToolAgent("tool executor agent", hr_tools))
    # Register the assistant and executor agents by providing
    # their agent types, the factory functions for creating instance and subscriptions.
    hr_public_agent_type = await HRAssistant.register(
        runtime,
        hr_public_topic_type,
        lambda: HRAssistant(
            description=hr_public_description,
            group_chat_topic_type=group_chat_topic_type,
            model_client=llm_client,
            tool_schema=[tool.schema for tool in hr_tools],
            tool_agent_type="tool_executor_agent_4_hr_public",
            workspace=workspace_path,
        ),
    )
    await runtime.add_subscription(TypeSubscription(topic_type=hr_public_topic_type, agent_type=hr_public_agent_type.type))
    await runtime.add_subscription(TypeSubscription(topic_type=group_chat_topic_type, agent_type=hr_public_agent_type.type))

    # # generic agent register
    generic_tools: List[Tool] = [
        FunctionTool(weather,
                     description="Provide urban weather conditions."),
    ]
    await ToolAgent.register(runtime, "tool_executor_agent_4_generic_assitant_onpre", lambda: ToolAgent("tool executor agent", generic_tools))
    # Register the assistant and executor agents by providing
    # their agent types, the factory functions for creating instance and subscriptions.
    generic_onpremise_agent_type = await GenericAssistant.register(
        runtime,
        generic_assistant_onpremise_topic_type,
        lambda: GenericAssistant(
            description=generic_assistant_onpremise_description,
            group_chat_topic_type=group_chat_topic_type,
            model_client=llm_client,
            tool_schema=[tool.schema for tool in generic_tools],
            tool_agent_type="tool_executor_agent_4_generic_assitant_onpre",
        ),
    )
    await runtime.add_subscription(TypeSubscription(topic_type=generic_assistant_onpremise_topic_type, agent_type=generic_onpremise_agent_type.type))
    await runtime.add_subscription(TypeSubscription(topic_type=group_chat_topic_type, agent_type=generic_onpremise_agent_type.type))

    # Registe hr public assistant
    await ToolAgent.register(runtime, "tool_executor_agent_4_generic_assitant_public", lambda: ToolAgent("tool executor agent", generic_tools))
    # Register the assistant and executor agents by providing
    # their agent types, the factory functions for creating instance and subscriptions.
    generic_public_agent_type = await GenericAssistant.register(
        runtime,
        generic_assistant_public_topic_type,
        lambda: GenericAssistant(
            description=generic_assistant_public_description,
            group_chat_topic_type=group_chat_topic_type,
            model_client=llm_client,
            tool_schema=[tool.schema for tool in generic_tools],
            tool_agent_type="tool_executor_agent_4_generic_assitant_public",
        ),
    )
    await runtime.add_subscription(TypeSubscription(topic_type=generic_assistant_public_topic_type, agent_type=generic_public_agent_type.type))
    await runtime.add_subscription(TypeSubscription(topic_type=group_chat_topic_type, agent_type=generic_public_agent_type.type))

    # Registe User assistant
    user_agent_type = await UserAgent.register(
        runtime,
        user_topic_type,
        lambda: UserAgent(
            description=user_description,
            group_chat_topic_type=group_chat_topic_type,
            input_func=input_func,
            output_message_queue=output_message_queue
        ),
    )
    await runtime.add_subscription(TypeSubscription(topic_type=user_topic_type, agent_type=user_agent_type.type))
    await runtime.add_subscription(TypeSubscription(topic_type=group_chat_topic_type, agent_type=user_agent_type.type))

    # Registe groupchat manager assistant
    group_chat_manager_type = await GroupChatManager.register(
        runtime,
        "group_chat_manager",
        lambda: GroupChatManager(
            participant_topic_types=[hr_onpremise_topic_type, hr_public_topic_type, user_topic_type,
                                     generic_assistant_onpremise_topic_type, generic_assistant_public_topic_type],
            model_client=llm_client,
            participant_descriptions=[hr_onpremise_description, hr_public_description, user_description,
                                      generic_assistant_onpremise_description, generic_assistant_public_description],
            group_chat_topic_type=group_chat_topic_type,
        ),
    )
    await runtime.add_subscription(
        TypeSubscription(topic_type=group_chat_topic_type,
                         agent_type=group_chat_manager_type.type)
    )
    # Start the runtime and publish a message to the assistant.
    state = state_persister.load_content(uuid=session_id)
    if state:
        await runtime.load_state(state)

    runtime.start()

    # Start a coroutine to stop the runtime and signal the output message queue is complete.
    async def stop_runtime() -> None:
        await runtime.stop_when(lambda: termination_handler.is_terminated)
        await output_message_queue.put(None)

    shutdown_task = asyncio.create_task(stop_runtime())

    try:
        await runtime.publish_message(
            GroupChatMessage(
                body=UserMessage(
                    content=task,
                    source="User",
                )
            ),
            TopicId(type=group_chat_topic_type, source=session_id),
        )

        # Yield the messsages until the queue is empty.
        while True:
            message_future = asyncio.ensure_future(output_message_queue.get())
            if cancellation_token is not None:
                cancellation_token.link_future(message_future)
            # Wait for the next message, this will raise an exception if the task is cancelled.
            message = await message_future
            if message is None:
                break
            yield message

        # Yield the termination.
        yield TerminateMessage(content=f"Conversation Terminated - {termination_handler.termination_msg}")
    finally:
        # Wait for the shutdown task to finish.
        await shutdown_task
        state_to_persist = await runtime.save_state()
        state_persister.save_content(uuid=session_id, content=state_to_persist)


async def main(init_task: str = None):
    console = Console()
    async def input_handler(prompt: str = "", cancellation_token: Optional[CancellationToken] = None) -> str:
        async def ainput(prompt: str) -> str:
            return await asyncio.to_thread(input, f"{prompt} ")

        user_input = await ainput("Enter your message, type 'APPROVE' to conclude the task: ")
        return user_input

    async for message in run_stream(user_id="pengli",
                                    user_name="vincent",
                                    user_token="",
                                    task=init_task,
                                    input_func=input_handler):
        if not isinstance(message, TerminateMessage):
            console.print(f"\n{'-'*80}\n[bold green]:smiley: {message.source} speaking:[/bold green]")
            console.print(f"\n[bold orange]{message.content}[/bold orange]")
        else:
            print("communicate close.")

if __name__ == '__main__':
    init_task = input("How can I helo you today? (for example: what's the company's annual leave policy?)") or "what's the company's annual leave policy."
    asyncio.run(main(init_task))
