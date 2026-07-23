from pydantic import BaseModel
from typing import List


class ChecklistItem(BaseModel):
    text: str
    status: str  # "ok" | "warn" | "risk"
    note: str


class LegalOutput(BaseModel):
    readiness_score: int
    readiness_label: str
    summary: str
    trademark_checklist: List[ChecklistItem]
    copyright_checklist: List[ChecklistItem]
    patent_checklist: List[ChecklistItem]