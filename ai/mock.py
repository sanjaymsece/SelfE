"""Deterministic mock provider for tests and local dry runs.

Usage:
    from unittest.mock import patch
    from ai.mock import MockAIClient
    mock = MockAIClient(responses={"ContentIdeasResult": {...}})
    with patch("ai.service.get_ai_client", return_value=mock):
        ...
"""

from typing import Any

from pydantic import BaseModel

from ai.client import AIResult, BaseAIClient
from ai.exceptions import AIError, AIInvalidResponse


def _content_ideas_default() -> dict:
    return {
        "ideas": [
            {
                "title": "Three pantry swaps that save money",
                "hook": "Stop buying this one expensive ingredient.",
                "angle": "Show three affordable swaps with a cost comparison.",
                "format": "reel",
                "hashtags": ["#budgetcooking", "#plantbased"],
                "why_it_works": "Actionable cost savings are easy to save and share.",
            }
        ]
    }


def _captions_default() -> dict:
    return {
        "captions": [
            {
                "text": "Small swaps, big flavour. Which one are you trying first?",
                "hashtags": ["#plantbased", "#easyrecipes"],
                "call_to_action": "Save this for your next grocery run.",
                "tone": "friendly",
            }
        ]
    }


def _scripts_default() -> dict:
    return {
        "scripts": [
            {
                "title": "Pantry swap script",
                "hook": "Here is how I cut my grocery bill without giving up flavour.",
                "sections": [
                    {
                        "section": "Problem",
                        "direction": "Direct-to-camera, quick cuts.",
                        "dialogue": "One ingredient was quietly blowing my budget.",
                    },
                    {
                        "section": "Solution",
                        "direction": "Show each swap on the counter.",
                        "dialogue": "These three swaps cost less and taste just as good.",
                    },
                ],
                "call_to_action": "Follow for more practical kitchen tips.",
                "estimated_duration_seconds": 30,
            }
        ]
    }


def _reel_default() -> dict:
    return {
        "title": "Three swaps, one cheaper grocery basket",
        "concept": "A fast, practical comparison of three ingredient swaps.",
        "hook": "Your grocery basket can cost less without losing flavour.",
        "target_audience": "Home cooks who want affordable plant-based meals.",
        "scenes": [
            {
                "scene_number": 1,
                "duration_seconds": 8,
                "visual": "Creator holds two similar ingredients up to the camera.",
                "dialogue": "These two look similar, but one costs twice as much.",
                "camera_angle": "Eye-level medium shot",
                "lighting": "Soft natural window light",
                "background": "Clean kitchen counter",
                "on_screen_text": "Same meal. Half the cost.",
            },
            {
                "scene_number": 2,
                "duration_seconds": 12,
                "visual": "Side-by-side bowls show the finished meals.",
                "dialogue": "Here is the swap I use every week.",
                "camera_angle": "45-degree close-up",
                "lighting": "Bright overhead light",
                "background": "Wooden table with fresh herbs",
                "on_screen_text": "Swap 1",
            },
            {
                "scene_number": 3,
                "duration_seconds": 10,
                "visual": "Creator points to the cost comparison on screen.",
                "dialogue": "Save this and try it on your next grocery run.",
                "camera_angle": "Medium close-up",
                "lighting": "Soft natural light",
                "background": "Kitchen counter",
                "on_screen_text": "Save this",
            },
        ],
        "music_suggestion": "Light, upbeat acoustic track at low volume.",
        "caption": "Three simple swaps that cut my grocery bill. Which one will you try?",
        "hashtags": ["#plantbased", "#budgetcooking"],
        "call_to_action": "Follow for more practical kitchen tips.",
        "estimated_duration_seconds": 30,
    }


def _reply_default() -> dict:
    return {
        "suggestions": [
            {
                "text": "Thanks for asking! I use a simple one-pan method and will share the full recipe soon. What are you cooking this week?",
                "tone": "friendly",
                "rationale": "Acknowledges the question and invites a light follow-up.",
            }
        ]
    }


_DEFAULTS = {
    "ContentIdeasResult": _content_ideas_default,
    "CaptionsResult": _captions_default,
    "ScriptsResult": _scripts_default,
    "ReelPlanResult": _reel_default,
    "ReplySuggestionsResult": _reply_default,
    "AnalyticsExplanation": lambda: {
        "summary": "The current period shows engagement across the simulated posts.",
        "growth_explanation": "The comparison uses the supplied prior-period totals only.",
        "key_findings": ["The supplied totals show meaningful engagement."],
        "recommendations": ["Double down on the best-performing supplied format."],
    },
}


class MockAIClient(BaseAIClient):
    provider = "mock"
    model = "mock-gemini"

    def __init__(self, responses: dict[Any, Any] | None = None):
        self.responses = responses or {}
        self.calls: list[dict[str, Any]] = []

    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema: type[BaseModel],
        temperature: float | None = None,
    ) -> AIResult:
        schema_name = response_schema.__name__
        self.calls.append(
            {
                "prompt": prompt,
                "schema": schema_name,
                "temperature": temperature,
            }
        )

        response = self.responses.get(schema_name, self.responses.get(response_schema))
        if isinstance(response, Exception):
            raise response
        if callable(response):
            response = response(prompt)
        if response is None:
            default = _DEFAULTS.get(schema_name)
            if default is None:
                raise AIInvalidResponse(
                    f"No mock response configured for {schema_name}."
                )
            response = default()
        if isinstance(response, BaseModel):
            response = response.model_dump()
        if not isinstance(response, dict):
            raise AIError("Mock response must be a dictionary.")
        return AIResult(data=response, model=self.model)
