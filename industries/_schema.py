"""Pydantic schema for industry YAML configs."""
from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


SLUG_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class Track(str, Enum):
    CONTRACT_MOTION = "contract_motion"
    AI_AUTOMATION = "ai_automation"


class ScoringMode(str, Enum):
    POSITIVE = "positive"
    NEGATIVE_TECH_STACK = "negative_tech_stack"
    HYBRID = "hybrid"


class ExpectedStack(BaseModel):
    fsm: list[str] = Field(default_factory=list)
    crm: list[str] = Field(default_factory=list)
    sms: list[str] = Field(default_factory=list)
    marketing_automation: list[str] = Field(default_factory=list)
    analytics: list[str] = Field(default_factory=list)


class Industry(BaseModel):
    slug: str
    display_name: str
    track: Track
    campaign_id: str

    revenue_range_m: list[float] = Field(min_length=2, max_length=2)
    naics: list[str]
    titles: list[str]
    states: list[str]

    apollo_keywords: list[str]
    directory_seeds: list[str] = Field(default_factory=list)
    directory_auto_discovery: bool = True

    scoring_mode: ScoringMode
    expected_stack_if_mature: ExpectedStack | None = None
    prioritize_when_missing: list[str] = Field(default_factory=list)
    min_heat: float = 50.0

    signal_ttl_days: int = 90
    budget_cap_per_run: int = 50
    landing_page_url: str | None = None

    sender_pool: str = "default"

    @field_validator("slug")
    @classmethod
    def _slug_format(cls, v: str) -> str:
        if not SLUG_RE.match(v):
            raise ValueError(
                f"slug must match {SLUG_RE.pattern}: got {v!r}"
            )
        return v

    @field_validator("revenue_range_m")
    @classmethod
    def _revenue_order(cls, v: list[float]) -> list[float]:
        if v[0] >= v[1]:
            raise ValueError("revenue_range_m must be [low, high] with low < high")
        return v

    @model_validator(mode="after")
    def _scoring_consistency(self) -> "Industry":
        if self.scoring_mode in (ScoringMode.NEGATIVE_TECH_STACK, ScoringMode.HYBRID):
            if self.expected_stack_if_mature is None:
                raise ValueError(
                    f"scoring_mode={self.scoring_mode.value} requires expected_stack_if_mature"
                )
        return self
