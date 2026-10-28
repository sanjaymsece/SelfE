"""Structured output contracts for every AI feature.

Gemini is asked to produce these schemas and responses are validated with
Pydantic before anything is returned or persisted.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AnalyticsExplanation(BaseModel):
    summary: str = Field(min_length=20, max_length=3000)
    growth_explanation: str = Field(min_length=10, max_length=3000)
    key_findings: list[str] = Field(min_length=1, max_length=8)
    recommendations: list[str] = Field(min_length=1, max_length=8)


class ContentIdeaItem(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    hook: str = Field(min_length=5, max_length=400)
    angle: str = Field(min_length=5, max_length=600)
    format: Literal["reel", "carousel", "image", "story", "text"]
    hashtags: list[str] = Field(default_factory=list, max_length=12)
    why_it_works: str = Field(min_length=5, max_length=600)


class ContentIdeasResult(BaseModel):
    ideas: list[ContentIdeaItem] = Field(min_length=1, max_length=10)


class CaptionItem(BaseModel):
    text: str = Field(min_length=5, max_length=2200)
    hashtags: list[str] = Field(default_factory=list, max_length=20)
    call_to_action: str = Field(min_length=2, max_length=250)
    tone: str = Field(min_length=2, max_length=60)


class CaptionsResult(BaseModel):
    captions: list[CaptionItem] = Field(min_length=1, max_length=10)


class ScriptSection(BaseModel):
    section: str = Field(min_length=2, max_length=80)
    direction: str = Field(min_length=5, max_length=1000)
    dialogue: str = Field(min_length=1, max_length=1500)


class GeneralScriptItem(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    hook: str = Field(min_length=5, max_length=500)
    sections: list[ScriptSection] = Field(min_length=2, max_length=10)
    call_to_action: str = Field(min_length=2, max_length=300)
    estimated_duration_seconds: int = Field(ge=5, le=600)


class ScriptsResult(BaseModel):
    scripts: list[GeneralScriptItem] = Field(min_length=1, max_length=3)


class ReelScene(BaseModel):
    scene_number: int = Field(ge=1, le=20)
    duration_seconds: int = Field(ge=1, le=90)
    visual: str = Field(min_length=5, max_length=1000)
    dialogue: str = Field(min_length=1, max_length=1200)
    camera_angle: str = Field(min_length=2, max_length=250)
    lighting: str = Field(min_length=2, max_length=250)
    background: str = Field(min_length=2, max_length=400)
    on_screen_text: str = Field(default="", max_length=300)


class ReelPlanResult(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    concept: str = Field(min_length=10, max_length=1200)
    hook: str = Field(min_length=5, max_length=500)
    target_audience: str = Field(default="", max_length=300)
    scenes: list[ReelScene] = Field(min_length=3, max_length=12)
    music_suggestion: str = Field(min_length=2, max_length=300)
    caption: str = Field(min_length=5, max_length=2200)
    hashtags: list[str] = Field(default_factory=list, max_length=20)
    call_to_action: str = Field(min_length=2, max_length=300)
    estimated_duration_seconds: int = Field(ge=10, le=180)

    @model_validator(mode="after")
    def validate_scene_order(self):
        numbers = [scene.scene_number for scene in self.scenes]
        if len(numbers) != len(set(numbers)):
            raise ValueError("Scene numbers must be unique.")
        if numbers != sorted(numbers):
            raise ValueError("Scenes must be ordered by scene_number.")
        return self


Sentiment = Literal["positive", "neutral", "negative"]
Intent = Literal[
    "question",
    "collaboration",
    "praise",
    "complaint",
    "feedback",
    "spam",
    "other",
]


class CommentAnalysisItem(BaseModel):
    comment_id: int
    sentiment: Sentiment
    intent: Intent
    is_question: bool
    is_collaboration_opportunity: bool
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str = Field(min_length=3, max_length=600)


class CommentAnalysisResult(BaseModel):
    analyses: list[CommentAnalysisItem] = Field(min_length=1, max_length=50)


class ReplyItem(BaseModel):
    text: str = Field(min_length=2, max_length=1200)
    tone: str = Field(min_length=2, max_length=60)
    rationale: str = Field(default="", max_length=600)


class ReplySuggestionsResult(BaseModel):
    suggestions: list[ReplyItem] = Field(min_length=1, max_length=3)
