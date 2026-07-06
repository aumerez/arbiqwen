"""OAuth linkage routes for OAuth-based integrations."""

from datetime import UTC

from fastapi import APIRouter, Depends, status
from fastapi.responses import HTMLResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.connection import get_session
from app.integrations.oauth_models import OAuthToken

# Mounted under the same /api/integrations prefix as the instance routes.
oauth_router = APIRouter(prefix="/api/integrations", tags=["integrations"])


def _granted(scopes: str | None) -> list[str]:
    return sorted(s for s in (scopes.split(",") if scopes else []) if s)


@oauth_router.get("/oauth/linked-integrations")
async def linked_integrations(current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """List the OAuth integrations the current user has connected."""
    rows = (
        (
            await session.execute(
                select(OAuthToken).where(
                    OAuthToken.tenant_id == current["tenant_id"], OAuthToken.user_id == current["id"]
                )
            )
        )
        .scalars()
        .all()
    )
    return {
        "linked_integrations": [
            {
                "provider": r.provider,
                "account_email": r.account_email,
                "scopes_granted": _granted(r.scopes),
                "connected_at": r.created_at.replace(tzinfo=UTC).isoformat() if r.created_at else None,
                "status": "connected",
                "is_oauth": True,
            }
            for r in rows
        ]
    }


@oauth_router.get("/oauth/status")
async def oauth_status(
    provider: str,
    scopes: str | None = None,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Report whether the user has a live OAuth token for a provider."""
    row = (
        await session.execute(
            select(OAuthToken).where(
                OAuthToken.tenant_id == current["tenant_id"],
                OAuthToken.user_id == current["id"],
                OAuthToken.provider == provider,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return {"linked": False, "expires_at": None, "scopes": []}

    granted = set(_granted(row.scopes))
    if scopes:
        required = {s.strip() for s in scopes.split(",") if s.strip()}
        if not required.issubset(granted):
            return {"linked": False, "expires_at": None, "scopes": sorted(granted)}

    return {
        "linked": True,
        "expires_at": row.expires_at.replace(tzinfo=UTC).isoformat() if row.expires_at else None,
        "scopes": sorted(granted),
    }


@oauth_router.post("/oauth/{provider}/disconnect", status_code=status.HTTP_200_OK)
async def oauth_disconnect(
    provider: str,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove the user's OAuth token for a provider."""
    await session.execute(
        delete(OAuthToken).where(
            OAuthToken.tenant_id == current["tenant_id"],
            OAuthToken.user_id == current["id"],
            OAuthToken.provider == provider,
        )
    )
    await session.commit()
    return {"disconnected": True, "provider": provider}


@oauth_router.get("/oauth/success", response_class=HTMLResponse, include_in_schema=False)
async def oauth_success_page():
    """Static page the browser lands on after a successful OAuth consent."""
    return HTMLResponse(
        """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><title>Authorization complete</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
         display: grid; place-items: center; min-height: 100vh; margin: 0;
         background: #0b0d10; color: #e8ecef; }
  .card { max-width: 440px; padding: 2rem 2.5rem; border-radius: 12px;
          background: #14181d; border: 1px solid #242a31; text-align: center; }
  h1 { margin: 0 0 .5rem; font-size: 1.25rem; }
  p  { margin: .5rem 0 0; opacity: .8; line-height: 1.5; }
</style></head><body>
<div class="card">
  <h1>Authorization complete</h1>
  <p>You can close this tab and return to Arbi.</p>
  <p style="font-size:.8rem;opacity:.6;margin-top:1rem">
    The app is detecting the new connection automatically.
  </p>
</div>
<script>setTimeout(function(){try{window.close();}catch(_){}},1500);</script>
</body></html>""",
    )
