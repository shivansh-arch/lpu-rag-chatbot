import os
from dotenv import load_dotenv
from google import genai

from rag_bot.retrieval import retrieve_relevant_docs
from rag_bot.student_fetch import (
    get_attendance,
    get_cgpa,
    get_fee_status,
    get_messages,
)


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# Tool wrappers
# ============================================================

def make_attendance_tool(student_id):
    def get_student_attendance() -> float | None:
        """Get the student's current attendance percentage."""
        return get_attendance(student_id)

    return get_student_attendance


def make_cgpa_tool(student_id):
    def get_student_cgpa() -> float | None:
        """Get the student's current CGPA."""
        return get_cgpa(student_id)

    return get_student_cgpa


def make_fee_status_tool(student_id):
    def get_student_fee_status() -> str | None:
        """Get the student's current fee payment status."""
        return get_fee_status(student_id)

    return get_student_fee_status


def make_messages_tool(student_id):
    def get_student_messages() -> list[str] | None:
        """Get the student's messages and announcements."""
        return get_messages(student_id)

    return get_student_messages


# ============================================================
# General RAG pipeline
# ============================================================

def answer_question(question, student_id):

    # --------------------------------------------------------
    # 1. Retrieve relevant announcement/policy documents
    # --------------------------------------------------------

    retrieved_docs = retrieve_relevant_docs(
        question,
        n_results=3
    )

    policy_text = "\n\n".join(
        doc["text"]
        for doc in retrieved_docs
    )

    # --------------------------------------------------------
    # 2. Create student-specific tools
    # --------------------------------------------------------

    attendance_tool = make_attendance_tool(student_id)
    cgpa_tool = make_cgpa_tool(student_id)
    fee_status_tool = make_fee_status_tool(student_id)
    messages_tool = make_messages_tool(student_id)

    tools = [
        attendance_tool,
        cgpa_tool,
        fee_status_tool,
        messages_tool,
    ]

    # --------------------------------------------------------
    # 3. Create Gemini chat with tools
    # --------------------------------------------------------

    chat = client.chats.create(
        model="gemini-2.5-flash",
        config={
            "tools": tools
        }
    )

    # --------------------------------------------------------
    # 4. Build prompt
    # --------------------------------------------------------

    prompt = f"""
You are an LPU student assistant.

Answer the student's question using the retrieved
university information and the student's data.

Retrieved university information:

{policy_text}

Student question:

{question}

You have access to tools that can retrieve specific
information about this student.

Use the tools whenever you need information such as:
- attendance
- CGPA
- fee status
- student messages

Do not invent student information.

Do not invent university rules.

If the retrieved information is insufficient, say so clearly.

Give a concise and useful answer.
"""

    # --------------------------------------------------------
    # 5. Send message
    # --------------------------------------------------------

    response = chat.send_message(prompt)

    return response.text


# ============================================================
# Test
# ============================================================

