from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question_th: str = Field(..., min_length=2, description="คำถามภาษาไทย")
    session_id: str | None = None


class TraceResponse(BaseModel):
    trace_id: str
    question: str
    plan: str | None = None
    sql: str | None = None
    row_count: int = 0
    verdict: str | None = None
    answer: str | None = None
    langsmith_url: str | None = None
