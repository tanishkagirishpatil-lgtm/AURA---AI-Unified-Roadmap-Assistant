from pydantic import BaseModel
from typing import List


class IdeaOutput(BaseModel):
    product_name: str
    summary: str
    industry: str
    goal: str

    problem_statement: List[str]
    target_users: List[str]

    value_proposition: str
    usp: str

    market_category: str

    monetization_models: List[str]
    competitors: List[str]

    suggested_mvp_features: List[str]

    assumptions: List[str]
    success_metrics: List[str]

    product_vision: str
    complexity_level: str