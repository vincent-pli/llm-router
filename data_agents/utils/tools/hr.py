from typing import Annotated
from dataclasses import dataclass


async def hr_rules_and_regulations(query: Annotated[str, "question will be search in document of rules and regulations"],
                            ) -> str:
    return "The company offers an annual leave of 10 days per year, and employees are required to notify their line manager 3 days in advance to take annual leave."


@dataclass
class AnalysisRes:
    id: int
    name: str
    title: str
    marital: bool
    age: int
    salary: float

async def employee_info(employee_id: Annotated[str, "ID of employee"],) -> str:
    return AnalysisRes(
        id=123,
        name="pengli",
        title="TPS",
        marital=True,
        age=42,
        salary=1,
    )



if __name__ == "__main__":
    print("nothing")