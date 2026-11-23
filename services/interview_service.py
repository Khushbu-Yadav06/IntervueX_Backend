import uuid

from sqlalchemy.orm import Session

from database.models import (
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
    AnswerEvaluation
)
from services.ai_service import submit_ai_answer



def create_interview_session(db: Session, candidate_profile, ai_session_id, first_question):

    # Generate a unique ID for our application
    interview_id = str(uuid.uuid4())

    # Create the interview session
    session = InterviewSession(
        interview_id=interview_id,
        ai_session_id=ai_session_id,
        target_role=candidate_profile["target_role"],
        education=candidate_profile["education"],
        experience=candidate_profile["experience"],
        skills=candidate_profile["skills"],
        interview_type=candidate_profile["interview_type"],
        difficulty=candidate_profile["difficulty"],
        number_of_questions=candidate_profile["number_of_questions"],
        resume_text=candidate_profile.get("resume_text"),
        status="in_progress"
    )

    # Save the first AI-generated question
    session.questions.append(
        InterviewQuestion(
            question_text=first_question,
            question_order=0
        )
    )

    # Save everything in MySQL
    db.add(session)
    db.commit()
    db.refresh(session)

    return session



def get_interview_session(db: Session, interview_id):

    return db.query(InterviewSession).filter(
        InterviewSession.interview_id == interview_id
    ).first()





def submit_interview_answer(db: Session, interview_id, question_index, answer):

    # Find the interview session
    session = get_interview_session(db, interview_id)

    if session is None:
        return {
            "success": False,
            "message": "Interview session not found."
        }

    if session.status != "in_progress":
        return {
            "success": False,
            "message": "This interview is already completed."
        }

    # Get questions in the correct order
    questions = sorted(session.questions, key=lambda q: q.question_order)

    # Check question index
    answered_count = sum(
        1 for q in questions if q.answer is not None
    )

    if question_index != answered_count:
        return {
            "success": False,
            "message": "Invalid question index."
        }

    if question_index >= len(questions):
        return {
            "success": False,
            "message": "Question not found."
        }

    # Check AI session ID
    if not session.ai_session_id:
        return {
            "success": False,
            "message": "AI session ID not found."
        }

    # Send answer to the AI API
    try:
        ai_response = submit_ai_answer(
            session.ai_session_id,
            answer
        )
    except Exception as error:
        return {
            "success": False,
            "message": f"AI evaluation failed: {str(error)}"
        }

    # Extract AI evaluation
    evaluation = ai_response.get("evaluation")
    score = ai_response.get(
        "current_score",
        ai_response.get("score_attained")
    )

    if evaluation is None or score is None:
        return {
            "success": False,
            "message": "AI API returned incomplete evaluation data."
        }

    keywords = ai_response.get("keywords", [])

    feedback = str(evaluation)

    if keywords:
        feedback += " | Keywords: " + ", ".join(keywords)

    interview_completed = ai_response.get(
        "interview_completed", False
    )

    next_question = ai_response.get("next_question")

    # Save candidate answer
    question = questions[question_index]

    new_answer = InterviewAnswer(
        question_id=question.id,
        answer_text=answer
    )

    db.add(new_answer)
    db.flush()

    # Save AI evaluation
    new_evaluation = AnswerEvaluation(
        answer_id=new_answer.id,
        feedback=feedback,
        score=float(score)
    )

    db.add(new_evaluation)

    # Save the next question if interview is not completed
    if interview_completed:
        session.status = "completed"

    else:
        if not next_question:
            db.rollback()
            return {
                "success": False,
                "message": "AI API did not return the next question."
            }

        session.questions.append(
            InterviewQuestion(
                question_text=next_question,
                question_order=question_index + 1
            )
        )

    # Update total question count if returned by AI
    if ai_response.get("total_questions") is not None:
        session.number_of_questions = ai_response["total_questions"]

    db.commit()

    return {
        "success": True,
        "message": "Answer evaluated and saved successfully.",
        "question": question.question_text,
        "evaluation": feedback,
        "score": float(score),
        "answered_question": question_index + 1,
        "next_question": next_question,
        "interview_completed": interview_completed,
        "interview_status": session.status
    }




