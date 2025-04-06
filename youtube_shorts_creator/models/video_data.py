from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class VideoSegment:
    start_time: float
    end_time: float
    text: str

@dataclass
class VideoDetails:
    id: str
    title: str
    description: str
    duration: str
    view_count: int
    like_count: int
    thumbnail_url: str

@dataclass
class VideoAnalysis:
    key_points: List[str]
    summary: Optional[str] = None
    tags: Optional[List[str]] = None