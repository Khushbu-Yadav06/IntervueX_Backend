
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class InterviewRequest(BaseModel):

    target_role: str

    education: str

    experience: str

    skills: List[str]

    interview_type: Literal["Technical", "HR"]

    difficulty: Literal["Easy", "Medium", "Hard"]

    number_of_questions: Literal[20, 30, 50] = 20

    resume_text: Optional[str] = None
