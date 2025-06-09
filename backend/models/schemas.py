from pydantic import BaseModel
from typing import List, Optional

class TranscriptionSegment(BaseModel):
    start: float
    end: float
    text: str

class TranscriptionResult(BaseModel):
    segments: List[TranscriptionSegment]
    full_text: str

class AnalysisResponse(BaseModel):
    success: bool
    analysis: str
    transcription: Optional[TranscriptionResult] = None
    full_transcription: str = ""  # 全文の文字起こし
    error: Optional[str] = None
