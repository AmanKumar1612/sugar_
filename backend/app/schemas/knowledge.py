from pydantic import BaseModel


class KnowledgeBase(BaseModel):
    title: str
    category: str
    question: str
    answer: str
    keywords: str | None = None


class KnowledgeCreate(KnowledgeBase):
    pass


class KnowledgeUpdate(KnowledgeBase):
    pass
