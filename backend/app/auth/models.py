from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy import true as sql_true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("idx_users_email", "email", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    # Single workspace for now; kept on the model so the login contract stays
    # stable if multi-workspace support lands later.
    tenant_id: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String, default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sql_true(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("idx_refresh_tokens_user_id", "user_id"),
        Index("idx_refresh_tokens_token_hash", "token_hash", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
