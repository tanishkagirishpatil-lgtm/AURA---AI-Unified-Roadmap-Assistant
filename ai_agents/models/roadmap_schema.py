from pydantic import BaseModel, Field
from typing import List, Dict, Any


class ExecutiveSummary(BaseModel):
    product: str
    estimated_duration: str
    team_size: str
    launch_strategy: str


class Sprint(BaseModel):
    sprint: int
    duration: str
    goals: List[str]


class Dependency(BaseModel):
    feature: str
    depends_on: List[str]


class Milestone(BaseModel):
    name: str
    week: int


class PriorityFeature(BaseModel):
    feature: str
    priority: str
    impact: str
    complexity: str


class RoadmapOutput(BaseModel):

    executive_summary: ExecutiveSummary

    development_phases: List[Dict[str, Any]]

    sprints: List[Sprint]

    feature_dependencies: List[Dependency]

    milestones: List[Milestone]

    resource_plan: Dict[str, Any]

    risk_plan: List[Dict[str, Any]]

    mvp_features: List[Dict[str, Any]]

    post_mvp_features: List[Dict[str, Any]]

    launch_checklist: List[Dict[str, Any]]

    timeline: Dict[str, Any]

    priority_matrix: List[PriorityFeature]

    