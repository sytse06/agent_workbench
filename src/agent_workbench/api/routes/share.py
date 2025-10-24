"""
Share target handler for PWA share functionality.

Allows users to share content from other apps/websites into Agent Workbench.
"""

import logging
from typing import List, Optional
from urllib.parse import quote_plus

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["pwa", "share"])


@router.post("/share")
async def share_target_handler(
    request: Request,
    title: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    documents: Optional[List[UploadFile]] = File(None),
) -> RedirectResponse:
    """
    Handle shared content from other apps via PWA share target.

    Creates a new conversation with shared content pre-filled in the message input.

    Args:
        request: FastAPI request (for accessing user session)
        title: Shared title (optional)
        text: Shared text content (optional)
        url: Shared URL (optional)
        documents: Shared files (optional, Phase 2.4 full implementation)

    Returns:
        Redirect to main chat interface with pre-filled message

    Examples:
        - Share URL: "Check this out: https://example.com"
        - Share text: "Analyze this: [shared text]"
        - Share file: "Uploaded: document.pdf" (Phase 2.4)
    """
    file_count = len(documents) if documents else 0
    logger.info(f"Share target received: title={title}, url={url}, files={file_count}")

    # Build message from shared content
    message_parts = []

    if title:
        message_parts.append(f"**{title}**")

    if url:
        message_parts.append(f"Shared URL: {url}")

    if text:
        # Limit text length to avoid overwhelming the chat
        max_text_length = 500
        truncated_text = (
            text[:max_text_length] + "..." if len(text) > max_text_length else text
        )
        message_parts.append(f"\n{truncated_text}")

    if documents:
        # Phase 2.1: Stub implementation (just list filenames)
        # Phase 2.4: Full file upload handling
        file_names = [doc.filename for doc in documents if doc.filename]
        if file_names:
            message_parts.append(f"\nAttached Files: {', '.join(file_names)}")
            logger.info(f"Files shared (not yet processed): {file_names}")

    # Combine message parts
    if not message_parts:
        # No content shared, just open chat
        return RedirectResponse(url="/", status_code=303)

    pre_filled_message = "\n".join(message_parts)

    # URL-encode message for query parameter
    encoded_message = quote_plus(pre_filled_message)

    # Redirect to chat with pre-filled message
    # The Gradio interface will read the 'message' query param and populate the input
    redirect_url = f"/?message={encoded_message}"

    logger.info(
        f"Redirecting to chat with pre-filled message ({len(pre_filled_message)} chars)"
    )

    return RedirectResponse(url=redirect_url, status_code=303)
