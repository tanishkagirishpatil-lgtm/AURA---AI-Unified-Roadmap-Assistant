from pydantic import BaseModel
from typing import List


class GrowthSegment(BaseModel):
    segment: str
    growth_rate: str


class MarketOpportunity(BaseModel):
    title: str
    description: str


class ThreatRisk(BaseModel):
    title: str
    description: str


class MarketOutput(BaseModel):
    tam: str
    sam: str
    som: str

    growth_rate_by_segment: List[GrowthSegment]

    industry_trends: List[str]

    market_opportunities: List[MarketOpportunity]

    threats_and_risks: List[ThreatRisk]

    market_intelligence_summary: str