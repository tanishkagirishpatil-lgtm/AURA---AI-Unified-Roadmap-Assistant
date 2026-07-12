from pydantic import BaseModel
from typing import List

class Competitor(BaseModel):
    name: str
    region: str
    pricing: str
    strengths: List[str]
    weaknesses: List[str]
    market_position: str


class MarketGap(BaseModel):
    title: str
    description: str


class CompetitorOutput(BaseModel):
    competitors: List[Competitor]
    market_gap_analysis: List[MarketGap]