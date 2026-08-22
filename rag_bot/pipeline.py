import os

from dotenv import load_dotenv
from google import genai

from rag_bot.retrieval import retrieve_relevant_docs
from rag_bot.student_fetch import (
    get_attendance,
    get_fee_status,
)


# Load variables from .env
load_dotenv()


# Create Gemini client
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def answer_question(question, student_id):

    question_lower = question.lower()

    # Currently we only handle exam eligibility questions
    if (
        "eligible" in question_lower
        or "eligibility" in question_lower
        or "exam" in question_lower
    ):

        # Retrieve relevant university policy
        retrieved_docs = retrieve_relevant_docs(question)

        policy_context = "\n\n".join(
            doc["text"]
            for doc in retrieved_docs
        )

        # Fetch student's actual data through the FastAPI service
        attendance = get_attendance(student_id)
        fee_status = get_fee_status(student_id)

        # Student doesn't exist / API failed
        if attendance is None or fee_status is None:
            return "Could not find student information."

        # Build prompt for Gemini
        prompt = f"""
You are an LPU student assistant.

Answer the student's question using ONLY the information
provided below. Do not invent or assume information.

Student ID:
{student_id}

Student attendance:
{attendance}%

Student fee status:
{fee_status}

Relevant university policy/notices:
{policy_context}

Student's question:
{question}

To determine exam eligibility:

1. Find the attendance requirement from the provided policy.
2. Compare it with the student's actual attendance.
3. Check the student's fee status.
4. Clearly state whether the student is eligible or not.
5. If the student is not eligible, clearly explain why.

If the provided information is insufficient, say so.

Give a concise and clear answer.
"""

        # Generate response
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    return "I can currently answer exam eligibility questions only."


if __name__ == "__main__":

    question = "Am I eligible for the exam?"
    student_id = "103"

    answer = answer_question(
        question,
        student_id
    )

    print("\nAnswer:")
    print(answer)