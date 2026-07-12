from pydantic import BaseModel
from typing import List

class IdeaOutput(BaseModel):
    product_name: str
    category: str

    target_users: str

    confidence_score: int

    problem_statement: str
    recommended_solution: str

    market_size: str
    target_users_count: int

    revenue_model: str

    competitor_count: int
    mvp_features_count: int

    market_opportunity_summary: str

    next_steps: List[str]
    