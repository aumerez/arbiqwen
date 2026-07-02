"""Limit/offset pagination helpers shared across list endpoints."""

from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams:
    """FastAPI dependency capturing `limit`/`offset` query params.

    Used as `params: PaginationParams = Depends()` so every list route exposes
    the same paging contract with sane bounds.
    """

    def __init__(
        self,
        limit: int = Query(50, ge=1, le=200, description="Max items to return"),
        offset: int = Query(0, ge=0, description="Items to skip"),
    ):
        self.limit = limit
        self.offset = offset


class Page(BaseModel, Generic[T]):
    """Envelope for a paginated list response."""

    items: list[T]
    total: int
    limit: int
    offset: int

    @classmethod
    def create(cls, items: list[T], total: int, params: PaginationParams) -> "Page[T]":
        return cls(items=items, total=total, limit=params.limit, offset=params.offset)
