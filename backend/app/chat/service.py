"""Chat service: conversation CRUD."""

import logging
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.models import Chat, ChatMessage, ChatRole

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Arbi, a helpful operations assistant. Answer the user's question "
    "using the provided context when it is relevant, and say so when the context "
    "does not contain the answer."
)


class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chat(self, user_id: int, tenant_id: int, title: str | None) -> Chat:
        chat = Chat(user_id=user_id, tenant_id=tenant_id, title=title)
        self.session.add(chat)
        await self.session.commit()
        await self.session.refresh(chat)
        return chat

    async def list_chats(self, user_id: int) -> list[Chat]:
        rows = await self.session.execute(select(Chat).where(Chat.user_id == user_id).order_by(Chat.updated_at.desc()))
        return list(rows.scalars().all())

    async def get_chat(self, chat_id: int) -> Chat | None:
        return (await self.session.execute(select(Chat).where(Chat.id == chat_id))).scalar_one_or_none()

    async def get_messages(self, chat_id: int) -> list[ChatMessage]:
        rows = await self.session.execute(
            select(ChatMessage).where(ChatMessage.chat_id == chat_id).order_by(ChatMessage.created_at)
        )
        return list(rows.scalars().all())

    async def delete_chat(self, chat: Chat) -> None:
        await self.session.delete(chat)
        await self.session.commit()

    async def add_message(self, chat_id: int, role: ChatRole, content: str, **fields) -> ChatMessage:
        message = ChatMessage(chat_id=chat_id, msg_uuid=str(uuid4()), role=role, content=content, **fields)
        self.session.add(message)
        return message
