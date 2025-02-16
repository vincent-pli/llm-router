from typing import List

from autogen_core.models import (
    ChatCompletionClient,
)
from autogen_core.tools import ToolSchema
from typing import Optional
from data_agents.base import BaseGroupChatAgent

class GenericAssistant(BaseGroupChatAgent):
    def __init__(
        self,
        description: str,
        group_chat_topic_type: str,
        model_client: ChatCompletionClient,
        tool_schema: Optional[List[ToolSchema]] = None,
        tool_agent_type: Optional[str] = None
    ) -> None:
        super().__init__(
            description=description,
            group_chat_topic_type=group_chat_topic_type,
            model_client=model_client,
            system_message="""
            A usefule AI assistant, try best to resolve the question.
            """,
            tool_schema=tool_schema,
            tool_agent_type=tool_agent_type
        )