def get_current_question(db: Session, interview_id):

    session = get_interview_session(db, interview_id)

    if session is None:
        return None

    questions = sorted(session.questions, key=lambda q: q.question_order)

    if session.status == "completed":
        return {
            "interview_id": interview_id,
            "interview_status": "completed",
            "message": "Interview has been completed.",
            "current_question": None
        }

    answered_questions = sum(
        1 for question in questions if question.answer is not None
    )

    if answered_questions >= len(questions):
        return {
            "interview_id": interview_id,
            "interview_status": "completed",
            "message": "Interview has been completed.",
            "current_question": None
        }

    return {
        "interview_id": interview_id,
        "interview_status": session.status,
        "current_question_index": answered_questions,
        "current_question": questions[answered_questions].question_text,
        "total_questions": len(questions),
        "answered_questions": answered_questions
    }




def get_interview_results(db: Session, interview_id):

    session = get_interview_session(db, interview_id)

    if session is None:
        return None

    if session.status != "completed":
        return {
            "completed": False,
            "message": "Interview is still in progress."
        }

    questions = sorted(session.questions, key=lambda q: q.question_order)

    answers = []

    for question in questions:
        answer = question.answer

        if answer is not None:
            answers.append({
                "question_index": question.question_order,
                "question": question.question_text,
                "answer": answer.answer_text,
                "evaluation": (
                    {
                        "feedback": answer.evaluation.feedback,
                        "score": answer.evaluation.score
                    }
                    if answer.evaluation is not None
                    else None
                )
            })

    return {
        "completed": True,
        "interview_id": interview_id,
        "candidate_profile": {
            "target_role": session.target_role,
            "education": session.education,
            "experience": session.experience,
            "skills": session.skills
        },
        "total_questions": len(questions),
        "total_answered": len(answers),
        "answers": answers,
        "score": calculate_interview_score(db, interview_id),
        "interview_status": session.status
    }




def save_answer_evaluation(db: Session, interview_id, question_index, feedback, score):

    session = get_interview_session(db, interview_id)

    if session is None:
        return {
            "success": False,
            "error": "interview_not_found",
            "message": "Interview session not found."
        }

    if session.status != "completed":
        return {
            "success": False,
            "error": "interview_not_completed",
            "message": "Interview must be completed before evaluation."
        }

    questions = sorted(session.questions, key=lambda q: q.question_order)

    if question_index < 0 or question_index >= len(questions):
        return {
            "success": False,
            "error": "answer_not_found",
            "message": "Answer not found for the given question index."
        }

    answer = questions[question_index].answer

    if answer is None:
        return {
            "success": False,
            "error": "answer_not_found",
            "message": "Answer not found for the given question index."
        }

    if answer.evaluation is not None:
        return {
            "success": False,
            "error": "already_evaluated",
            "message": "This answer has already been evaluated."
        }

    evaluation = AnswerEvaluation(
        answer_id=answer.id,
        feedback=feedback,
        score=score
    )

    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return {
        "success": True,
        "answer": {
            "question_index": question_index,
            "question": questions[question_index].question_text,
            "answer": answer.answer_text,
            "evaluation": {
                "feedback": evaluation.feedback,
                "score": evaluation.score
            }
        }
    }




def calculate_interview_score(db: Session, interview_id):

    session = get_interview_session(db, interview_id)

    if session is None:
        return {
            "success": False,
            "error": "interview_not_found",
            "message": "Interview session not found."
        }

    if session.status != "completed":
        return {
            "success": False,
            "error": "interview_not_completed",
            "message": "Interview is not completed yet."
        }

    questions = sorted(session.questions, key=lambda q: q.question_order)

    answers = [question.answer for question in questions]

    if not answers or any(answer is None for answer in answers):
        return {
            "success": False,
            "error": "evaluations_pending",
            "message": "All answers must be submitted before calculating the final score."
        }

    evaluations = [answer.evaluation for answer in answers]

    if any(evaluation is None for evaluation in evaluations):
        return {
            "success": False,
            "error": "evaluations_pending",
            "message": "All answers must be evaluated before calculating the final score."
        }

    # Calculate score using the AI model's 4-mark system
    total_score = sum(evaluation.score for evaluation in evaluations)

    maximum_score = len(evaluations) * 4

    average_score = total_score / len(evaluations)

    percentage = (total_score / maximum_score) * 100

    return {
        "success": True,
        "evaluation_completed": True,
        "total_score": round(total_score, 2),
        "maximum_score": maximum_score,
        "average_score": round(average_score, 2),
        "percentage": round(percentage, 2)
    }
