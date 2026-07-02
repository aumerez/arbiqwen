"""Base service class.

Services hold business logic and own a DB session for the duration of a
request. Concrete services subclass `BaseService` and add domain methods.
"""

from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    def __init__(self, session: AsyncSession):
        self.session = session
