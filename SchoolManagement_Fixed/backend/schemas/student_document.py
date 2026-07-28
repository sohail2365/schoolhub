from datetime import datetime
from pydantic import BaseModel


class StudentDocumentOut(BaseModel):
    id: int
    school_id: int
    student_id: int
    doc_type: str
    file_url: str
    file_name: str | None = None
    label: str | None = None
    uploaded_by_user_id: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True
