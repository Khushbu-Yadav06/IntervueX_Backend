from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database.connection import get_db

from schemas.interview import InterviewRequest
from schemas.answer import AnswerRequest

from schemas.session import SubmitAnswerRequest
from schemas.evaluation import EvaluationRequest

from services.interview_service import (
    create_interview_session,
    submit_interview_answer,
    get_current_question,
    get_interview_results,
    save_answer_evaluation,
    calculate_interview_score
)
from services.ai_service import start_ai_interview

router = APIRouter(
    prefix="/api/interviews",
    tags=["Interviews"]
)




@router.post("/generate")
def generate_interview(
    request: InterviewRequest,
    db: Session = Depends(get_db)
):
    candidate_profile = {
        "target_role": request.target_role,
        "education": request.education,
        "experience": request.experience,
        "skills": request.skills,
        "interview_type": request.interview_type,
        "difficulty": request.difficulty,
        "number_of_questions": request.number_of_questions,
        "resume_text": None
    }

    try:
        # Start the interview using the external AI API
        ai_response = start_ai_interview(candidate_profile)

        # Extract the AI session ID and first question
        ai_session_id = ai_response.get("session_id")

        first_question = (
            ai_response.get("question")
            or ai_response.get("generated_question")
            or ai_response.get("question_text")
        )

        if not ai_session_id or not first_question:
            raise HTTPException(
                status_code=502,
                detail="AI API did not return a valid session ID or question."
            )

        # Save the interview and first question in MySQL
        session = create_interview_session(
            db,
            candidate_profile,
            ai_session_id,
            first_question
        )

        return {
            "status": "success",
            "message": "Interview session created successfully",
            "interview_id": session.interview_id,
            "candidate_profile": candidate_profile,
            "questions": [first_question],
            "total_questions": request.number_of_questions,
            "interview_status": session.status
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Could not start AI interview: {str(error)}"
        )



@router.post("/evaluate")
def evaluate_answer(request: AnswerRequest):

    return {
        "status": "success",
        "message": "Answer received successfully",
        "question": request.question,
        "submitted_answer": request.answer,
        "evaluation": {
            "feedback": "Answer received. AI evaluation will be integrated soon.",
            "score": None
        }
    }



@router.post("/{interview_id}/answer")
def submit_answer(
    interview_id: str,
    request: SubmitAnswerRequest,
    db: Session = Depends(get_db)
):
    result = submit_interview_answer(
        db,
        interview_id,
        request.question_index,
        request.answer
    )

    if not result["success"]:

        message = result["message"]

        if "not found" in message.lower():
            status_code = 404
        elif "AI" in message:
            status_code = 502
        else:
            status_code = 400

        raise HTTPException(
            status_code=status_code,
            detail=message
        )

    return {
        "status": "success",
        "message": result["message"],
        "question": result["question"],
        "evaluation": result["evaluation"],
        "score": result["score"],
        "answered_question": result["answered_question"],
        "next_question": result["next_question"],
        "interview_completed": result["interview_completed"],
        "interview_status": result["interview_status"]
    }



@router.get("/{interview_id}/current")
def current_question(
    interview_id: str,
    db: Session = Depends(get_db)
):

    result = get_current_question(db, interview_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found."
        )

    return result


@router.get("/{interview_id}/results")
def interview_results(
    interview_id: str,
    db: Session = Depends(get_db)
):

    result = get_interview_results(db, interview_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found."
        )

    return result


@router.post("/{interview_id}/evaluate")
def evaluate_interview_answer(
    interview_id: str,
    request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    result = save_answer_evaluation(
        db,
        interview_id,
        request.question_index,
        request.feedback,
        request.score
    )

    if not result["success"]:
        status_codes = {
            "interview_not_found": 404,
            "interview_not_completed": 400,
            "answer_not_found": 404,
            "already_evaluated": 409
        }

        raise HTTPException(
            status_code=status_codes[result["error"]],
            detail=result["message"]
        )

    return {
        "status": "success",
        "message": "Answer evaluation saved successfully.",
        "question_index": request.question_index,
        "evaluation": result["answer"]["evaluation"]
    }


@router.get("/{interview_id}/score")
def interview_score(
    interview_id: str,
    db: Session = Depends(get_db)
):
    result = calculate_interview_score(db, interview_id)

    if not result["success"]:
        status_codes = {
            "interview_not_found": 404,
            "interview_not_completed": 400,
            "evaluations_pending": 400
        }

        raise HTTPException(
            status_code=status_codes[result["error"]],
            detail=result["message"]
        )

    return result
