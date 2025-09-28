from __future__ import annotations
from pydantic import BaseModel, HttpUrl
import datetime


class Score(BaseModel):
    """
    Represents the calculated scores for a given source.
    """
    trust: float
    ai_slop: float


class Source(BaseModel):
    """
    Represents a source URL that has been analyzed.
    """
    id: int
    url: HttpUrl
    analyzed_at: datetime.datetime
    score: Score


class Entry(BaseModel):
    """
    Represents a single "Xikizpedia" entry.
    """
    id: int
    title: str
    slug: str
    abstract: str
    content: str
    source: Source
    created_at: datetime.datetime

class EntryCreate(BaseModel):
    """
    Represents the data needed to create a new entry.
    """
    title: str
    content: str
    url: HttpUrl
    abstract: str

class SourceCreate(BaseModel):
    """
    Represents the data needed to create a new source.
    """
    url: HttpUrl

class ScoreCreate(BaseModel):
    """
    Represents the data needed to create a new score.
    """
    trust: float
    ai_slop: float
    source_id: int