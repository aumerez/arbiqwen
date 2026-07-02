"""Common FastAPI dependencies reused across routers."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_session

# Inject a request-scoped async DB session: `session: SessionDep`.
SessionDep = Annotated[AsyncSession, Depends(get_session)]
