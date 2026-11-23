
import os
import httpx

from dotenv import load_dotenv

load_dotenv()

AI_API_URL = os.getenv("AI_API_URL")



def start_ai_interview(candidate_profile):

    if not AI_API_URL:
        raise Exception("AI API URL is not configured.")

    payload = {
        "target_role": candidate_profile["target_role"],
        "education": candidate_profile["education"],
        "experience": candidate_profile["experience"],
        "interview_type": candidate_profile["interview_type"],
        "interview_difficulty": candidate_profile["difficulty"],
        "interview_length": candidate_profile["number_of_questions"]
    }

    try:
        response = httpx.post(
            f"{AI_API_URL}/interviews/start",
            json=payload,
            timeout=400
        )

        if response.status_code >= 400:
            raise Exception(
                f"AI API status: {response.status_code}. "
                f"Validation details: {response.text}"
            )

        return response.json()

    except httpx.HTTPError as error:
        raise Exception(f"AI interview service error: {str(error)}")



def submit_ai_answer(ai_session_id, answer):

    if not AI_API_URL:
        raise Exception("AI API URL is not configured.")

    payload = {
        "answer": answer
    }

    try:
        response = httpx.post(
            f"{AI_API_URL}/interviews/{ai_session_id}/answer",
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        return response.json()

    except httpx.HTTPError as error:
        raise Exception(f"AI answer evaluation error: {str(error)}")


def get_ai_interview_status(ai_session_id):

    if not AI_API_URL:
        raise Exception("AI API URL is not configured.")

    try:
        response = httpx.get(
            f"{AI_API_URL}/interviews/{ai_session_id}/status",
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    except httpx.HTTPStatusError as error:
     raise Exception(
        f"AI API returned {error.response.status_code}: "
        f"{error.response.text}"
    )

    except httpx.HTTPError as error:
        raise Exception(f"AI interview service error: {str(error)}")
