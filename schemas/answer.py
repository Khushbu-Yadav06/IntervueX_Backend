
from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):

    question: str

    answer: str = Field(
        min_length=1,
        max_length=5000
    )
