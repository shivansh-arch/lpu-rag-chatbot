from fastapi import FastAPI, HTTPException
from mock_student_api.data import students as student_data
from mock_student_api.models import Attendance, CGPA, FeeStatus, Message

app = FastAPI()


@app.get("/students/{student_id}/attendance", response_model=Attendance)
async def get_attendance(student_id: str):
    student = student_data.get(student_id)

    if student:
        return Attendance(
            student_id=student_id,
            attendance=student["attendance"]
        )

    raise HTTPException(
        status_code=404,
        detail="Student not found"
    )


@app.get("/students/{student_id}/cgpa", response_model=CGPA)
async def get_cgpa(student_id: str):
    student = student_data.get(student_id)

    if student:
        return CGPA(
            student_id=student_id,
            cgpa=student["cgpa"]
        )

    raise HTTPException(
        status_code=404,
        detail="Student not found"
    )


@app.get("/students/{student_id}/fee-status", response_model=FeeStatus)
async def get_fee_status(student_id: str):
    student = student_data.get(student_id)

    if student:
        return FeeStatus(
            student_id=student_id,
            fee_status=student["fee_status"]
        )

    raise HTTPException(
        status_code=404,
        detail="Student not found"
    )


@app.get("/students/{student_id}/messages", response_model=Message)
async def get_messages(student_id: str):
    student = student_data.get(student_id)

    if student:
        return Message(
            student_id=student_id,
            messages=student["messages"]
        )

    raise HTTPException(
        status_code=404,
        detail="Student not found"
    )