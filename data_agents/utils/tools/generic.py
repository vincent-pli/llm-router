from typing import Annotated

async def weather(city: Annotated[str, "city of the weather"]) -> str:
    return "Xi'an is sunny today."
