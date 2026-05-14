from pydantic import BaseModel


class SafetyDecision(BaseModel):
    blocked: bool = False
    reason: str = ""
    message: str = ""
