"""Demo profile — seeds a coherent set of example data for a fresh install.

Idempotent: keyed on the demo user's email, so running it twice is a no-op.
"""

import logging
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentTask
from app.auth.models import User
from app.auth.password import hash_password
from app.chat.models import Chat, ChatMessage, ChatRole
from app.dashboards.models import Dashboard
from app.documents.models import Document, DocumentChunk, DocumentStatus
from app.integrations.models import Integration, IntegrationConnection
from app.playbooks.models import Playbook
from app.projects.models import Project
from app.rag_sources.models import TenantRAGSource

logger = logging.getLogger(__name__)

DEMO_EMAIL = "demo@arbi.dev"
DEMO_PASSWORD = "demo1234"


async def seed_demo(session: AsyncSession) -> dict:
    """Insert the demo dataset. Returns a summary of what was created."""
    existing = (await session.execute(select(User).where(User.email == DEMO_EMAIL))).scalar_one_or_none()
    if existing is not None:
        return {"status": "already_seeded", "user_id": existing.id}

    user = User(email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD), role="admin")
    session.add(user)
    await session.flush()

    project = Project(
        tenant_id=1,
        user_id=user.id,
        name="Operations",
        description="Default demo workspace.",
        is_default=True,
    )
    session.add(project)

    rag_source = TenantRAGSource(
        tenant_id=1, rag_key="qdrant", label="Knowledge Base", description="Primary vector store.", writable=True
    )
    session.add(rag_source)

    integration = Integration(
        tenant_id=1,
        name="Slack",
        instance_alias="Team Slack",
        description="Demo Slack connection.",
        type="apikey",
        category="slack",
        icon_name="slack",
        status="connected",
    )
    session.add(integration)
    await session.flush()
    session.add(
        IntegrationConnection(integration_id=integration.id, status="connected", connected_at=datetime.now(UTC))
    )

    session.add(
        AgentTask(
            tenant_id=1,
            user_id=user.id,
            title="Daily Summary",
            prompt_template="Summarize activity for {date}.",
            steps=["collect", "summarize"],
            allowed_tools=["document_search"],
            status="draft",
        )
    )

    document = Document(
        tenant_id=1,
        user_id=user.id,
        filename="welcome.txt",
        mimetype="text/plain",
        size=64,
        status=DocumentStatus.indexed,
        folder_path="guides",
        source="upload",
    )
    session.add(document)
    await session.flush()
    session.add(
        DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            content="Welcome to Arbi, your operations assistant.",
            token_count=10,
        )
    )

    chat = Chat(tenant_id=1, user_id=user.id, title="Getting started")
    session.add(chat)
    await session.flush()
    session.add(ChatMessage(chat_id=chat.id, msg_uuid=str(uuid4()), role=ChatRole.user, content="What can you do?"))
    session.add(
        ChatMessage(
            chat_id=chat.id,
            msg_uuid=str(uuid4()),
            role=ChatRole.assistant,
            content="I can search your documents and answer questions grounded in them.",
        )
    )

    session.add(
        Playbook(
            tenant_id=1,
            project_id=project.id,
            created_by_user_id=user.id,
            name="Onboarding",
            description="Steps to onboard a new teammate.",
            status="active",
            steps=[{"id": "s1", "order": 1, "type": "action", "name": "Send welcome"}],
        )
    )

    session.add(
        Dashboard(
            tenant_id=1,
            project_id=project.id,
            created_by_user_id=user.id,
            title="Overview",
            spec={"type": "summary"},
            skill_name="chart",
        )
    )

    await session.commit()
    logger.info("Seeded demo data for %s", DEMO_EMAIL)
    return {
        "status": "seeded",
        "user_id": user.id,
        "email": DEMO_EMAIL,
        "project_id": project.id,
    }
