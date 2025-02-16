from autogen_core.models import (
    ChatCompletionClient,
)
from autogen_core.tools import ToolSchema
from typing import Optional, List
from data_agents.base import BaseGroupChatAgent
from data_agents.messages import RequestToSpeak
from autogen_core import (
    MessageContext,
    message_handler,
)
from autogen_core.models import (
    UserMessage,
)

class HRAssistant(BaseGroupChatAgent):
    def __init__(
        self,
        description: str,
        group_chat_topic_type: str,
        model_client: ChatCompletionClient,
        tool_schema: Optional[List[ToolSchema]] = None,
        tool_agent_type: Optional[str] = None,
        workspace: Optional[str] = None,
    ) -> None:
        super().__init__(
            description=description,
            group_chat_topic_type=group_chat_topic_type,
            model_client=model_client,
            system_message="""
            You are an HR professional at a corporation, well-versed in HR-related matters. For questions pertaining to the company, utilize tools to provide answers.
            """,
            tool_schema=tool_schema,
            tool_agent_type=tool_agent_type,
            workspace=workspace
        )

        self.extra_instruction = None

    @message_handler
    async def handle_request_to_speak(self, message: RequestToSpeak, ctx: MessageContext) -> None:
        if self.extra_instruction:
            self._chat_history.append(
                UserMessage(content=self.extra_instruction, source="system")
            )
        await super().handle_request_to_speak(
            message,
            ctx
        )