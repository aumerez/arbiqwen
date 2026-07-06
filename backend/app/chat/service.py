"""Chat service: conversation CRUD and RAG-grounded answer generation."""

import logging
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.models import Chat, ChatMessage, ChatRole
from app.chat.retrieval import RetrievedChunk, retrieve
from app.config import settings
from app.llm import get_llm_provider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Arbi, a helpful operations assistant. Answer the user's question "
    "using the provided context when it is relevant, and say so when the context "
    "does not contain the answer."
)


def _build_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return f"{SYSTEM_PROMPT}\n\nQuestion: {question}"
    context = "\n\n".join(f"[{i + 1}] {c.text}" for i, c in enumerate(chunks))
    return f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nQuestion: {question}"


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

    async def answer(self, chat: Chat, user_text: str) -> ChatMessage:
        """Persist the user turn, retrieve context, generate + persist the answer."""
        await self.add_message(chat.id, ChatRole.user, user_text)

        chunks = await retrieve(user_text)
        prompt = _build_prompt(user_text, chunks)

        if settings.llm_configured:
            try:
                answer_text = await get_llm_provider().generate(prompt)
            except Exception as exc:  # noqa: BLE001 — surface a message rather than a 500
                logger.warning("LLM generation failed (%s): %s", type(exc).__name__, exc)
                answer_text = "I couldn't generate a response right now. Please try again."
        else:
            answer_text = "The language model is not configured on this server."

        citations = [{"document_id": c.document_id, "chunk_index": c.chunk_index, "text": c.text[:200]} for c in chunks]
        assistant = await self.add_message(
            chat.id,
            ChatRole.assistant,
            answer_text,
            citations=citations or None,
            retrieved_chunk_ids=[c.chunk_index for c in chunks] or None,
        )
        await self.session.commit()
        await self.session.refresh(assistant)
        return assistant
