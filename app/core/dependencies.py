"""Shared FastAPI dependencies."""

from typing import Optional

from fastapi import Query


class PaginationParams:
    """Reusable pagination dependency."""

    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    ):
        self.skip = skip
        self.limit = limit
