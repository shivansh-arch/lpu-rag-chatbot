from pydantic import BaseModel


class Attendance(BaseModel):
    student_id: str
    attendance: float


class CGPA(BaseModel):
    student_id: str
    cgpa: float


class FeeStatus(BaseModel):
    student_id: str
    fee_status: str


class Message(BaseModel):
    student_id: str
    messages: list[str]