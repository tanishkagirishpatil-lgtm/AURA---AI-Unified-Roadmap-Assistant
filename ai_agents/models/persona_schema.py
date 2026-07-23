from pydantic import BaseModel
from typing import List


class Persona(BaseModel):
    name: str
    role: str
    age: int
    context: str  # e.g. "Tier-2 City", "Working Professional"
    goals: List[str]
    pain_points: List[str]
    motivation_quote: str


class PersonaOutput(BaseModel):
    personas: List[Persona]