"""Chat routes: conversation CRUD and streaming message generation."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.chat.models import ChatRole
from app.chat.retrieval import retrieve
from app.chat.schemas import (
    ChatCreateSchema,
    ChatMessageCreateSchema,
    ChatMessageSchema,
    ChatResponseSchema,
    TitleGenerationSchema,
    TitleResponseSchema,
)
from app.chat.service import SYSTEM_PROMPT, ChatService
from app.config import settings
from app.database.connection import get_session
from app.llm import get_llm_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["chats"])


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


async def _load_owned_chat(chat_id: int, user_id: int, svc: ChatService):
    chat = await svc.get_chat(chat_id)
    if chat is None or chat.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat


@router.post("", response_model=ChatResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_chat(
    body: ChatCreateSchema,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new chat."""
    return await ChatService(session).create_chat(current["id"], current["tenant_id"], body.title)


@router.get("", response_model=list[ChatResponseSchema])
async def list_chats(current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """List the current user's chats, most recently updated first."""
    return await ChatService(session).list_chats(current["id"])


@router.get("/{chat_id}", response_model=ChatResponseSchema)
async def get_chat(chat_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Fetch a single chat."""
    return await _load_owned_chat(chat_id, current["id"], ChatService(session))


@router.get("/{chat_id}/messages", response_model=list[ChatMessageSchema])
async def get_messages(chat_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Fetch a chat's messages in order."""
    svc = ChatService(session)
    await _load_owned_chat(chat_id, current["id"], svc)
    return await svc.get_messages(chat_id)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(chat_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Delete a chat and its messages."""
    svc = ChatService(session)
    chat = await _load_owned_chat(chat_id, current["id"], svc)
    await svc.delete_chat(chat)


@router.patch("/{chat_id}/title", response_model=ChatResponseSchema)
async def update_title(
    chat_id: int,
    body: TitleResponseSchema,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Rename a chat."""
    svc = ChatService(session)
    chat = await _load_owned_chat(chat_id, current["id"], svc)
    chat.title = body.title
    await session.commit()
    await session.refresh(chat)
    return chat


@router.post("/{chat_id}/generate-title", response_model=TitleResponseSchema)
async def generate_title(
    chat_id: int,
    body: TitleGenerationSchema,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Generate a short chat title from a message (falls back to a truncation)."""
    svc = ChatService(session)
    await _load_owned_chat(chat_id, current["id"], svc)
    title = body.message.strip()[:60] or "New chat"
    if settings.llm_configured:
        try:
            generated = await get_llm_provider().generate(
                f"Give a concise 3-6 word title (no quotes) for this message: {body.message}"
            )
            title = generated.strip().strip('"')[:120] or title
        except Exception as exc:  # noqa: BLE001 — fall back to the truncation
            logger.warning("Title generation failed (%s): %s", type(exc).__name__, exc)
    return TitleResponseSchema(title=title)


@router.post("/{chat_id}/messages")
async def stream_message(
    chat_id: int,
    body: ChatMessageCreateSchema,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Stream a RAG-grounded answer to a message as Server-Sent Events."""
    svc = ChatService(session)
    chat = await _load_owned_chat(chat_id, current["id"], svc)

    await svc.add_message(chat.id, ChatRole.user, body.message)
    await session.commit()

    chunks = await retrieve(body.message)
    context = "\n\n".join(f"[{i + 1}] {c.text}" for i, c in enumerate(chunks))
    system_content = f"{SYSTEM_PROMPT}\n\nContext:\n{context}" if chunks else SYSTEM_PROMPT
    citations = [
        {"document_id": c.document_id, "chunk_index": c.chunk_index, "text": c.text[:200]} for c in chunks
    ]

    async def event_generator():
        parts: list[str] = []
        if settings.llm_configured:
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": body.message},
            ]
            try:
                async for event in get_llm_provider().generate_stream(messages):
                    if event.get("type") == "text":
                        parts.append(event["text"])
                        yield _sse({"type": "text", "text": event["text"]})
            except Exception as exc:  # noqa: BLE001 — end the stream cleanly on error
                logger.warning("Streaming failed (%s): %s", type(exc).__name__, exc)
                fallback = "I couldn't generate a response right now."
                parts.append(fallback)
                yield _sse({"type": "text", "text": fallback})
        else:
            fallback = "The language model is not configured on this server."
            parts.append(fallback)
            yield _sse({"type": "text", "text": fallback})

        await svc.add_message(
            chat.id,
            ChatRole.assistant,
            "".join(parts),
            citations=citations or None,
            retrieved_chunk_ids=[c.chunk_index for c in chunks] or None,
        )
        await session.commit()
        yield _sse({"type": "done", "citations": citations})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
