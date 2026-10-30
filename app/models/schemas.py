from typing import List, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    text: str
    attachments: Optional[int] = 0


class TriageRequest(BaseModel):
    kind: str  # "complaint" | "report"
    messages: List[Message]


class ExtractedInfo(BaseModel):
    nickname: Optional[str] = None
    rule_refs: List[str] = Field(default_factory=list)
    has_evidence: bool = False
    server: Optional[str] = None


class DraftReply(BaseModel):
    lang: str
    text: str
    cited: List[str] = Field(default_factory=list)


class TriageResponse(BaseModel):
    lang: str
    category: str
    priority: str  # "p0" | "p1" | "p2" | "p3"
    is_spam_or_duplicate: bool = False
    extracted: ExtractedInfo
    draft_reply: DraftReply
    needs_human: bool
    confidence: float
    reasons: List[str] = Field(default_factory=list)