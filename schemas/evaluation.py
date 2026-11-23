
from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    question_index: int = Field(ge=0)
    feedback: str = Field(min_length=1, max_length=2000)
    score: float
