from pydantic import BaseModel
from typing import List


class UserStory(BaseModel):
    id: str
    story: str
    acceptance_criteria: str


class PRDOutput(BaseModel):
    executive_summary: str
    objectives: List[str]
    out_of_scope: List[str]
    features: List[str]
    user_stories: List[UserStory]
    success_metrics: List[str]