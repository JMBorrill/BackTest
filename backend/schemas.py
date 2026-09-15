"""Request and response models.

Everything that can be rejected before the workload runs is rejected here,
so an invalid request costs nothing and the caller gets a field path.
"""
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class BacktestRequest(BaseModel):
    # extra="forbid" so a typo like "fast_windows" is a clear 422 rather
    # than a silently ignored field and a surprising result.
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=16)
    start: date
    end: date
    # slow_window is declared first so that when fast_window is validated the
    # slow one is already parsed - that is what lets the error name
    # "fast_window", the field the caller has to change.
    slow_window: int = Field(ge=2, le=1000)
    fast_window: int = Field(ge=1, le=500)

    @field_validator("fast_window")
    @classmethod
    def _fast_below_slow(cls, value: int, info: ValidationInfo) -> int:
        slow = info.data.get("slow_window")
        if slow is not None and value >= slow:
            raise ValueError("must be less than slow_window")
        return value

    @field_validator("end")
    @classmethod
    def _end_after_start(cls, value: date, info: ValidationInfo) -> date:
        start = info.data.get("start")
        if start is not None and value <= start:
            raise ValueError("must be later than start")
        return value


class Metrics(BaseModel):
    total_return: float
    cagr: float
    max_drawdown: float
    trades: int


class Benchmark(BaseModel):
    total_return: float


class BacktestResponse(BaseModel):
    symbol: str
    start: str
    end: str
    bars: int
    metrics: Metrics
    benchmark: Benchmark
